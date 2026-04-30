"""
DuckDB Analytics API endpoints for PE Knowledge Base.

This module provides FastAPI routes for DuckDB analytics functionality.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.analytics import get_duckdb_analytics

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analytics", tags=["analytics"])


class AnalyticsSyncRequest(BaseModel):
    sync_type: str = "full"  # "full" or "incremental"


class AnalyticsSyncResponse(BaseModel):
    status: str
    documents_synced: int
    chunks_synced: int


class CategoryStatsResponse(BaseModel):
    category: str
    document_count: int
    chunk_count: int
    avg_pages: float


class DealComparisonRequest(BaseModel):
    deal_ids: list[str]


class DealComparisonResponse(BaseModel):
    deal_id: str
    document_count: int
    total_chunks: int
    categories: list[str]


@router.post("/sync", response_model=AnalyticsSyncResponse)
def analytics_sync(request: AnalyticsSyncRequest, db: Session = Depends(get_db)):
    """Sync SQLite data to DuckDB analytics warehouse."""
    try:
        analytics = get_duckdb_analytics()
        analytics.sync_from_sqlite(db)

        # Get counts for response
        with analytics.session() as conn:
            doc_count = conn.execute("SELECT COUNT(DISTINCT document_id) FROM document_chunks").fetchone()[0]
            chunk_count = conn.execute("SELECT COUNT(*) FROM document_chunks").fetchone()[0]

        return AnalyticsSyncResponse(
            status="success",
            documents_synced=doc_count,
            chunks_synced=chunk_count,
        )
    except Exception as exc:
        logger.exception("Analytics sync failed")
        raise HTTPException(status_code=500, detail=f"Sync failed: {exc}") from exc


@router.get("/category-stats", response_model=list[CategoryStatsResponse])
def analytics_category_stats():
    """Get document statistics grouped by category."""
    try:
        analytics = get_duckdb_analytics()
        stats = analytics.query_category_stats()
        return [CategoryStatsResponse(**row) for row in stats]
    except Exception as exc:
        logger.exception("Category stats query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc


@router.post("/deal-comparison", response_model=list[DealComparisonResponse])
def analytics_deal_comparison(request: DealComparisonRequest):
    """Compare multiple deals by document metrics."""
    if len(request.deal_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 deal IDs required for comparison")

    try:
        analytics = get_duckdb_analytics()
        results = analytics.query_deal_comparison(request.deal_ids)
        return [DealComparisonResponse(**row) for row in results]
    except Exception as exc:
        logger.exception("Deal comparison query failed")
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc


@router.get("/deal/{deal_id}/chunks")
def analytics_deal_chunks(deal_id: str, category: str | None = None):
    """Get all document chunks for a specific deal."""
    try:
        analytics = get_duckdb_analytics()
        chunks = analytics.query_chunks_by_deal(deal_id, category)
        return {"deal_id": deal_id, "chunks": chunks, "total": len(chunks)}
    except Exception as exc:
        logger.exception(f"Deal chunks query failed for {deal_id}")
        raise HTTPException(status_code=500, detail=f"Query failed: {exc}") from exc


@router.get("/tables/search")
def analytics_search_tables(query: str):
    """Search extracted tables by content."""
    try:
        analytics = get_duckdb_analytics()
        tables = analytics.search_tables(query)
        return {"query": query, "tables": tables, "total": len(tables)}
    except Exception as exc:
        logger.exception("Table search failed")
        raise HTTPException(status_code=500, detail=f"Search failed: {exc}") from exc
