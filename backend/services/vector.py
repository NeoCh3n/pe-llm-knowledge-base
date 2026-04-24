from dataclasses import dataclass
from typing import Any, Iterable, List, Optional, Sequence

import numpy as np
from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models

from backend.config import get_settings
from backend.services.parser import ParsedChunk

settings = get_settings()


@dataclass
class ScoredChunk:
    content: str
    score: float
    document_id: str
    filename: str
    page_number: int
    chunk_index: int
    source: str
    section: Optional[str]
    category: str
    deal_outcome: Optional[str]


class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model = TextEmbedding(model_name=model_name)

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return [list(vec) for vec in self.model.embed(texts)]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]


class QdrantVectorStore:
    def __init__(self):
        self.client = QdrantClient(
            url=settings.qdrant_url, api_key=settings.qdrant_api_key
        )
        self.embedding = EmbeddingModel(settings.embedding_model_name)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Create the Qdrant collection if it does not already exist.

        Uses create_collection (non-destructive) rather than recreate_collection
        so that a service restart never wipes existing vectors.
        """
        try:
            self.client.http.collections_api.get_collection(
                collection_name=settings.qdrant_collection
            )
            return  # already exists — nothing to do
        except Exception:
            pass  # collection not found — create it below

        try:
            self.client.http.collections_api.create_collection(
                collection_name=settings.qdrant_collection,
                create_collection=models.CreateCollection(
                    vectors=models.VectorParams(
                        size=settings.embedding_dim,
                        distance=models.Distance.COSINE,
                    ),
                ),
            )
        except Exception as exc:
            # Tolerate race condition where another worker created it first
            if "already exists" in str(exc).lower():
                return
            raise

    def upsert_chunks(
        self,
        chunks: Iterable[ParsedChunk],
        document_id: str,
        filename: str,
        metadata: Optional[dict] = None,
    ) -> None:
        chunk_list = list(chunks)
        vectors = self.embedding.embed([chunk.content for chunk in chunk_list])
        metadata = metadata or {}

        points = []
        for chunk, vector in zip(chunk_list, vectors):
            points.append(
                models.PointStruct(
                    id=f"{document_id}-{chunk.chunk_index}",
                    vector=vector,
                    payload={
                        "document_id": document_id,
                        "filename": filename,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "source": chunk.source,
                        "section": chunk.section,
                        "content": chunk.content,
                        "category": metadata.get("category"),
                        "deal_outcome": metadata.get("deal_outcome"),
                        "deal_id": metadata.get("deal_id"),
                    },
                )
            )

        # Use new API for upsert
        points_list = models.PointsList(points=points)
        self.client.http.points_api.upsert_points(
            collection_name=settings.qdrant_collection,
            wait=True,
            point_insert_operations=points_list,
        )

    def search(
        self,
        query: str,
        doc_ids: list[str] | None = None,
        top_k: int = 5,
        categories: list[str] | None = None,
        deal_outcomes: list[str] | None = None,
    ) -> List[ScoredChunk]:
        query_vector = self.embedding.embed_one(query)

        must_conditions: list[models.FieldCondition] = []
        if doc_ids:
            must_conditions.append(
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchAny(any=doc_ids),
                )
            )
        if categories:
            must_conditions.append(
                models.FieldCondition(
                    key="category",
                    match=models.MatchAny(any=categories),
                )
            )
        if deal_outcomes:
            must_conditions.append(
                models.FieldCondition(
                    key="deal_outcome",
                    match=models.MatchAny(any=deal_outcomes),
                )
            )

        search_filter = models.Filter(must=must_conditions) if must_conditions else None

        # Build search request for new API
        search_request = models.SearchRequest(
            vector=models.NamedVector(
                name="",
                vector=query_vector,
            ),
            filter=search_filter,
            limit=top_k,
            with_payload=True,
        )

        # Call new API
        response = self.client.http.search_api.search_points(
            collection_name=settings.qdrant_collection,
            search_request=search_request,
        )

        scored: List[ScoredChunk] = []
        for hit in response.result or []:
            payload = hit.payload or {}
            scored.append(
                ScoredChunk(
                    content=payload.get("content", ""),
                    score=hit.score or 0.0,
                    document_id=str(payload.get("document_id", "")),
                    filename=str(payload.get("filename", "")),
                    page_number=int(payload.get("page_number", 1)),
                    chunk_index=int(payload.get("chunk_index", 0)),
                    source=str(payload.get("source", "")),
                    section=payload.get("section"),
                    category=str(payload.get("category", "")),
                    deal_outcome=payload.get("deal_outcome"),
                )
            )

        return scored

    def delete_document(self, document_id: str) -> None:
        # Use FilterSelector directly (PointsSelector is a Union type)
        selector = models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="document_id",
                        match=models.MatchValue(value=document_id),
                    )
                ]
            )
        )
        self.client.http.points_api.delete_points(
            collection_name=settings.qdrant_collection,
            wait=True,
            points_selector=selector,
        )
