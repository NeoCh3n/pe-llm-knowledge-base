import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
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
    WorkflowRun,
)
from backend.services.parser import ParsedChunk, parse_and_chunk
from backend.services.precedent import find_precedents, summarize_precedents
from backend.services.rag import generate_answer
from backend.services.vector import QdrantVectorStore
from backend.services.workspace import WorkspaceManager
from backend.services.workflow import run_ic_workflow

logger = logging.getLogger(__name__)
settings = get_settings()

app = FastAPI(title="PE Local RAG API", version="0.1.0")

# ---------------------------------------------------------------------------
# CORS — local dev only; add your deploy origin before any cloud deployment
# ---------------------------------------------------------------------------
_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,   # False: no cookies/auth headers cross-origin
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# ---------------------------------------------------------------------------
# Singletons — initialized once at startup via app.state
# ---------------------------------------------------------------------------
vector_store: QdrantVectorStore | None = None
workspace_manager: WorkspaceManager | None = None


def get_vector_store() -> QdrantVectorStore:
    global vector_store
    if vector_store is None:
        vector_store = QdrantVectorStore()
    return vector_store


def get_workspace_manager() -> WorkspaceManager:
    global workspace_manager
    if workspace_manager is None:
        workspace_manager = WorkspaceManager()
    return workspace_manager


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class DocumentOut(BaseModel):
    id: str
    filename: str
    upload_timestamp: datetime
    tags: list[str]
    category: str
    deal_outcome: str | None
    status: str
    deal_id: str | None = None

    class Config:
        from_attributes = True


class DocumentStatusOut(BaseModel):
    id: str
    status: str
    status_error: str | None


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Background ingestion task
# ---------------------------------------------------------------------------

def _ingest_document(
    document_id: str,
    file_location: Path,
    filename: str,
    deal_id: str | None,
    content: bytes,
    metadata: dict,
) -> None:
    """Parse, embed, and index a document. Runs in a BackgroundTask."""
    from backend.database import SessionLocal  # avoid circular at module level

    db = SessionLocal()
    try:
        # Parse
        chunks = parse_and_chunk(file_location)

        # Write parsed artifacts
        parsed_artifacts = get_workspace_manager().write_parsed_artifacts(
            document_id, filename, chunks, deal_id=deal_id
        )

        # Store provenance + chunks in SQLite
        db.add(
            DocumentProvenance(
                document_id=document_id,
                sha256=_hash_bytes(content),
                source_path=str(file_location),
                document_type=metadata.get("document_type"),
                language=metadata.get("language"),
                metadata_json={**metadata.get("extra", {}), **parsed_artifacts},
            )
        )
        _store_chunks(db, document_id, chunks)
        db.commit()

        # Embed + upsert to Qdrant — if this fails, document stays "processing" → "failed"
        get_vector_store().upsert_chunks(
            chunks,
            document_id,
            filename,
            metadata={
                "category": metadata.get("category"),
                "deal_outcome": metadata.get("deal_outcome"),
                "deal_id": deal_id,
            },
        )

        # Mark ready
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "ready"
            db.commit()

        logger.info("Ingestion complete: document_id=%s chunks=%d", document_id, len(chunks))

    except Exception as exc:
        logger.exception("Ingestion failed: document_id=%s error=%s", document_id, exc)
        try:
            doc = db.query(Document).filter(Document.id == document_id).first()
            if doc:
                doc.status = "failed"
                doc.status_error = str(exc)
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Startup
# ---------------------------------------------------------------------------

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    get_vector_store()
    get_workspace_manager()


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/documents", response_model=List[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.upload_timestamp.desc()).all()
    result = []
    for doc in documents:
        # Get primary deal_id from deal_links (first link if any)
        deal_id = doc.deal_links[0].deal_id if doc.deal_links else None
        result.append(DocumentOut(
            id=doc.id,
            filename=doc.filename,
            upload_timestamp=doc.upload_timestamp,
            tags=doc.tags,
            category=doc.category,
            deal_outcome=doc.deal_outcome,
            status=doc.status,
            deal_id=deal_id
        ))
    return result


@app.get("/documents/{document_id}/status", response_model=DocumentStatusOut)
def document_status(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusOut(id=doc.id, status=doc.status, status_error=doc.status_error)


@app.delete("/documents/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")

    # Vector store deletion — fail loudly so orphaned vectors are visible
    try:
        get_vector_store().delete_document(document_id)
    except Exception as exc:
        logger.warning(
            "Qdrant delete failed for document_id=%s: %s — proceeding with DB delete",
            document_id,
            exc,
        )
        # Don't swallow silently; surface in response but continue DB cleanup
        # so the document doesn't get stuck in an undeletable state.

    # File cleanup via provenance
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

    db.add(
        AuditLog(
            entity_type="document",
            entity_id=document_id,
            action="deleted",
            payload_json={"filename": document.filename},
        )
    )
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


@app.post("/upload", response_model=DocumentOut)
async def upload_document(
    background_tasks: BackgroundTasks,
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
    extra_metadata: dict = {}
    if metadata_json:
        try:
            extra_metadata = json.loads(metadata_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail=f"Invalid metadata_json: {exc}") from exc

    content = await file.read()

    # Create document record immediately with status="processing"
    document = Document(
        filename=file.filename,
        tags=parsed_tags,
        category=category,
        deal_outcome=deal_outcome,
        status="processing",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # Link to deal (validates deal_id exists)
    try:
        _link_document_to_deal(db, document.id, deal_id)
        db.commit()
    except HTTPException:
        db.delete(document)
        db.commit()
        raise

    # Save raw file to workspace
    file_location = get_workspace_manager().store_raw_document(
        document.id, file.filename, content, deal_id=deal_id
    )

    db.add(
        AuditLog(
            entity_type="document",
            entity_id=document.id,
            action="uploaded",
            payload_json={"filename": document.filename, "deal_id": deal_id, "category": category},
        )
    )
    db.commit()

    # Kick off async ingestion — returns immediately to client
    background_tasks.add_task(
        _ingest_document,
        document_id=document.id,
        file_location=file_location,
        filename=file.filename,
        deal_id=deal_id,
        content=content,
        metadata={
            "category": category,
            "deal_outcome": deal_outcome,
            "document_type": document_type,
            "language": language,
            "extra": extra_metadata,
        },
    )

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
    db.add(
        AuditLog(
            entity_type="workflow_run",
            entity_id="pending",  # filled after flush
            action="completed",
            payload_json={"query": request.query, "deal_id": request.deal_id},
        )
    )
    db.flush()
    db.commit()
    db.refresh(workflow)

    report_path = get_workspace_manager().write_workflow_output(
        workflow.id, request.deal_id, "IC Workflow Output", payload
    )

    return {
        "workflow_id": workflow.id,
        **payload,
        "artifacts": {"report_path": str(report_path)},
    }


class LLMConfigUpdate(BaseModel):
    llm_provider: str
    llm_model: str
    llm_base_url: str
    llm_api_key: str | None = None


@app.get("/config/llm")
def get_llm_config():
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "llm_api_key": settings.llm_api_key,
    }


@app.put("/config/llm")
def update_llm_config(payload: LLMConfigUpdate):
    import os
    from pathlib import Path

    env_path = Path(".env")
    env_vars = {}

    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, value = line.split("=", 1)
                    env_vars[key] = value

    env_vars["LLM_PROVIDER"] = payload.llm_provider
    env_vars["LLM_MODEL"] = payload.llm_model
    env_vars["LLM_BASE_URL"] = payload.llm_base_url
    if payload.llm_api_key:
        env_vars["LLM_API_KEY"] = payload.llm_api_key
    elif "LLM_API_KEY" in env_vars:
        del env_vars["LLM_API_KEY"]

    with open(env_path, "w") as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")

    settings.llm_provider = payload.llm_provider
    settings.llm_model = payload.llm_model
    settings.llm_base_url = payload.llm_base_url
    settings.llm_api_key = payload.llm_api_key

    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "llm_base_url": settings.llm_base_url,
        "llm_api_key": settings.llm_api_key,
    }
