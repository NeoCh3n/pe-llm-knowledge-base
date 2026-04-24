from textwrap import dedent
from typing import List

from openai import OpenAI

from backend.config import get_settings
from backend.services.vector import ScoredChunk

settings = get_settings()
PROMPT_VERSION = "pe_ic_copilot_v1"


SYSTEM_PROMPT = dedent(
    """
    You are a private equity research and IC copilot. Use ONLY the provided context to answer.
    - Treat the task as evidence-grounded decision support, not autonomous decision-making.
    - When you reference data, always cite the Source Document and Page Number.
    - If tables are present in the context, keep them as Markdown tables in the answer.
    - If you perform calculations (e.g., CAGR, sums, ratios), show the math step-by-step using only numbers from the context.
    - If evidence is insufficient or conflicting, say so explicitly and point to the closest available evidence.
    - Do not provide investment advice, final approval language, or unsupported conclusions.
    """
).strip()


def _build_context(chunks: List[ScoredChunk]) -> str:
    lines: List[str] = []
    for chunk in chunks:
        header = f"Source: {chunk.filename} | Page: {chunk.page_number}"
        lines.append(f"{header}\n{chunk.content}")
    return "\n\n---\n\n".join(lines)


def generate_answer(query: str, retrieved_chunks: List[ScoredChunk]) -> dict:
    # For LM Studio (local server), api_key can be dummy value if not set
    api_key = settings.llm_api_key if settings.llm_api_key else "not-needed"
    client = OpenAI(api_key=api_key, base_url=settings.llm_base_url)
    context = _build_context(retrieved_chunks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"User question: {query}\n\nContext:\n{context}",
        },
    ]

    completion = client.chat.completions.create(
        model=settings.llm_model,
        messages=messages,
        temperature=0,
        max_tokens=500,
    )

    # Handle empty content (LM Studio may return reasoning_content only)
    message = completion.choices[0].message if completion.choices else None
    answer = message.content if message and message.content else ""
    # If still empty, try reasoning_content as fallback
    if not answer and message:
        answer = getattr(message, "reasoning_content", "")[:500]
    sources = [
        {
            "filename": chunk.filename,
            "page_number": chunk.page_number,
            "doc_id": chunk.document_id,
            "chunk_text": chunk.content,
            "category": chunk.category,
            "deal_outcome": chunk.deal_outcome,
            "chunk_index": chunk.chunk_index,
        }
        for chunk in retrieved_chunks
    ]

    return {
        "answer": answer,
        "sources": sources,
        "prompt_version": PROMPT_VERSION,
        "model_name": settings.llm_model,
    }
