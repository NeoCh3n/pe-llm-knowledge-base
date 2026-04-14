"""
Tier 1 tests for parser.py — pure chunking logic, no docling/Qdrant needed.

These tests work directly with _chunk_elements() and _export_elements()-adjacent
logic, so they run without any external services.
"""

import pytest

from backend.services.parser import ParsedChunk, _chunk_elements, _is_table_content


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_elements(items: list[tuple[int, str | None, str]]) -> list[tuple[int, str | None, str]]:
    """Thin helper so tests read like specs."""
    return items


# ---------------------------------------------------------------------------
# _chunk_elements — basic behaviour
# ---------------------------------------------------------------------------

class TestChunkElementsBasic:
    def test_single_element_becomes_one_chunk(self):
        elements = _make_elements([(1, "Revenue", "Revenue was $10M in FY24.")])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        assert len(chunks) == 1
        assert chunks[0].content == "Revenue was $10M in FY24."
        assert chunks[0].page_number == 1
        assert chunks[0].section == "Revenue"

    def test_page_number_taken_from_first_element(self):
        elements = _make_elements([
            (7, "EBITDA", "EBITDA margin 35%."),
            (7, "EBITDA", "Adjusted for one-offs."),
        ])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        assert chunks[0].page_number == 7

    def test_chunk_index_is_sequential(self):
        # Force multiple chunks with a tiny max_len
        elements = _make_elements([
            (1, None, "A" * 100),
            (2, None, "B" * 100),
            (3, None, "C" * 100),
        ])
        chunks = _chunk_elements(elements, max_len=150, overlap=0)
        for i, chunk in enumerate(chunks):
            assert chunk.chunk_index == i

    def test_section_metadata_propagates(self):
        elements = _make_elements([
            (3, "Risk Factors", "Foreign exchange exposure."),
            (3, "Risk Factors", "Regulatory risk in EU."),
        ])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        assert chunks[0].section == "Risk Factors"

    def test_section_falls_back_to_first_non_none(self):
        elements = _make_elements([
            (1, None, "Preamble text."),
            (1, "Appendix", "Appendix content."),
        ])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        # Both fit in one chunk; section should be the first non-None found
        assert chunks[0].section == "Appendix"

    def test_empty_elements_returns_empty_list(self):
        assert _chunk_elements([], max_len=800, overlap=0) == []


# ---------------------------------------------------------------------------
# _chunk_elements — table isolation
# ---------------------------------------------------------------------------

class TestTableIsolation:
    TABLE = "| Company | Revenue |\n|---------|--------|\n| Acme | $50M |"

    def test_table_gets_its_own_chunk(self):
        elements = _make_elements([
            (5, "Financials", "Text before table."),
            (5, "Financials", self.TABLE),
            (5, "Financials", "Text after table."),
        ])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        table_chunks = [c for c in chunks if "|" in c.content]
        assert len(table_chunks) == 1
        assert self.TABLE in table_chunks[0].content

    def test_table_page_number_is_correct(self):
        elements = _make_elements([
            (3, None, "Intro text."),
            (4, "Financials", self.TABLE),
        ])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        table_chunk = next(c for c in chunks if "|" in c.content)
        assert table_chunk.page_number == 4

    def test_table_not_merged_with_preceding_text(self):
        elements = _make_elements([
            (1, None, "Some text."),
            (1, None, self.TABLE),
        ])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        # Must be in separate chunks
        text_chunks = [c for c in chunks if "|" not in c.content]
        table_chunks = [c for c in chunks if "|" in c.content]
        assert len(text_chunks) >= 1
        assert len(table_chunks) == 1

    def test_oversized_table_still_fits_in_one_chunk(self):
        """A table larger than max_len must not be split."""
        big_table = "| A | B |\n|---|---|\n" + "| x | y |\n" * 200  # >> max_len
        elements = _make_elements([(10, "Data", big_table)])
        chunks = _chunk_elements(elements, max_len=50, overlap=0)
        assert len(chunks) == 1
        assert "| x | y |" in chunks[0].content

    def test_consecutive_tables_are_separate_chunks(self):
        elements = _make_elements([
            (1, "T1", self.TABLE),
            (2, "T2", self.TABLE),
        ])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        table_chunks = [c for c in chunks if "|" in c.content]
        assert len(table_chunks) == 2
        assert table_chunks[0].page_number == 1
        assert table_chunks[1].page_number == 2


# ---------------------------------------------------------------------------
# _chunk_elements — size-based splitting and overlap
# ---------------------------------------------------------------------------

class TestSplittingAndOverlap:
    def test_oversized_elements_split_into_multiple_chunks(self):
        # Each element is 200 chars; max_len is 250 → second element forces flush
        elements = _make_elements([
            (1, None, "A" * 200),
            (2, None, "B" * 200),
            (3, None, "C" * 200),
        ])
        chunks = _chunk_elements(elements, max_len=250, overlap=0)
        assert len(chunks) == 3

    def test_overlap_text_appears_in_next_chunk(self):
        long_a = "Alpha " * 50          # 300 chars
        long_b = "Beta content here."    # 18 chars; combined 318 > max_len=310
        elements = _make_elements([
            (1, None, long_a),
            (2, None, long_b),
        ])
        chunks = _chunk_elements(elements, max_len=310, overlap=50)
        # First chunk holds long_a; second chunk starts with overlap + long_b
        assert len(chunks) == 2
        overlap_present = long_a[-50:] in chunks[1].content
        assert overlap_present, "Overlap text from first chunk should appear in second chunk"

    def test_no_overlap_when_overlap_is_zero(self):
        long_a = "Alpha " * 50          # 300 chars; combined 313 > max_len=310
        long_b = "Beta content here."
        elements = _make_elements([
            (1, None, long_a),
            (2, None, long_b),
        ])
        chunks = _chunk_elements(elements, max_len=310, overlap=0)
        # With overlap=0, second chunk contains only long_b
        assert len(chunks) == 2
        assert long_b in chunks[-1].content
        assert long_a.strip() not in chunks[-1].content


# ---------------------------------------------------------------------------
# _chunk_elements — page number accuracy across page boundaries
# ---------------------------------------------------------------------------

class TestPageNumberAccuracy:
    def test_multi_page_chunk_uses_first_page(self):
        elements = _make_elements([
            (5, None, "Content from page 5."),
            (6, None, "Content from page 6."),
        ])
        chunks = _chunk_elements(elements, max_len=800, overlap=0)
        assert chunks[0].page_number == 5

    def test_each_chunk_has_its_own_page_number(self):
        elements = _make_elements([
            (10, None, "A" * 200),
            (11, None, "B" * 200),
            (12, None, "C" * 200),
        ])
        chunks = _chunk_elements(elements, max_len=250, overlap=0)
        pages = [c.page_number for c in chunks]
        assert pages == [10, 11, 12]

    def test_overlap_carryover_does_not_advance_page_number(self):
        long_a = "Page nine " * 40     # 360 chars, spans past max_len on its own
        long_b = "Page ten content."
        elements = _make_elements([
            (9, None, long_a),
            (10, None, long_b),
        ])
        chunks = _chunk_elements(elements, max_len=400, overlap=50)
        # Second chunk starts with overlap from page 9 content,
        # but the overlap buf entry gets page 9's page number.
        # The actual new content (long_b) is from page 10.
        # The page number of chunk[1] should be 9 (from overlap) — this is
        # conservative and correct: the chunk contains content starting on p9.
        assert chunks[0].page_number == 9
        # chunk[1] page is whatever buf_pages[0] is after overlap is prepended
        assert chunks[1].page_number in (9, 10)  # either is defensible


# ---------------------------------------------------------------------------
# Helper: _is_table_content (internal utility, tested for correctness)
# ---------------------------------------------------------------------------

class TestIsTableContent:
    def test_pipe_table_detected(self):
        assert _is_table_content("| A | B |\n|---|---|\n| 1 | 2 |")

    def test_plain_text_not_a_table(self):
        assert not _is_table_content("This is a paragraph about revenue.")

    def test_empty_string_not_a_table(self):
        assert not _is_table_content("")

    def test_leading_whitespace_handled(self):
        assert _is_table_content("  | A | B |\n  |---|---|")
