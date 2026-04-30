from textwrap import dedent
from typing import List
import logging

from openai import OpenAI

from backend.config import get_settings
from backend.services.vector import ScoredChunk

logger = logging.getLogger(__name__)
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


def _build_context(chunks: List[ScoredChunk], max_tokens: int = 4000) -> str:
    """Build context from chunks, limiting total size to avoid exceeding context window."""
    lines: List[str] = []
    total_chars = 0
    # Approximate tokens: 1 token ≈ 4 characters for English text
    max_chars = max_tokens * 4

    for chunk in chunks:
        header = f"Source: {chunk.filename} | Page: {chunk.page_number}"
        chunk_text = f"{header}\n{chunk.content}"
        chunk_chars = len(chunk_text)

        if total_chars + chunk_chars > max_chars and lines:
            # Skip this chunk if it would exceed the limit (but keep at least one)
            logger.info(f"Context limit reached: {total_chars} chars, skipping remaining chunks")
            break

        lines.append(chunk_text)
        total_chars += chunk_chars

    return "\n\n---\n\n".join(lines)


def generate_answer(query: str, retrieved_chunks: List[ScoredChunk]) -> dict:
    # For LM Studio (local server), api_key can be dummy value if not set
    api_key = settings.llm_api_key if settings.llm_api_key else "not-needed"
    client = OpenAI(api_key=api_key, base_url=settings.llm_base_url)
    context = _build_context(retrieved_chunks)

    # LM Studio often ignores the model name and uses the loaded model
    # Use "local-model" or the configured model name
    model_name = settings.llm_model
    if "127.0.0.1" in settings.llm_base_url or "localhost" in settings.llm_base_url:
        # Try common LM Studio model names
        model_name = "local-model"  # LM Studio default

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {
            "role": "user",
            "content": f"User question: {query}\n\nContext:\n{context}",
        },
    ]

    logger.info(f"Sending request to LLM: base_url={settings.llm_base_url}, model={model_name}")

    completion = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=0,
        max_tokens=500,
    )

    logger.info(f"LLM raw response: choices={len(completion.choices) if completion.choices else 0}")
    if completion.choices:
        msg = completion.choices[0].message
        logger.info(f"Message content: {bool(msg.content)}, reasoning: {hasattr(msg, 'reasoning_content')}")

    # Handle empty content (LM Studio may return reasoning_content only)
    message = completion.choices[0].message if completion.choices else None
    answer = message.content if message and message.content else ""
    # If still empty, try reasoning_content as fallback
    if not answer and message:
        answer = getattr(message, "reasoning_content", "")[:500]

    logger.info(f"LLM processed: answer_length={len(answer)}, has_choices={bool(completion.choices)}")

    if not answer:
        # Return a helpful message instead of raising error
        answer = (
            f"⚠️ **LLM returned empty response**\n\n"
            f"The LLM service at `{settings.llm_base_url}` did not generate an answer. "
            f"This usually means:\n\n"
            f"1. **LM Studio**: Make sure a model is loaded and the server is running\n"
            f"2. **Model name mismatch**: Try using 'local-model' as the model name\n"
            f"3. **Context too long**: The retrieved context may exceed the model's context window\n\n"
            f"**Current config**: Model=`{settings.llm_model}`, Base URL=`{settings.llm_base_url}`\n\n"
            f"The sources below were retrieved but no answer was generated."
        )
        logger.warning(f"LLM empty response: model={settings.llm_model}, url={settings.llm_base_url}")

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
