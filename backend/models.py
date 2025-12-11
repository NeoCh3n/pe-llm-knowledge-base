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


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(String, primary_key=True, default=_uuid)
    document_id = Column(String, ForeignKey("documents.id", ondelete="CASCADE"), index=True, nullable=False)
    content = Column(Text, nullable=False)
    page_number = Column(Integer, default=1)
    chunk_index = Column(Integer, default=0)
    source = Column(String, nullable=True)

    document = relationship("Document", back_populates="chunks")


class ChatLog(Base):
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_query = Column(Text, nullable=False)
    ai_response = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
