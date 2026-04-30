from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.models import Deal
from backend.services.precedent import find_precedents, summarize_precedents
from backend.services.rag import generate_answer
from backend.services.vector import QdrantVectorStore


WORKFLOW_PROMPT_VERSION = "ic_workflow_v1"


@dataclass
class WorkflowPack:
    precedent_scan: dict[str, Any]
    risk_gaps: list[str]
    diligence_questions: list[str]
    ic_memo_outline: list[str]
    committee_challenges: list[str]


def _derive_risk_gaps(query: str, precedent_summary: dict[str, Any], deal: Deal | None) -> list[str]:
    gaps: list[str] = []
    if deal and not deal.outcome_status:
        gaps.append("Outcome data is missing for the current deal shell; compare only against historical precedent, not realized performance.")
    if precedent_summary["buckets"]["passed"]:
        gaps.append("Rejected precedents exist for this query theme; review why those cases failed governance or diligence thresholds.")
    if not precedent_summary["buckets"]["exited"]:
        gaps.append("There are no clearly exited precedents in the retrieved set; realized-outcome evidence is thin.")
    if "regulation" in query.lower() or "compliance" in query.lower():
        gaps.append("Regulatory exposure was explicitly referenced in the query and should be treated as a first-class diligence track.")
    if not gaps:
        gaps.append("No dominant gap pattern detected from the current precedent set. Validate through fresh diligence rather than assuming fit.")
    return gaps


def _derive_questions(deal: Deal | None, precedent_summary: dict[str, Any]) -> list[str]:
    questions = [
        "Which assumptions in the current memo are unsupported by cited evidence?",
        "Which historical passed deals most closely resemble this opportunity, and what killed them?",
        "What outcome evidence exists for the closest invested precedents?",
    ]
    if deal and deal.stage:
        questions.append(f"What stage-specific risks recur in the firm's {deal.stage} precedents?")
    if deal and deal.sector:
        questions.append(f"What sector-specific failure modes recur across {deal.sector} deals?")
    if precedent_summary["buckets"]["invested"]:
        questions.append("Which operating metrics separated successful invested precedents from mediocre ones?")
    return questions


def _build_memo_outline(deal: Deal | None) -> list[str]:
    deal_name = deal.name if deal else "Current Opportunity"
    return [
        f"Executive summary for {deal_name}",
        "Investment thesis grounded in retrieved precedent",
        "Comparison against approved, rejected, and exited cases",
        "Key risks, open diligence items, and gating assumptions",
        "Governance considerations and likely IC objections",
        "Evidence appendix with cited documents and pages",
    ]


def _build_committee_challenges(precedent_summary: dict[str, Any], deal: Deal | None) -> list[str]:
    challenges = [
        "What is the strongest argument that this deal fits historical style but not historical success?",
        "Which piece of evidence in the current packet would an opposing partner attack first?",
        "If this deal underperforms, which ignored precedent would look most obvious in hindsight?",
    ]
    if deal and deal.geography:
        challenges.append(f"Are there geography-specific precedents in {deal.geography}, or are we overgeneralizing from other markets?")
    if precedent_summary["buckets"]["passed"]:
        challenges.append("Why are the most similar passed deals not disqualifying here?")
    return challenges


def run_ic_workflow(
    db: Session,
    vector_store: QdrantVectorStore,
    query: str,
    deal_id: str | None = None,
    doc_ids: list[str] | None = None,
    categories: list[str] | None = None,
    deal_outcomes: list[str] | None = None,
) -> dict[str, Any]:
    deal = db.query(Deal).filter(Deal.id == deal_id).first() if deal_id else None
    precedents = find_precedents(
        db,
        vector_store,
        query,
        doc_ids=doc_ids,
        categories=categories,
        deal_outcomes=deal_outcomes,
        top_k=8,  # Reduced from 16 to avoid context window overflow
    )
    precedent_summary = summarize_precedents(precedents)

    top_hits = precedents[:5]
    llm_answer = generate_answer(query, [
        type("WorkflowChunk", (), {
            "filename": item.filename,
            "page_number": item.page_number,
            "document_id": item.document_id,
            "content": item.evidence,
            "category": item.category,
            "deal_outcome": item.deal_outcome,
            "chunk_index": item.chunk_index,
        })()
        for item in top_hits
    ]) if top_hits else {
        "answer": "No precedent evidence was retrieved.",
        "sources": [],
        "prompt_version": WORKFLOW_PROMPT_VERSION,
        "model_name": "",
    }

    pack = WorkflowPack(
        precedent_scan=precedent_summary,
        risk_gaps=_derive_risk_gaps(query, precedent_summary, deal),
        diligence_questions=_derive_questions(deal, precedent_summary),
        ic_memo_outline=_build_memo_outline(deal),
        committee_challenges=_build_committee_challenges(precedent_summary, deal),
    )

    return {
        "deal": {
            "id": deal.id,
            "name": deal.name,
            "sector": deal.sector,
            "stage": deal.stage,
            "geography": deal.geography,
            "decision_status": deal.decision_status,
            "outcome_status": deal.outcome_status,
        } if deal else None,
        "query": query,
        "precedent_scan": pack.precedent_scan,
        "risk_gaps": pack.risk_gaps,
        "diligence_questions": pack.diligence_questions,
        "ic_memo_outline": pack.ic_memo_outline,
        "committee_challenges": pack.committee_challenges,
        "draft_answer": llm_answer["answer"],
        "draft_sources": llm_answer["sources"],
        "prompt_version": llm_answer.get("prompt_version", WORKFLOW_PROMPT_VERSION),
        "model_name": llm_answer.get("model_name", ""),
    }
