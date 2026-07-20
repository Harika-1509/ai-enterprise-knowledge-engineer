"""
Unit tests for TextChunker (Step 9). Pure logic - no I/O, no network,
no database - runs in milliseconds and requires no live services.
"""

from app.services.chunking.text_chunker import TextChunker
from app.services.extraction.base_extractor import ExtractedChunk


def test_short_text_produces_single_chunk():
    chunker = TextChunker(max_tokens=500, overlap_tokens=50)
    extracted = ExtractedChunk(content="This is a short sentence.", metadata={})

    result = chunker.split(extracted)

    assert len(result) == 1
    assert result[0].content == "This is a short sentence."


def test_long_text_respects_max_token_limit():
    chunker = TextChunker(max_tokens=50, overlap_tokens=10)
    long_text = "This is a sentence that will be repeated many times. " * 50
    extracted = ExtractedChunk(content=long_text, metadata={})

    result = chunker.split(extracted)

    assert len(result) > 1
    for chunk in result:
        assert chunk.token_count <= 50, f"Chunk exceeded max_tokens: {chunk.token_count}"


def test_metadata_is_preserved_across_all_chunks():
    chunker = TextChunker(max_tokens=20, overlap_tokens=5)
    long_text = "Sentence number one here. " * 20
    extracted = ExtractedChunk(
        content=long_text, metadata={"page_number": 4, "source_type": "pdf"}
    )

    result = chunker.split(extracted)

    assert len(result) > 1  # confirm this test actually exercises multi-chunk behavior
    for chunk in result:
        assert chunk.metadata["page_number"] == 4
        assert chunk.metadata["source_type"] == "pdf"


def test_empty_content_produces_no_chunks():
    chunker = TextChunker()
    extracted = ExtractedChunk(content="", metadata={})

    result = chunker.split(extracted)

    assert result == []


def test_chunk_indices_are_sequential_within_a_single_split_call():
    chunker = TextChunker(max_tokens=20, overlap_tokens=5)
    long_text = "Sentence number one here. " * 20
    extracted = ExtractedChunk(content=long_text, metadata={})

    result = chunker.split(extracted)

    indices = [c.chunk_index for c in result]
    assert indices == list(range(len(result)))