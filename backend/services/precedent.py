from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from sqlalchemy.orm import Session

from backend.models import Deal, DealDocumentLink, Document
from backend.services.vector import QdrantVectorStore


@dataclass
class PrecedentResult:
    document_id: str
    filename: str
    deal_id: str | None
    deal_name: str | None
    category: str
    deal_outcome: str | None
    score: float
    page_number: int
    chunk_index: int
    evidence: str
    sector: str | None
    stage: str | None
    geography: str | None
    decision_status: str | None
    outcome_status: str | None


def find_precedents(
    db: Session,
    vector_store: QdrantVectorStore,
    query: str,
    doc_ids: list[str] | None = None,
    categories: list[str] | None = None,
    deal_outcomes: list[str] | None = None,
    top_k: int = 12,
) -> list[PrecedentResult]:
    raw_hits = vector_store.search(
        query,
        doc_ids=doc_ids,
        top_k=top_k,
        categories=categories,
        deal_outcomes=deal_outcomes,
    )
    if not raw_hits:
        return []

    doc_ids_to_fetch = list({hit.document_id for hit in raw_hits})
    docs = db.query(Document).filter(Document.id.in_(doc_ids_to_fetch)).all()
    doc_map = {doc.id: doc for doc in docs}

    links = db.query(DealDocumentLink).filter(DealDocumentLink.document_id.in_(doc_ids_to_fetch)).all()
    deal_ids = list({link.deal_id for link in links})
    deals = db.query(Deal).filter(Deal.id.in_(deal_ids)).all() if deal_ids else []

    link_map = defaultdict(list)
    for link in links:
        link_map[link.document_id].append(link)
    deal_map = {deal.id: deal for deal in deals}

    results: list[PrecedentResult] = []
    for hit in raw_hits:
        doc = doc_map.get(hit.document_id)
        linked_deal = None
        if hit.document_id in link_map:
            linked_deal = deal_map.get(link_map[hit.document_id][0].deal_id)

        results.append(
            PrecedentResult(
                document_id=hit.document_id,
                filename=hit.filename,
                deal_id=linked_deal.id if linked_deal else None,
                deal_name=linked_deal.name if linked_deal else None,
                category=doc.category if doc else hit.category,
                deal_outcome=doc.deal_outcome if doc else hit.deal_outcome,
                score=hit.score,
                page_number=hit.page_number,
                chunk_index=hit.chunk_index,
                evidence=hit.content,
                sector=linked_deal.sector if linked_deal else None,
                stage=linked_deal.stage if linked_deal else None,
                geography=linked_deal.geography if linked_deal else None,
                decision_status=linked_deal.decision_status if linked_deal else None,
                outcome_status=linked_deal.outcome_status if linked_deal else None,
            )
        )

    return results


def summarize_precedents(results: list[PrecedentResult]) -> dict[str, Any]:
    buckets: dict[str, list[dict[str, Any]]] = {
        "invested": [],
        "passed": [],
        "exited": [],
        "other": [],
    }

    for item in results:
        bucket = item.deal_outcome or "other"
        if bucket not in buckets:
            bucket = "other"
        buckets[bucket].append(
            {
                "document_id": item.document_id,
                "filename": item.filename,
                "deal_id": item.deal_id,
                "deal_name": item.deal_name,
                "category": item.category,
                "deal_outcome": item.deal_outcome,
                "score": item.score,
                "page_number": item.page_number,
                "chunk_index": item.chunk_index,
                "evidence": item.evidence,
                "sector": item.sector,
                "stage": item.stage,
                "geography": item.geography,
                "decision_status": item.decision_status,
                "outcome_status": item.outcome_status,
            }
        )

    return {
        "total": len(results),
        "buckets": buckets,
    }
