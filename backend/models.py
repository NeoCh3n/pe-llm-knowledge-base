from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import relationship

from backend.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    filename = Column(String, nullable=False)
    upload_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    tags = Column(JSON, default=list)
    category = Column(String, default="other")
    deal_outcome = Column(String, nullable=True)

    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    provenance = relationship(
        "DocumentProvenance",
        back_populates="document",
        cascade="all, delete-orphan",
        uselist=False,
    )
    deal_links = relationship("DealDocumentLink", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, default=1)
    chunk_index = Column(Integer, default=0)
    source = Column(String, nullable=True)
    section = Column(String, nullable=True)

    document = relationship("Document", back_populates="chunks")


class Deal(Base):
    __tablename__ = "deals"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    geography = Column(String, nullable=True)
    stage = Column(String, nullable=True)
    fund_name = Column(String, nullable=True)
    vintage_year = Column(Integer, nullable=True)
    strategy = Column(String, nullable=True)
    decision_status = Column(String, nullable=True)
    outcome_status = Column(String, nullable=True)
    partner_owner = Column(String, nullable=True)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    documents = relationship("DealDocumentLink", back_populates="deal", cascade="all, delete-orphan")
    outcomes = relationship("OutcomeSnapshot", back_populates="deal", cascade="all, delete-orphan")
    workflow_runs = relationship("WorkflowRun", back_populates="deal", cascade="all, delete-orphan")
    tasks = relationship("PipelineTask", back_populates="deal", cascade="all, delete-orphan")
    contacts = relationship("Contact", back_populates="deal", cascade="all, delete-orphan")
    semantic_memories = relationship("SemanticMemory", back_populates="deal", cascade="all, delete-orphan")


class Company(Base):
    __tablename__ = "companies"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    sector = Column(String, nullable=True)
    geography = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    contacts = relationship("Contact", back_populates="company", cascade="all, delete-orphan")


class Contact(Base):
    __tablename__ = "contacts"

    id = Column(String, primary_key=True, default=_uuid)
    company_id = Column(String, ForeignKey("companies.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(String, ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String, nullable=False)
    title = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    company = relationship("Company", back_populates="contacts")
    deal = relationship("Deal", back_populates="contacts")


class DealDocumentLink(Base):
    __tablename__ = "deal_document_links"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String, ForeignKey("deals.id", ondelete="CASCADE"), index=True, nullable=False)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    relation_type = Column(String, default="evidence", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    deal = relationship("Deal", back_populates="documents")
    document = relationship("Document", back_populates="deal_links")


class DocumentProvenance(Base):
    __tablename__ = "document_provenance"

    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)
    sha256 = Column(String, nullable=False)
    source_path = Column(String, nullable=False)
    document_type = Column(String, nullable=True)
    language = Column(String, nullable=True)
    metadata_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    document = relationship("Document", back_populates="provenance")


class OutcomeSnapshot(Base):
    __tablename__ = "outcome_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    deal_id = Column(String, ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True)
    as_of_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    irr = Column(String, nullable=True)
    moic = Column(String, nullable=True)
    status = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    deal = relationship("Deal", back_populates="outcomes")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    traces = relationship("RetrievalTrace", back_populates="chat_log", cascade="all, delete-orphan")


class PipelineTask(Base):
    __tablename__ = "pipeline_tasks"

    id = Column(String, primary_key=True, default=_uuid)
    deal_id = Column(String, ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(String, nullable=False)
    status = Column(String, default="open", nullable=False)
    owner = Column(String, nullable=True)
    due_at = Column(DateTime, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    deal = relationship("Deal", back_populates="tasks")


class RetrievalTrace(Base):
    __tablename__ = "retrieval_traces"

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_log_id = Column(Integer, ForeignKey("chat_logs.id", ondelete="CASCADE"), nullable=False, index=True)
    query = Column(Text, nullable=False)
    analysis_mode = Column(String, default="document_search", nullable=False)
    prompt_version = Column(String, nullable=False)
    model_name = Column(String, nullable=False)
    selected_doc_ids = Column(JSON, default=list)
    retrieved_chunks = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    chat_log = relationship("ChatLog", back_populates="traces")


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True, default=_uuid)
    deal_id = Column(String, ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)
    workflow_type = Column(String, default="ic_copilot", nullable=False)
    status = Column(String, default="completed", nullable=False)
    input_json = Column(JSON, default=dict)
    output_json = Column(JSON, default=dict)
    model_name = Column(String, nullable=True)
    prompt_version = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    deal = relationship("Deal", back_populates="workflow_runs")


class SemanticMemory(Base):
    __tablename__ = "semantic_memories"

    id = Column(String, primary_key=True, default=_uuid)
    deal_id = Column(String, ForeignKey("deals.id", ondelete="CASCADE"), nullable=True, index=True)
    memory_type = Column(String, default="workflow_summary", nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=False)
    evidence_json = Column(JSON, default=list)
    source_workflow_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    deal = relationship("Deal", back_populates="semantic_memories")


class SkillRecord(Base):
    __tablename__ = "skill_records"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String, nullable=False)
    stage = Column(String, default="candidate", nullable=False)
    description = Column(Text, nullable=True)
    path = Column(String, nullable=False)
    source_workflow_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    payload_json = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
