import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import Base, engine, get_db
from backend.models import (
    AuditLog,
    ChatLog,
    Chunk,
    Deal,
    DealDocumentLink,
    Document,
    DocumentProvenance,
    RetrievalTrace,
    SkillRecord,
    WorkflowRun,
)
from backend.services.analytics import DuckDBAnalyticsStore
from backend.services.parser import ParsedChunk, parse_and_chunk
from backend.services.connectors import scan_local_directory, to_payload
from backend.services.graph import Neo4jGraphStore
from backend.services.precedent import find_precedents, summarize_precedents
from backend.services.rag import generate_answer
from backend.services.semantic_memory import MemPalaceStore
from backend.services.skills import SkillManager
from backend.services.vector import QdrantVectorStore
from backend.services.workspace import WorkspaceManager
from backend.services.workflow import run_ic_workflow

settings = get_settings()
app = FastAPI(title="PE Local RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_store: QdrantVectorStore | None = None
graph_store: Neo4jGraphStore | None = None
analytics_store: DuckDBAnalyticsStore | None = None
workspace_manager: WorkspaceManager | None = None
semantic_memory_store: MemPalaceStore | None = None
skill_manager: SkillManager | None = None


def get_vector_store() -> QdrantVectorStore:
    global vector_store
    if vector_store is None:
        vector_store = QdrantVectorStore()
    return vector_store


def get_graph_store() -> Neo4jGraphStore:
    global graph_store
    if graph_store is None:
        graph_store = Neo4jGraphStore()
    return graph_store


def get_workspace_manager() -> WorkspaceManager:
    global workspace_manager
    if workspace_manager is None:
        workspace_manager = WorkspaceManager()
    return workspace_manager


def get_analytics_store() -> DuckDBAnalyticsStore:
    global analytics_store
    if analytics_store is None:
        analytics_store = DuckDBAnalyticsStore()
    return analytics_store


def get_semantic_memory_store() -> MemPalaceStore:
    global semantic_memory_store
    if semantic_memory_store is None:
        semantic_memory_store = MemPalaceStore(get_workspace_manager())
    return semantic_memory_store


def get_skill_manager() -> SkillManager:
    global skill_manager
    if skill_manager is None:
        skill_manager = SkillManager(get_workspace_manager())
    return skill_manager


class DocumentOut(BaseModel):
    id: str
    filename: str
    upload_timestamp: datetime
    tags: list[str]
    category: str
    deal_outcome: str | None

    class Config:
        from_attributes = True


class DealOut(BaseModel):
    id: str
    name: str
    company_name: str | None
    sector: str | None
    geography: str | None
    stage: str | None
    fund_name: str | None
    vintage_year: int | None
    strategy: str | None
    decision_status: str | None
    outcome_status: str | None
    partner_owner: str | None
    summary: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DealCreate(BaseModel):
    name: str
    company_name: str | None = None
    sector: str | None = None
    geography: str | None = None
    stage: str | None = None
    fund_name: str | None = None
    vintage_year: int | None = None
    strategy: str | None = None
    decision_status: str | None = None
    outcome_status: str | None = None
    partner_owner: str | None = None
    summary: str | None = None


class ChatFilters(BaseModel):
    categories: list[str] | None = None
    deal_outcomes: list[str] | None = None


class ChatRequest(BaseModel):
    query: str
    doc_ids: Optional[List[str]] = None
    analysis_mode: str = "document_search"
    filters: ChatFilters | None = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    prompt_version: str
    model_name: str


class PrecedentRequest(BaseModel):
    query: str
    doc_ids: list[str] | None = None
    categories: list[str] | None = None
    deal_outcomes: list[str] | None = None
    top_k: int = 12


class WorkflowRequest(BaseModel):
    query: str
    deal_id: str | None = None
    doc_ids: list[str] | None = None
    categories: list[str] | None = None
    deal_outcomes: list[str] | None = None


def _hash_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _normalize_json_list(raw_value: str | None) -> list[str]:
    if not raw_value:
        return []
    try:
        parsed = json.loads(raw_value)
        if isinstance(parsed, list):
            return [str(item) for item in parsed]
    except json.JSONDecodeError:
        pass
    return []


def _link_document_to_deal(db: Session, document_id: str, deal_id: str | None) -> None:
    if not deal_id:
        return

    deal = db.query(Deal).filter(Deal.id == deal_id).first()
    if deal is None:
        raise HTTPException(status_code=400, detail=f"Unknown deal_id: {deal_id}")

    db.add(DealDocumentLink(deal_id=deal_id, document_id=document_id, relation_type="evidence"))


def _store_chunks(db: Session, document_id: str, chunks: list[ParsedChunk]) -> None:
    for chunk in chunks:
        db.add(
            Chunk(
                document_id=document_id,
                content=chunk.content,
                page_number=chunk.page_number,
                chunk_index=chunk.chunk_index,
                source=chunk.source,
                section=chunk.section,
            )
        )


def _build_retrieval_trace_payload(retrieved: list) -> list[dict]:
    return [
        {
            "doc_id": item.document_id,
            "filename": item.filename,
            "page_number": item.page_number,
            "chunk_index": item.chunk_index,
            "score": item.score,
            "category": item.category,
            "deal_outcome": item.deal_outcome,
        }
        for item in retrieved
    ]


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    get_workspace_manager()
    get_analytics_store()
    get_vector_store()
    get_graph_store()


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "workspace": get_workspace_manager().summary(),
        "duckdb": get_analytics_store().health(),
        "graph": get_graph_store().health(),
    }


@app.get("/documents", response_model=List[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.upload_timestamp.desc()).all()
    return documents


@app.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        get_vector_store().delete_document(document_id)
    except Exception:
        pass
    try:
        get_analytics_store().delete_document(document_id)
    except Exception:
        pass

    provenance = document.provenance
    if provenance:
        source_path = Path(provenance.source_path)
        if source_path.exists():
            source_path.unlink()
        metadata = provenance.metadata_json or {}
        for key in ("markdown_path", "chunks_path"):
            artifact = metadata.get(key)
            if artifact:
                artifact_path = Path(artifact)
                if artifact_path.exists():
                    artifact_path.unlink()

    db.delete(document)
    db.commit()
    return {"status": "deleted", "document_id": document_id}


@app.get("/deals", response_model=List[DealOut])
def list_deals(db: Session = Depends(get_db)):
    return db.query(Deal).order_by(Deal.updated_at.desc()).all()


@app.post("/deals", response_model=DealOut)
def create_deal(payload: DealCreate, db: Session = Depends(get_db)):
    deal = Deal(**payload.model_dump())
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


@app.get("/connectors/local")
def list_local_connector_documents(root: str | None = None):
    scan_root = root or settings.connectors_root
    return {
        "root": scan_root,
        "documents": to_payload(scan_local_directory(scan_root)),
    }


@app.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    tags: str = Form("[]"),
    category: str = Form("other"),
    deal_outcome: str | None = Form(None),
    deal_id: str | None = Form(None),
    document_type: str | None = Form(None),
    language: str | None = Form(None),
    metadata_json: str | None = Form(None),
    db: Session = Depends(get_db),
):
    parsed_tags = _normalize_json_list(tags)
    parsed_metadata = {}
    if metadata_json:
        try:
            parsed_metadata = json.loads(metadata_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid metadata_json: {exc}") from exc

    content = await file.read()
    document = Document(
        filename=file.filename,
        tags=parsed_tags,
        category=category,
        deal_outcome=deal_outcome,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    file_location = get_workspace_manager().store_raw_document(
        document.id,
        file.filename,
        content,
        deal_id=deal_id,
    )

    try:
        chunks = parse_and_chunk(file_location)
    except Exception as exc:
        db.delete(document)
        db.commit()
        if file_location.exists():
            file_location.unlink()
        raise HTTPException(status_code=400, detail=f"Parsing failed: {exc}") from exc

    parsed_artifacts = get_workspace_manager().write_parsed_artifacts(
        document.id,
        document.filename,
        chunks,
        deal_id=deal_id,
    )

    db.add(
        DocumentProvenance(
            document_id=document.id,
            sha256=_hash_bytes(content),
            source_path=str(file_location),
            document_type=document_type,
            language=language,
            metadata_json={**parsed_metadata, **parsed_artifacts},
        )
    )
    _store_chunks(db, document.id, chunks)
    _link_document_to_deal(db, document.id, deal_id)
    db.add(
        AuditLog(
            entity_type="document",
            entity_id=document.id,
            action="uploaded",
            payload_json={
                "filename": document.filename,
                "deal_id": deal_id,
                "category": category,
                "parsed_artifacts": parsed_artifacts,
            },
        )
    )
    db.commit()

    try:
        get_vector_store().upsert_chunks(
            chunks,
            document.id,
            document.filename,
            metadata={
                "category": document.category,
                "deal_outcome": document.deal_outcome,
                "deal_id": deal_id,
            },
        )
        get_analytics_store().replace_document_chunks(
            document.id,
            document.filename,
            deal_id,
            str(file_location),
            chunks,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vector upsert failed: {exc}") from exc

    return document


@app.post("/precedents")
def precedents(request: PrecedentRequest, db: Session = Depends(get_db)):
    results = find_precedents(
        db,
        get_vector_store(),
        request.query,
        doc_ids=request.doc_ids,
        categories=request.categories,
        deal_outcomes=request.deal_outcomes,
        top_k=request.top_k,
    )
    return summarize_precedents(results)


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        categories = request.filters.categories if request.filters else None
        deal_outcomes = request.filters.deal_outcomes if request.filters else None
        retrieved = get_vector_store().search(
            request.query,
            doc_ids=request.doc_ids,
            categories=categories,
            deal_outcomes=deal_outcomes,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {exc}") from exc

    if not retrieved:
        raise HTTPException(status_code=404, detail="No relevant context found")

    answer_payload = generate_answer(request.query, retrieved)

    log = ChatLog(user_query=request.query, ai_response=answer_payload["answer"])
    db.add(log)
    db.flush()
    db.add(
        RetrievalTrace(
            chat_log_id=log.id,
            query=request.query,
            analysis_mode=request.analysis_mode,
            prompt_version=answer_payload["prompt_version"],
            model_name=answer_payload["model_name"],
            selected_doc_ids=request.doc_ids or [],
            retrieved_chunks=_build_retrieval_trace_payload(retrieved),
        )
    )
    db.commit()

    return ChatResponse(**answer_payload)


@app.post("/workflow/run")
def workflow_run(request: WorkflowRequest, db: Session = Depends(get_db)):
    payload = run_ic_workflow(
        db,
        get_vector_store(),
        request.query,
        deal_id=request.deal_id,
        doc_ids=request.doc_ids,
        categories=request.categories,
        deal_outcomes=request.deal_outcomes,
    )
    workflow = WorkflowRun(
        deal_id=request.deal_id,
        workflow_type="ic_copilot",
        status="completed",
        input_json=request.model_dump(),
        output_json=payload,
        model_name=payload.get("model_name"),
        prompt_version=payload.get("prompt_version"),
    )
    db.add(workflow)
    db.flush()

    report_path = get_workspace_manager().write_workflow_output(
        workflow.id,
        request.deal_id,
        "IC Workflow Output",
        payload,
    )
    get_analytics_store().log_analysis_run(workflow.id, request.deal_id, request.query, str(report_path))

    summary = "\n".join(
        [
            payload.get("draft_answer", "No answer"),
            "",
            "Risk gaps:",
            *[f"- {item}" for item in payload.get("risk_gaps", [])],
        ]
    ).strip()
    postmortem_path = get_workspace_manager().write_postmortem(
        workflow.id,
        request.deal_id,
        summary,
        {"query": request.query, "report_path": str(report_path)},
    )
    memory = get_semantic_memory_store().write_summary(
        db,
        request.deal_id,
        workflow.id,
        title=f"Workflow summary for {request.query[:80]}",
        summary=summary,
        evidence=payload.get("draft_sources", []),
    )
    skill_name, skill_path = get_skill_manager().create_candidate(workflow.id, request.query, payload)
    db.add(
        SkillRecord(
            name=skill_name,
            stage="candidate",
            description=f"Generated from workflow {workflow.id}",
            path=skill_path,
            source_workflow_id=workflow.id,
        )
    )
    db.add(
        AuditLog(
            entity_type="workflow_run",
            entity_id=workflow.id,
            action="completed",
            payload_json={
                "report_path": str(report_path),
                "postmortem_path": str(postmortem_path),
                "semantic_memory_id": memory.id,
                "skill_path": skill_path,
            },
        )
    )
    workflow.output_json = {
        **payload,
        "artifacts": {
            "report_path": str(report_path),
            "postmortem_path": str(postmortem_path),
            "skill_path": skill_path,
            "semantic_memory_id": memory.id,
        },
    }
    db.commit()
    db.refresh(workflow)
    return {
        "workflow_id": workflow.id,
        **workflow.output_json,
    }


@app.get("/skills")
def list_skills(stage: str | None = None, db: Session = Depends(get_db)):
    query = db.query(SkillRecord)
    if stage:
        query = query.filter(SkillRecord.stage == stage)
    skills = query.order_by(SkillRecord.updated_at.desc()).all()
    return [
        {
            "id": skill.id,
            "name": skill.name,
            "stage": skill.stage,
            "description": skill.description,
            "path": skill.path,
            "source_workflow_id": skill.source_workflow_id,
            "updated_at": skill.updated_at,
        }
        for skill in skills
    ]


@app.get("/workflow/runs")
def list_workflow_runs(deal_id: str | None = None, db: Session = Depends(get_db)):
    query = db.query(WorkflowRun)
    if deal_id:
        query = query.filter(WorkflowRun.deal_id == deal_id)
    runs = query.order_by(WorkflowRun.created_at.desc()).all()
    return [
        {
            "id": run.id,
            "deal_id": run.deal_id,
            "workflow_type": run.workflow_type,
            "status": run.status,
            "model_name": run.model_name,
            "prompt_version": run.prompt_version,
            "created_at": run.created_at,
            "output": run.output_json,
        }
        for run in runs
    ]
