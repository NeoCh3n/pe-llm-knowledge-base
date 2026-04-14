from __future__ import annotations

from datetime import datetime
from pathlib import Path

from backend.config import get_settings
from backend.services.parser import ParsedChunk

settings = get_settings()


class DuckDBAnalyticsStore:
    def __init__(self) -> None:
        try:
            import duckdb
        except Exception as exc:
            raise RuntimeError("duckdb is required for the analytics layer") from exc

        self._duckdb = duckdb
        self.path = Path(settings.duckdb_path)
        self.conn = duckdb.connect(str(self.path))
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS document_chunks (
                document_id TEXT,
                filename TEXT,
                deal_id TEXT,
                page_number INTEGER,
                chunk_index INTEGER,
                section TEXT,
                source_path TEXT,
                content TEXT,
                ingested_at TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS analysis_runs (
                workflow_id TEXT,
                deal_id TEXT,
                query TEXT,
                report_path TEXT,
                created_at TIMESTAMP
            )
            """
        )
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS extracted_tables (
                document_id TEXT,
                filename TEXT,
                deal_id TEXT,
                page_number INTEGER,
                chunk_index INTEGER,
                section TEXT,
                markdown_table TEXT,
                extracted_at TIMESTAMP
            )
            """
        )

    def replace_document_chunks(
        self,
        document_id: str,
        filename: str,
        deal_id: str | None,
        source_path: str,
        chunks: list[ParsedChunk],
    ) -> None:
        now = datetime.utcnow()
        self.conn.execute("DELETE FROM document_chunks WHERE document_id = ?", [document_id])
        self.conn.execute("DELETE FROM extracted_tables WHERE document_id = ?", [document_id])

        rows = [
            (
                document_id,
                filename,
                deal_id,
                chunk.page_number,
                chunk.chunk_index,
                chunk.section,
                source_path,
                chunk.content,
                now,
            )
            for chunk in chunks
        ]
        if rows:
            self.conn.executemany(
                """
                INSERT INTO document_chunks
                (document_id, filename, deal_id, page_number, chunk_index, section, source_path, content, ingested_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )

        table_rows = [
            (
                document_id,
                filename,
                deal_id,
                chunk.page_number,
                chunk.chunk_index,
                chunk.section,
                chunk.content,
                now,
            )
            for chunk in chunks
            if "|" in chunk.content and "---" in chunk.content
        ]
        if table_rows:
            self.conn.executemany(
                """
                INSERT INTO extracted_tables
                (document_id, filename, deal_id, page_number, chunk_index, section, markdown_table, extracted_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                table_rows,
            )

    def log_analysis_run(self, workflow_id: str, deal_id: str | None, query: str, report_path: str) -> None:
        self.conn.execute(
            """
            INSERT INTO analysis_runs (workflow_id, deal_id, query, report_path, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            [workflow_id, deal_id, query, report_path, datetime.utcnow()],
        )

    def delete_document(self, document_id: str) -> None:
        self.conn.execute("DELETE FROM document_chunks WHERE document_id = ?", [document_id])
        self.conn.execute("DELETE FROM extracted_tables WHERE document_id = ?", [document_id])

    def health(self) -> dict[str, str]:
        return {
            "path": str(self.path),
            "status": "ok",
        }
