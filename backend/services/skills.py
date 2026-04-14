from __future__ import annotations

from backend.services.workspace import WorkspaceManager


class SkillManager:
    def __init__(self, workspace: WorkspaceManager) -> None:
        self.workspace = workspace

    def build_candidate_content(
        self,
        workflow_id: str,
        query: str,
        payload: dict,
    ) -> tuple[str, str]:
        skill_name = f"workflow-{workflow_id}-playbook"
        content = "\n".join(
            [
                f"# {skill_name}",
                "",
                "## Intent",
                query,
                "",
                "## Reusable Steps",
                "1. Load the current deal shell and linked documents from SQLite.",
                "2. Pull the parsed artifacts from the local workspace and supporting evidence from retrieval.",
                "3. Compare the current case against similar precedents and extract the highest-signal red flags.",
                "4. Draft diligence questions and memo scaffolding with strict evidence links.",
                "5. Store the outcome, postmortem, and promoted learnings back into the local system.",
                "",
                "## Risk Gaps",
            ]
        )
        risk_gap_lines = [f"- {item}" for item in payload.get("risk_gaps", [])] or ["- None"]
        question_lines = [f"- {item}" for item in payload.get("diligence_questions", [])] or ["- None"]
        content = "\n".join(
            [
                content,
                *risk_gap_lines,
                "",
                "## Diligence Questions",
                *question_lines,
                "",
                "## Draft Answer",
                payload.get("draft_answer", "No answer"),
            ]
        )
        return skill_name, content

    def create_candidate(self, workflow_id: str, query: str, payload: dict) -> tuple[str, str]:
        skill_name, content = self.build_candidate_content(workflow_id, query, payload)
        path = self.workspace.write_skill_file("candidate", skill_name, content)
        return skill_name, str(path)
