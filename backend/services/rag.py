from textwrap import dedent
from typing import List

from openai import OpenAI

from backend.config import get_settings
from backend.services.vector import ScoredChunk

settings = get_settings()


SYSTEM_PROMPT = dedent(
    """
    You are a financial analyst assistant. Use ONLY the provided context to answer.
    - When you reference data, always cite the Source Document and Page Number.
    - If tables are present in the context, keep them as Markdown tables in the answer.
    - If you perform calculations (e.g., CAGR, sums), show the math step-by-step using the numbers from the context.
    - If the answer cannot be found in the context, say you do not have enough information.
    """
).strip()


def _build_context(chunks: List[ScoredChunk]) -> str:
    lines: List[str] = []
    for chunk in chunks:
        header = f"Source: {chunk.filename} | Page: {chunk.page_number}"
        lines.append(f"{header}\n{chunk.content}")
    return "\n\n---\n\n".join(lines)


def generate_answer(query: str, retrieved_chunks: List[ScoredChunk]) -> dict:
    client = OpenAI(api_key=settings.llm_api_key, base_url=settings.llm_base_url)
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
    )

    answer = completion.choices[0].message.content if completion.choices else ""
    sources = [
        {
            "filename": chunk.filename,
            "page_number": chunk.page_number,
            "doc_id": chunk.document_id,
            "chunk_text": chunk.content,
        }
        for chunk in retrieved_chunks
    ]

    return {"answer": answer, "sources": sources}
