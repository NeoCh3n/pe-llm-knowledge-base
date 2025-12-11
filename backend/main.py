import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.database import Base, engine, get_db
from backend.models import ChatLog, Chunk, Document
from backend.services.parser import parse_and_chunk
from backend.services.rag import generate_answer
from backend.services.vector import QdrantVectorStore

settings = get_settings()
app = FastAPI(title="PE Local RAG API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = Path("data/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

vector_store: QdrantVectorStore | None = None


def get_vector_store() -> QdrantVectorStore:
    global vector_store
    if vector_store is None:
        vector_store = QdrantVectorStore()
    return vector_store


class DocumentOut(BaseModel):
    id: str
    filename: str
    upload_timestamp: datetime
    tags: list[str]
    category: str
    deal_outcome: str | None

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    query: str
    doc_ids: Optional[List[str]] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    get_vector_store()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/documents", response_model=List[DocumentOut])
def list_documents(db: Session = Depends(get_db)):
    documents = db.query(Document).order_by(Document.upload_timestamp.desc()).all()
    return documents


@app.post("/upload", response_model=DocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    tags: str = Form("[]"),
    category: str = Form("other"),
    deal_outcome: str | None = Form(None),
    db: Session = Depends(get_db),
):
    try:
        parsed_tags = json.loads(tags) if tags else []
        if not isinstance(parsed_tags, list):
            parsed_tags = []
    except json.JSONDecodeError:
        parsed_tags = []

    file_location = UPLOAD_DIR / file.filename
    with file_location.open("wb") as f:
        content = await file.read()
        f.write(content)

    document = Document(
        filename=file.filename,
        tags=parsed_tags,
        category=category,
        deal_outcome=deal_outcome,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    try:
        chunks = parse_and_chunk(file_location)
    except Exception as exc:
        db.delete(document)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Parsing failed: {exc}") from exc

    for chunk in chunks:
        db_chunk = Chunk(
            document_id=document.id,
            content=chunk.content,
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            source=chunk.source,
        )
        db.add(db_chunk)
    db.commit()

    try:
        get_vector_store().upsert_chunks(chunks, document.id, document.filename)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vector upsert failed: {exc}") from exc

    return document


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    try:
        retrieved = get_vector_store().search(request.query, doc_ids=request.doc_ids)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vector search failed: {exc}") from exc

    if not retrieved:
        raise HTTPException(status_code=404, detail="No relevant context found")

    answer_payload = generate_answer(request.query, retrieved)

    log = ChatLog(user_query=request.query, ai_response=answer_payload["answer"])
    db.add(log)
    db.commit()

    return ChatResponse(**answer_payload)
