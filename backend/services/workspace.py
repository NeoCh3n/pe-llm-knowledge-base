from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from backend.config import get_settings
from backend.services.parser import ParsedChunk

settings = get_settings()


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return slug or "artifact"


class WorkspaceManager:
    def __init__(self) -> None:
        self.workspace_root = Path(settings.workspace_root)
        self.deals_root = Path(settings.deals_root)
        self.skills_root = Path(settings.skills_root)
        self.postmortems_root = Path(settings.postmortems_root)
        self.mempalace_root = Path(settings.mempalace_root)
        self.templates_root = Path(settings.templates_root)
        self.cache_root = Path(settings.cache_root)
        self.logs_root = Path(settings.logs_root)
        self.ensure_layout()

    def ensure_layout(self) -> None:
        for path in (
            self.workspace_root,
            self.deals_root,
            self.skills_root,
            self.postmortems_root,
            self.mempalace_root,
            self.templates_root,
            self.cache_root,
            self.logs_root,
        ):
            path.mkdir(parents=True, exist_ok=True)

        for stage in ("draft", "candidate", "tested", "blessed", "deprecated"):
            (self.skills_root / stage).mkdir(parents=True, exist_ok=True)

    def deal_root(self, deal_id: str | None) -> Path:
        deal_segment = f"deal_{deal_id}" if deal_id else "deal_unassigned"
        root = self.deals_root / deal_segment
        for name in ("raw", "parsed", "notes", "models", "outputs"):
            (root / name).mkdir(parents=True, exist_ok=True)
        return root

    def store_raw_document(self, document_id: str, filename: str, content: bytes, deal_id: str | None = None) -> Path:
        deal_root = self.deal_root(deal_id)
        target = deal_root / "raw" / f"{document_id}_{filename}"
        target.write_bytes(content)
        return target

    def write_parsed_artifacts(
        self,
        document_id: str,
        filename: str,
        chunks: list[ParsedChunk],
        deal_id: str | None = None,
    ) -> dict[str, str]:
        deal_root = self.deal_root(deal_id)
        parsed_dir = deal_root / "parsed"
        stem = _slugify(Path(filename).stem)
        markdown_path = parsed_dir / f"{document_id}_{stem}.md"
        chunks_path = parsed_dir / f"{document_id}_{stem}.chunks.json"

        markdown_path.write_text("\n\n---\n\n".join(chunk.content for chunk in chunks), encoding="utf-8")
        chunks_path.write_text(
            json.dumps(
                [
                    {
                        "content": chunk.content,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "source": chunk.source,
                        "section": chunk.section,
                    }
                    for chunk in chunks
                ],
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        return {
            "markdown_path": str(markdown_path),
            "chunks_path": str(chunks_path),
        }

    def write_workflow_output(
        self,
        workflow_id: str,
        deal_id: str | None,
        title: str,
        payload: dict[str, Any],
    ) -> Path:
        deal_root = self.deal_root(deal_id)
        output_path = deal_root / "outputs" / f"{workflow_id}_{_slugify(title)}.md"
        lines = [
            f"# {title}",
            "",
            f"- workflow_id: `{workflow_id}`",
            f"- deal_id: `{deal_id or 'unassigned'}`",
            "",
            "## Draft Answer",
            payload.get("draft_answer", "No answer"),
            "",
            "## Risk Gaps",
        ]
        lines.extend([f"- {item}" for item in payload.get("risk_gaps", [])] or ["- None"])
        lines.extend(["", "## Diligence Questions"])
        lines.extend([f"- {item}" for item in payload.get("diligence_questions", [])] or ["- None"])
        lines.extend(["", "## Committee Challenges"])
        lines.extend([f"- {item}" for item in payload.get("committee_challenges", [])] or ["- None"])
        output_path.write_text("\n".join(lines), encoding="utf-8")
        return output_path

    def write_postmortem(
        self,
        workflow_id: str,
        deal_id: str | None,
        summary: str,
        metadata: dict[str, Any],
    ) -> Path:
        target = self.postmortems_root / f"{workflow_id}.md"
        frontmatter = "\n".join([f"- {key}: {value}" for key, value in metadata.items()])
        target.write_text(
            f"# Postmortem {workflow_id}\n\n{summary}\n\n## Metadata\n{frontmatter}\n",
            encoding="utf-8",
        )
        return target

    def write_skill_file(self, stage: str, name: str, content: str) -> Path:
        stage_dir = self.skills_root / stage
        stage_dir.mkdir(parents=True, exist_ok=True)
        target = stage_dir / f"{_slugify(name)}.md"
        target.write_text(content, encoding="utf-8")
        return target

    def write_mempalace_artifact(self, memory_id: str, payload: dict[str, Any]) -> Path:
        export_dir = self.mempalace_root / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        target = export_dir / f"{memory_id}.json"
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def summary(self) -> dict[str, str]:
        return {
            "workspace_root": str(self.workspace_root),
            "deals_root": str(self.deals_root),
            "skills_root": str(self.skills_root),
            "mempalace_root": str(self.mempalace_root),
        }
