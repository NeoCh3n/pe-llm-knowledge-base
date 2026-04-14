from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from backend.models import AuditLog, SemanticMemory
from backend.services.workspace import WorkspaceManager


class MemPalaceStore:
    """
    Local-first adapter for semantic memory writeback.
    The authoritative metadata lives in SQLite; export artifacts are mirrored
    into the workspace so an external MemPalace service can ingest them later.
    """

    def __init__(self, workspace: WorkspaceManager) -> None:
        self.workspace = workspace

    def write_summary(
        self,
        db: Session,
        deal_id: str | None,
        workflow_id: str,
        title: str,
        summary: str,
        evidence: list[dict[str, Any]],
    ) -> SemanticMemory:
        memory = SemanticMemory(
            id=str(uuid.uuid4()),
            deal_id=deal_id,
            memory_type="workflow_summary",
            title=title,
            summary=summary,
            evidence_json=evidence,
            source_workflow_id=workflow_id,
        )
        db.add(memory)
        db.flush()

        export_payload = {
            "memory_id": memory.id,
            "deal_id": deal_id,
            "workflow_id": workflow_id,
            "title": title,
            "summary": summary,
            "evidence": evidence,
            "created_at": datetime.utcnow().isoformat(),
        }
        export_path = self.workspace.write_mempalace_artifact(memory.id, export_payload)
        db.add(
            AuditLog(
                entity_type="semantic_memory",
                entity_id=memory.id,
                action="mempalace_exported",
                payload_json={"path": str(export_path), "workflow_id": workflow_id},
            )
        )
        return memory
