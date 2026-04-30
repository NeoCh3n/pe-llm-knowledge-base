"""DuckDB analytics warehouse for PE Knowledge Base.

This module provides analytical capabilities using DuckDB for:
- Parsed document chunks and tables
- Heavy data comparisons and aggregations
- Workflow analysis outputs
"""

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, List, Optional

import duckdb
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models import Document, Chunk

logger = logging.getLogger(__name__)


class DuckDBAnalytics:
    """DuckDB analytics warehouse for document analysis."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or get_settings().duckdb_path
        self._connection: Optional[duckdb.DuckDBPyConnection] = None

    def _get_connection(self) -> duckdb.DuckDBPyConnection:
        """Get or create DuckDB connection."""
        if self._connection is None:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._connection = duckdb.connect(self.db_path)
            self._init_tables()
        return self._connection

    def _init_tables(self) -> None:
        """Initialize analytics tables."""
        conn = self._connection

        # Document chunks table for analytical queries
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                chunk_id VARCHAR PRIMARY KEY,
                document_id VARCHAR NOT NULL,
                filename VARCHAR NOT NULL,
                content TEXT NOT NULL,
                page_number INTEGER,
                chunk_index INTEGER,
                category VARCHAR,
                deal_outcome VARCHAR,
                deal_id VARCHAR,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Extracted tables from documents
        conn.execute("""
            CREATE TABLE IF NOT EXISTS extracted_tables (
                table_id VARCHAR PRIMARY KEY,
                document_id VARCHAR NOT NULL,
                filename VARCHAR NOT NULL,
                page_number INTEGER,
                table_content TEXT NOT NULL,
                table_type VARCHAR,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Document statistics for quick analytics
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_stats (
                document_id VARCHAR PRIMARY KEY,
                filename VARCHAR NOT NULL,
                total_chunks INTEGER DEFAULT 0,
                total_pages INTEGER DEFAULT 0,
                category VARCHAR,
                deal_id VARCHAR,
                upload_timestamp TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Deal analytics aggregation
        conn.execute("""
            CREATE TABLE IF NOT EXISTS deal_analytics (
                deal_id VARCHAR PRIMARY KEY,
                document_count INTEGER DEFAULT 0,
                total_chunks INTEGER DEFAULT 0,
                categories TEXT[],
                last_document_upload TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create indexes for common queries
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON document_chunks(document_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_category ON document_chunks(category)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_chunks_deal ON document_chunks(deal_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_tables_doc_id ON extracted_tables(document_id)")

        logger.info("DuckDB analytics tables initialized")

    @contextmanager
    def session(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Context manager for DuckDB sessions."""
        conn = self._get_connection()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise

    def sync_from_sqlite(self, db: Session, document_id: Optional[str] = None) -> None:
        """Sync document data from SQLite to DuckDB.

        Args:
            db: SQLAlchemy session
            document_id: If provided, only sync this specific document (incremental sync)
        """
        # Query only the document(s) we need
        if document_id:
            documents = db.query(Document).filter(Document.id == document_id).all()
            chunks = db.query(Chunk).filter(Chunk.document_id == document_id).all()
            logger.info(f"Incremental sync for document {document_id}: {len(documents)} docs, {len(chunks)} chunks")
        else:
            documents = db.query(Document).all()
            chunks = db.query(Chunk).all()
            logger.info(f"Full sync: {len(documents)} docs, {len(chunks)} chunks")

        with self.session() as conn:
            if document_id:
                # For incremental sync, only delete this document's existing data
                conn.execute("DELETE FROM document_chunks WHERE document_id = ?", [document_id])
                conn.execute("DELETE FROM document_stats WHERE document_id = ?", [document_id])
            else:
                # For full sync, clear all existing data
                conn.execute("DELETE FROM document_chunks")
                conn.execute("DELETE FROM document_stats")

            # Insert chunks
            for chunk in chunks:
                conn.execute("""
                    INSERT INTO document_chunks (
                        chunk_id, document_id, filename, content,
                        page_number, chunk_index, category, deal_outcome, deal_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (chunk_id) DO UPDATE SET
                        content = EXCLUDED.content,
                        page_number = EXCLUDED.page_number,
                        category = EXCLUDED.category,
                        deal_outcome = EXCLUDED.deal_outcome,
                        deal_id = EXCLUDED.deal_id
                """, [
                    f"{chunk.document_id}_{chunk.chunk_index}",
                    chunk.document_id,
                    chunk.filename,
                    chunk.content,
                    chunk.page_number,
                    chunk.chunk_index,
                    chunk.category,
                    chunk.deal_outcome,
                    chunk.deal_id,
                ])

            # Insert document stats
            for doc in documents:
                doc_chunks = [c for c in chunks if c.document_id == doc.id]
                total_pages = max([c.page_number for c in doc_chunks], default=0)

                conn.execute("""
                    INSERT INTO document_stats (
                        document_id, filename, total_chunks, total_pages,
                        category, deal_id, upload_timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT (document_id) DO UPDATE SET
                        total_chunks = EXCLUDED.total_chunks,
                        total_pages = EXCLUDED.total_pages,
                        last_updated = CURRENT_TIMESTAMP
                """, [
                    doc.id,
                    doc.filename,
                    len(doc_chunks),
                    total_pages,
                    doc.category,
                    doc.deal_id,
                    doc.upload_timestamp,
                ])

            conn.commit()

        logger.info(f"Synced {len(documents)} documents and {len(chunks)} chunks to DuckDB")

    def add_chunk(self, chunk_data: dict[str, Any]) -> None:
        """Add a single chunk to analytics."""
        with self.session() as conn:
            conn.execute("""
                INSERT INTO document_chunks (
                    chunk_id, document_id, filename, content,
                    page_number, chunk_index, category, deal_outcome, deal_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT (chunk_id) DO UPDATE SET
                    content = EXCLUDED.content,
                    page_number = EXCLUDED.page_number
            """, [
                chunk_data.get("chunk_id"),
                chunk_data.get("document_id"),
                chunk_data.get("filename"),
                chunk_data.get("content"),
                chunk_data.get("page_number"),
                chunk_data.get("chunk_index"),
                chunk_data.get("category"),
                chunk_data.get("deal_outcome"),
                chunk_data.get("deal_id"),
            ])
            conn.commit()

    def add_extracted_table(self, table_data: dict[str, Any]) -> None:
        """Add an extracted table from document parsing."""
        with self.session() as conn:
            conn.execute("""
                INSERT INTO extracted_tables (
                    table_id, document_id, filename, page_number,
                    table_content, table_type
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT (table_id) DO UPDATE SET
                    table_content = EXCLUDED.table_content,
                    table_type = EXCLUDED.table_type
            """, [
                table_data.get("table_id"),
                table_data.get("document_id"),
                table_data.get("filename"),
                table_data.get("page_number"),
                table_data.get("table_content"),
                table_data.get("table_type"),
            ])
            conn.commit()

    def delete_document(self, document_id: str) -> None:
        """Delete all data for a specific document."""
        with self.session() as conn:
            conn.execute("DELETE FROM document_chunks WHERE document_id = ?", [document_id])
            conn.execute("DELETE FROM document_stats WHERE document_id = ?", [document_id])
            conn.execute("DELETE FROM extracted_tables WHERE document_id = ?", [document_id])
            conn.commit()
        logger.info("Deleted document %s from DuckDB analytics", document_id)

    def query_chunks_by_deal(self, deal_id: str, category: Optional[str] = None) -> List[dict]:
        """Query all chunks for a specific deal."""
        with self.session() as conn:
            if category:
                result = conn.execute("""
                    SELECT * FROM document_chunks
                    WHERE deal_id = ? AND category = ?
                    ORDER BY page_number, chunk_index
                """, [deal_id, category]).fetchall()
            else:
                result = conn.execute("""
                    SELECT * FROM document_chunks
                    WHERE deal_id = ?
                    ORDER BY page_number, chunk_index
                """, [deal_id]).fetchall()

            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]

    def query_category_stats(self) -> List[dict]:
        """Get document statistics by category."""
        with self.session() as conn:
            result = conn.execute("""
                SELECT
                    category,
                    COUNT(DISTINCT document_id) as document_count,
                    COUNT(*) as chunk_count,
                    AVG(total_pages) as avg_pages
                FROM document_stats
                GROUP BY category
                ORDER BY document_count DESC
            """).fetchall()

            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]

    def query_deal_comparison(self, deal_ids: List[str]) -> List[dict]:
        """Compare multiple deals by document metrics."""
        with self.session() as conn:
            placeholders = ", ".join(["?"] * len(deal_ids))
            result = conn.execute(f"""
                SELECT
                    deal_id,
                    COUNT(DISTINCT document_id) as document_count,
                    COUNT(*) as total_chunks,
                    ARRAY_AGG(DISTINCT category) as categories
                FROM document_chunks
                WHERE deal_id IN ({placeholders})
                GROUP BY deal_id
            """, deal_ids).fetchall()

            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]

    def search_tables(self, query: str) -> List[dict]:
        """Search extracted tables by content."""
        with self.session() as conn:
            result = conn.execute("""
                SELECT * FROM extracted_tables
                WHERE table_content ILIKE ?
                ORDER BY extracted_at DESC
            """, [f"%{query}%"]).fetchall()

            columns = [desc[0] for desc in conn.description]
            return [dict(zip(columns, row)) for row in result]

    def get_document_table_summary(self, document_id: str) -> dict:
        """Get summary of tables in a document."""
        with self.session() as conn:
            result = conn.execute("""
                SELECT
                    COUNT(*) as table_count,
                    ARRAY_AGG(DISTINCT table_type) as table_types
                FROM extracted_tables
                WHERE document_id = ?
            """, [document_id]).fetchone()

            if result:
                return {"table_count": result[0], "table_types": result[1]}
            return {"table_count": 0, "table_types": []}

    def export_to_parquet(self, table_name: str, output_path: str) -> None:
        """Export a table to Parquet format for external analysis."""
        with self.session() as conn:
            conn.execute(f"""
                COPY (SELECT * FROM {table_name})
                TO '{output_path}' (FORMAT PARQUET)
            """)
        logger.info(f"Exported {table_name} to {output_path}")

    def close(self) -> None:
        """Close DuckDB connection."""
        if self._connection:
            self._connection.close()
            self._connection = None


# Global instance
_duckdb_analytics: Optional[DuckDBAnalytics] = None


def get_duckdb_analytics() -> DuckDBAnalytics:
    """Get or create global DuckDB analytics instance."""
    global _duckdb_analytics
    if _duckdb_analytics is None:
        _duckdb_analytics = DuckDBAnalytics()
    return _duckdb_analytics
