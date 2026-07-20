"""
Unit tests for citation parsing (Step 23). Pure regex/parsing logic.
"""

from app.schemas.search import SearchResult
from app.services.generation.citation_parser import parse_citations


def _make_source(filename: str, content: str = "some content") -> SearchResult:
    return SearchResult(
        document_id="00000000-0000-0000-0000-000000000001",
        filename=filename,
        content=content,
        score=0.5,
        chunk_index=0,
    )


def test_single_citation_is_parsed_correctly():
    sources = [_make_source("doc1.pdf")]
    answer = "The stipend is 30K [Source 1]."

    citations = parse_citations(answer, sources)

    assert len(citations) == 1
    assert citations[0].source_number == 1
    assert citations[0].filename == "doc1.pdf"


def test_multiple_citations_in_one_marker():
    sources = [_make_source("doc1.pdf"), _make_source("doc2.pdf")]
    answer = "Both sources agree [Source 1, 2]."

    citations = parse_citations(answer, sources)

    assert len(citations) == 2
    assert {c.source_number for c in citations} == {1, 2}


def test_and_phrasing_is_handled():
    sources = [_make_source("doc1.pdf"), _make_source("doc2.pdf")]
    answer = "Confirmed by [Sources 1 and 2]."

    citations = parse_citations(answer, sources)

    assert len(citations) == 2


def test_out_of_range_citation_number_is_skipped_not_crashed():
    sources = [_make_source("doc1.pdf")]
    answer = "This claims [Source 5] which does not exist."

    citations = parse_citations(answer, sources)

    assert citations == []  # gracefully skipped, no exception raised


def test_no_citation_markers_produces_empty_list():
    sources = [_make_source("doc1.pdf")]
    answer = "This is a refusal with no sources cited."

    citations = parse_citations(answer, sources)

    assert citations == []


def test_duplicate_citation_numbers_are_deduplicated():
    sources = [_make_source("doc1.pdf")]
    answer = "First mention [Source 1]. Second mention [Source 1] again."

    citations = parse_citations(answer, sources)

    assert len(citations) == 1