from dataclasses import dataclass
from typing import Iterable, List, Sequence

from fastembed import TextEmbedding
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest

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


class EmbeddingModel:
    def __init__(self, model_name: str):
        self.model = TextEmbedding(model_name=model_name)

    def embed(self, texts: Sequence[str]) -> List[List[float]]:
        return [vec for vec in self.model.embed(texts)]

    def embed_one(self, text: str) -> List[float]:
        return self.embed([text])[0]


class QdrantVectorStore:
    def __init__(self):
        self.client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        self.embedding = EmbeddingModel(settings.embedding_model_name)
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        try:
            self.client.get_collection(settings.qdrant_collection)
        except Exception:
            self.client.recreate_collection(
                collection_name=settings.qdrant_collection,
                vectors_config=rest.VectorParams(
                    size=settings.embedding_dim,
                    distance=rest.Distance.COSINE,
                ),
            )

    def upsert_chunks(self, chunks: Iterable[ParsedChunk], document_id: str, filename: str) -> None:
        chunk_list = list(chunks)
        vectors = self.embedding.embed([chunk.content for chunk in chunk_list])

        points = []
        for chunk, vector in zip(chunk_list, vectors):
            points.append(
                rest.PointStruct(
                    id=f"{document_id}-{chunk.chunk_index}",
                    vector=vector,
                    payload={
                        "document_id": document_id,
                        "filename": filename,
                        "page_number": chunk.page_number,
                        "chunk_index": chunk.chunk_index,
                        "source": chunk.source,
                        "content": chunk.content,
                    },
                )
            )

        self.client.upsert(collection_name=settings.qdrant_collection, points=points, wait=True)

    def search(self, query: str, doc_ids: list[str] | None = None, top_k: int = 5) -> List[ScoredChunk]:
        query_vector = self.embedding.embed_one(query)

        search_filter = None
        if doc_ids:
            search_filter = rest.Filter(
                must=[
                    rest.FieldCondition(
                        key="document_id",
                        match=rest.MatchAny(any=doc_ids),
                    )
                ]
            )

        results = self.client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            query_filter=search_filter,
            limit=top_k,
        )

        scored: List[ScoredChunk] = []
        for hit in results:
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
                )
            )

        return scored
