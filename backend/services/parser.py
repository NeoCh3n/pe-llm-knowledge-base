from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from backend.config import get_settings

settings = get_settings()


@dataclass
class ParsedChunk:
    content: str
    page_number: int
    chunk_index: int
    source: str


def _export_markdown(file_path: Path) -> str:
    """
    Use docling to convert the document to Markdown.
    Tables stay intact because docling preserves Markdown table structures.
    """
    try:
        from docling.document_converter import DocumentConverter
    except Exception as exc:
        raise RuntimeError(
            "docling is required for parsing documents. Install the extras in requirements.txt."
        ) from exc

    converter = DocumentConverter()
    result = converter.convert(str(file_path))

    if hasattr(result, "document") and result.document is not None:
        return result.document.export_to_markdown()

    raise RuntimeError("Failed to export document to Markdown via docling")


def _split_blocks(markdown_text: str) -> List[str]:
    """
    Split markdown into logical blocks without breaking tables.
    Tables are detected by the pipe/--- pattern and kept together.
    """
    blocks: List[str] = []
    current: List[str] = []
    in_table = False

    for line in markdown_text.splitlines():
        stripped = line.strip()
        is_table_line = "|" in stripped and "---" in stripped or stripped.startswith("|")

        if stripped.startswith("# "):
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            current.append(line)
            in_table = False
            continue

        if is_table_line:
            in_table = True
            current.append(line)
            continue

        if stripped == "" and not in_table:
            if current:
                blocks.append("\n".join(current).strip())
                current = []
            continue

        if stripped == "" and in_table:
            current.append(line)
            continue

        current.append(line)
        if in_table and not is_table_line:
            in_table = False

    if current:
        blocks.append("\n".join(current).strip())

    return [b for b in blocks if b]


def _chunk_blocks(blocks: Iterable[str]) -> List[str]:
    chunks: List[str] = []
    buffer: List[str] = []
    current_len = 0
    max_len = settings.chunk_size
    overlap = settings.chunk_overlap

    for block in blocks:
        block_len = len(block)

        if current_len + block_len <= max_len:
            buffer.append(block)
            current_len += block_len
            continue

        if buffer:
            chunks.append("\n\n".join(buffer))
            # start next chunk with overlap for continuity
            overlap_text = ("\n\n".join(buffer))[-overlap:] if overlap > 0 else ""
            buffer = [overlap_text, block] if overlap_text else [block]
            current_len = sum(len(part) for part in buffer)
        else:
            # extremely large block (e.g., huge table) - force add
            chunks.append(block)
            current_len = 0
            buffer = []

    if buffer:
        chunks.append("\n\n".join(buffer))

    return chunks


def parse_and_chunk(file_path: str | Path) -> List[ParsedChunk]:
    """
    Parse a document into Markdown and split into RAG-friendly chunks.

    Markdown export preserves tables; chunking keeps tables intact and
    maintains some overlap to reduce context loss.
    """
    path = Path(file_path)
    markdown_text = _export_markdown(path)
    blocks = _split_blocks(markdown_text)
    chunk_bodies = _chunk_blocks(blocks)

    parsed_chunks: List[ParsedChunk] = []
    for idx, chunk in enumerate(chunk_bodies):
        parsed_chunks.append(
            ParsedChunk(
                content=chunk,
                page_number=1,  # docling markdown currently does not expose per-page numbers
                chunk_index=idx,
                source=str(path.name),
            )
        )

    return parsed_chunks
