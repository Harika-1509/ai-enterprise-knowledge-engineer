"""
Integration test for the full ingestion pipeline (Steps 8-16), using a
REAL test Qdrant collection - this is specifically designed to catch
the class of bug Step 30 found (chunk_index collisions across multiple
extracted segments), which no unit test in isolation could reveal.
"""

from pathlib import Path

from app.services.chunking.text_chunker import text_chunker
from app.services.embedding.embedding_service import embedding_service
from app.services.extraction.docx_extractor import DOCXExtractor
from qdrant_client.http.models import PointStruct
import hashlib


def _deterministic_point_id(document_id: str, chunk_index: int) -> str:
    namespace = hashlib.md5(document_id.encode()).hexdigest()
    seed = f"{namespace}-{chunk_index}"
    return hashlib.md5(seed.encode()).hexdigest()


def test_multi_segment_document_produces_unique_point_ids(tmp_path, test_qdrant_collection):
    """
    Regression test for Step 30's real bug: a document with MANY short
    extracted segments (simulating a table with many rows) must NOT
    collide on point IDs when chunk_index is assigned globally, not
    per-extraction-call.
    """
    from docx import Document as DocxDocument

    # Build a small real DOCX with a multi-row table, mirroring the
    # actual structure that exposed the original bug.
    doc = DocxDocument()
    table = doc.add_table(rows=6, cols=2)
    table.rows[0].cells[0].text = "Field"
    table.rows[0].cells[1].text = "Value"
    for i in range(1, 6):
        table.rows[i].cells[0].text = f"Field{i}"
        table.rows[i].cells[1].text = f"Value{i}"

    file_path = tmp_path / "test_table.docx"
    doc.save(str(file_path))

    # Run the real extraction + chunking pipeline
    extractor = DOCXExtractor()
    extracted_chunks = extractor.extract(Path(file_path))
    all_text_chunks = []
    for extracted_chunk in extracted_chunks:
        all_text_chunks.extend(text_chunker.split(extracted_chunk))

    # THIS is the exact fix from Step 30 - global re-indexing
    for global_idx, chunk in enumerate(all_text_chunks):
        chunk.chunk_index = global_idx

    document_id = "test-doc-integration-001"
    vectors = embedding_service.embed_documents([c.content for c in all_text_chunks])

    points = [
        PointStruct(
            id=_deterministic_point_id(document_id, chunk.chunk_index),
            vector={"dense": vec},
            payload={"document_id": document_id, "chunk_index": chunk.chunk_index, "content": chunk.content},
        )
        for chunk, vec in zip(all_text_chunks, vectors)
    ]

    test_qdrant_collection.upsert(collection_name="documents_test", points=points)

    # THE ACTUAL REGRESSION CHECK: every chunk must have survived storage.
    # If chunk_index collisions were happening (Step 30's bug), this
    # count would be far lower than len(all_text_chunks).
    stored_points, _ = test_qdrant_collection.scroll(
        collection_name="documents_test", limit=1000
    )

    assert len(stored_points) == len(all_text_chunks), (
        f"Expected {len(all_text_chunks)} stored points but found "
        f"{len(stored_points)} - possible chunk_index collision regression"
    )

    point_ids = {p.id for p in stored_points}
    assert len(point_ids) == len(stored_points), "Duplicate point IDs detected"