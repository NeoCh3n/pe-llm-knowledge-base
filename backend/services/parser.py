from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple

from backend.config import get_settings

settings = get_settings()


@dataclass
class ParsedChunk:
    content: str
    page_number: int
    chunk_index: int
    source: str
    section: str | None = None


@dataclass
class ParsedTable:
    """Represents an extracted table from a document."""
    content: str
    page_number: int
    table_type: str | None = None  # e.g., "financial", "cap_table", "other"


class ParseResult:
    """Result of parsing a document, including chunks and tables."""
    def __init__(self):
        self.chunks: List[ParsedChunk] = []
        self.tables: List[ParsedTable] = []


# ---------------------------------------------------------------------------
# Structured element export — preserves real page numbers via docling provenance
# ---------------------------------------------------------------------------

def _export_elements(file_path: Path) -> Tuple[List[Tuple[int, str | None, str]], List[ParsedTable]]:
    """
    Use docling's structured document model to extract elements with their
    real page numbers.

    Returns:
        - List of (page_number, section_header, markdown_content) tuples
        - List of ParsedTable objects for extracted tables
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

    elements: List[Tuple[int, str | None, str]] = []
    tables: List[ParsedTable] = []
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

        # --- detect and extract tables ------------------------------------
        if _is_table_content(content):
            # Infer table type from content/section
            table_type = _infer_table_type(content, current_section)
            tables.append(ParsedTable(
                content=content,
                page_number=page_no,
                table_type=table_type
            ))

        elements.append((page_no, current_section, content))

    return elements, tables


# ---------------------------------------------------------------------------
# Chunking — groups elements respecting max_len, keeps tables atomic
# ---------------------------------------------------------------------------


def _is_table_content(content: str) -> bool:
    """Return True if content looks like a Markdown table (starts with '|')."""
    first_line = content.lstrip().split("\n", 1)[0]
    return first_line.startswith("|")


def _infer_table_type(content: str, section: str | None) -> str | None:
    """Infer the type of table from its content and section context."""
    content_lower = content.lower()
    section_lower = (section or "").lower()

    # Financial tables
    financial_keywords = ['revenue', 'ebitda', 'profit', 'loss', 'income', 'balance', 'cash flow',
                         'financial', 'million', 'billion', '$', '%', 'margin', 'cagr', 'growth']
    if any(kw in content_lower for kw in financial_keywords):
        return 'financial'

    # Cap table / ownership
    cap_keywords = ['shareholder', 'ownership', 'shares', 'equity', 'cap table', 'founder',
                   'investor', 'stake', 'percentage', 'voting']
    if any(kw in content_lower for kw in cap_keywords):
        return 'cap_table'

    # Team / people
    team_keywords = ['founder', 'ceo', 'cto', 'cfo', 'executive', 'team', 'management',
                    'director', 'vp', 'head of']
    if any(kw in content_lower for kw in team_keywords):
        return 'team'

    # Market / competitive
    market_keywords = ['market', 'competitor', 'competitive', 'landscape', 'comparison',
                      'benchmark', 'peer', 'industry']
    if any(kw in content_lower for kw in market_keywords):
        return 'market'

    # Check section context
    if section:
        if any(kw in section_lower for kw in ['financial', 'revenue', 'ebitda', 'profit']):
            return 'financial'
        if any(kw in section_lower for kw in ['cap table', 'ownership', 'shareholder']):
            return 'cap_table'
        if any(kw in section_lower for kw in ['team', 'management', 'founder']):
            return 'team'

    return 'other'


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

def parse_and_chunk(file_path: str | Path) -> ParseResult:
    """
    Parse a document and split it into RAG-friendly chunks with real page numbers.

    Uses docling's structured element iteration so that page provenance is
    preserved end-to-end. Tables are kept in single chunks and also extracted
    separately for analytics. Section headers are tracked as metadata.

    Returns a ParseResult containing chunks and extracted tables.
    """
    path = Path(file_path)
    elements, tables = _export_elements(path)
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

    result = ParseResult()
    result.chunks = chunks
    result.tables = tables
    return result

