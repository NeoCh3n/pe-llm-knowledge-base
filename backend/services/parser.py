from dataclasses import dataclass
from pathlib import Path
from typing import List

from backend.config import get_settings

settings = get_settings()


@dataclass
class ParsedChunk:
    content: str
    page_number: int
    chunk_index: int
    source: str
    section: str | None = None


# ---------------------------------------------------------------------------
# Structured element export — preserves real page numbers via docling provenance
# ---------------------------------------------------------------------------

def _export_elements(file_path: Path) -> List[tuple[int, str | None, str]]:
    """
    Use docling's structured document model to extract elements with their
    real page numbers.

    Returns a list of (page_number, section_header, markdown_content) tuples,
    one per logical document element (text block, heading, table, list item).

    Tables are exported as Markdown table strings and later kept as atomic
    chunks by _chunk_elements().
    """
    try:
        from docling.document_converter import DocumentConverter
    except ImportError as exc:
        raise RuntimeError(
            "docling is required for parsing documents. "
            "Install the extras in requirements.txt."
        ) from exc

    converter = DocumentConverter()
    result = converter.convert(str(file_path))
    doc = result.document

    if doc is None:
        raise RuntimeError("docling returned no document for file: %s" % file_path)

    elements: List[tuple[int, str | None, str]] = []
    current_section: str | None = None

    for item, _level in doc.iterate_items():
        # --- page number from provenance --------------------------------
        page_no: int = 1
        prov = getattr(item, "prov", None)
        if prov:
            try:
                page_no = int(prov[0].page_no)
            except (AttributeError, IndexError, TypeError, ValueError):
                page_no = 1

        # --- export element to markdown ---------------------------------
        try:
            content: str = item.export_to_markdown()
        except Exception:
            # fallback for element types that don't support markdown export
            content = str(getattr(item, "text", "") or "")

        content = content.strip()
        if not content:
            continue

        # --- track section headers for chunk metadata -------------------
        label = str(getattr(item, "label", "")).lower()
        if "section_header" in label or label in ("title",):
            current_section = content.lstrip("#").strip()

        elements.append((page_no, current_section, content))

    return elements


# ---------------------------------------------------------------------------
# Chunking — groups elements respecting max_len, keeps tables atomic
# ---------------------------------------------------------------------------


def _is_table_content(content: str) -> bool:
    """Return True if content looks like a Markdown table (starts with '|')."""
    first_line = content.lstrip().split("\n", 1)[0]
    return first_line.startswith("|")


def _chunk_elements(
    elements: List[tuple[int, str | None, str]],
    max_len: int,
    overlap: int,
) -> List[ParsedChunk]:
    """
    Group (page_number, section, content) elements into ParsedChunk objects.

    Rules:
    - Target chunk size is max_len characters.
    - Tables (detected by leading '|') are always emitted as their own chunk,
      never split or merged with adjacent text.
    - Overlap carryover is plain text; it is prepended to the next chunk's
      buffer so context is not lost at boundaries.
    - page_number is taken from the first element in each chunk.
    """
    chunks: List[ParsedChunk] = []

    buf_parts: List[str] = []
    buf_pages: List[int] = []
    buf_sections: List[str | None] = []
    current_len: int = 0

    def _flush() -> None:
        if not buf_parts:
            return
        chunks.append(
            ParsedChunk(
                content="\n\n".join(buf_parts),
                page_number=buf_pages[0],
                chunk_index=len(chunks),
                source="",  # filled in by caller
                section=next((s for s in buf_sections if s is not None), None),
            )
        )

    for page_no, section, content in elements:
        content_len = len(content)

        if _is_table_content(content):
            # Tables are atomic: flush current buffer, emit table alone.
            _flush()
            buf_parts.clear()
            buf_pages.clear()
            buf_sections.clear()
            current_len = 0

            chunks.append(
                ParsedChunk(
                    content=content,
                    page_number=page_no,
                    chunk_index=len(chunks),
                    source="",
                    section=section,
                )
            )
            continue

        if current_len + content_len > max_len and buf_parts:
            # Flush and start next buffer, optionally carrying overlap.
            prev_full = "\n\n".join(buf_parts)
            prev_page = buf_pages[-1]
            prev_section = next((s for s in reversed(buf_sections) if s is not None), None)

            _flush()
            buf_parts.clear()
            buf_pages.clear()
            buf_sections.clear()
            current_len = 0

            if overlap > 0:
                overlap_text = prev_full[-overlap:]
                buf_parts.append(overlap_text)
                buf_pages.append(prev_page)
                buf_sections.append(prev_section)
                current_len += len(overlap_text)

        buf_parts.append(content)
        buf_pages.append(page_no)
        buf_sections.append(section)
        current_len += content_len

    _flush()
    return chunks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def parse_and_chunk(file_path: str | Path) -> List[ParsedChunk]:
    """
    Parse a document and split it into RAG-friendly chunks with real page numbers.

    Uses docling's structured element iteration so that page provenance is
    preserved end-to-end. Tables are kept in single chunks. Section headers
    are tracked as metadata.

    Returns a list of ParsedChunk objects ready for vector embedding and
    SQLite storage.
    """
    path = Path(file_path)
    elements = _export_elements(path)
    chunks = _chunk_elements(
        elements,
        max_len=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
    # Back-fill source field and re-index chunk_index (chunk_index is set
    # incrementally inside _chunk_elements, but make it explicit here).
    for idx, chunk in enumerate(chunks):
        chunk.source = path.name
        chunk.chunk_index = idx

    return chunks

