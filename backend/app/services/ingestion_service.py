import hashlib
import logging
from pathlib import Path

from qdrant_client.http.models import PointStruct
from sqlalchemy.orm import Session

from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.chunking.text_chunker import text_chunker
from app.services.embedding.embedding_service import embedding_service
from app.services.extraction.extractor_factory import ExtractorFactory
from app.services.vectorstore.qdrant_service import qdrant_service

logger = logging.getLogger(__name__)


def _deterministic_point_id(document_id: str, chunk_index: int) -> str:
    """
    Generates a stable, repeatable point ID from document_id + chunk_index.
    Using a UUID5 (hash-based) instead of UUID4 (random) means re-processing
    the same document produces the SAME point IDs, so re-ingestion cleanly
    overwrites old vectors via upsert instead of creating duplicates.
    """
    namespace = hashlib.md5(document_id.encode()).hexdigest()
    seed = f"{namespace}-{chunk_index}"
    return hashlib.md5(seed.encode()).hexdigest()


class IngestionService:
    """
    Orchestrates the full ingestion pipeline: extraction -> chunking ->
    embedding -> vector storage. This is the single place where all four
    prior steps (8, 9, 14, 15) come together.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = DocumentRepository(db)

    def process_document(self, document_id: str) -> None:
        document = self.repo.get_by_id(document_id)
        if not document:
            logger.error(f"Document {document_id} not found for processing.")
            return

        document.status = DocumentStatus.PROCESSING
        self.db.commit()

        try:
            # Stage 1: Extraction (Step 8)
            extractor = ExtractorFactory.get_extractor(document.file_type)
            extracted_chunks = extractor.extract(Path(document.storage_path))

            if not extracted_chunks:
                raise ValueError("No extractable text found in document.")

            logger.info(
                f"Extracted {len(extracted_chunks)} raw segments from "
                f"document {document.id} ({document.filename})"
            )

            # Stage 2: Chunking (Step 9)
            all_text_chunks = []
            for extracted_chunk in extracted_chunks:
                all_text_chunks.extend(text_chunker.split(extracted_chunk))

            if not all_text_chunks:
                raise ValueError("Chunking produced no usable text chunks.")

            logger.info(
                f"Chunked into {len(all_text_chunks)} final chunks for "
                f"document {document.id}"
            )

            # Stage 3: Embedding (Step 14) - batched, not one-by-one
            texts = [chunk.content for chunk in all_text_chunks]
            vectors = embedding_service.embed_documents(texts)

            logger.info(f"Embedded {len(vectors)} chunks for document {document.id}")

            # Stage 4: Build payloads and store in Qdrant (Step 15)
            points = []
            for chunk, vector in zip(all_text_chunks, vectors):
                payload = {
                    "document_id": str(document.id),
                    "owner_id": str(document.owner_id),
                    "filename": document.filename,
                    "file_type": document.file_type.value,
                    "chunk_index": chunk.chunk_index,
                    "token_count": chunk.token_count,
                    "content": chunk.content,
                    **chunk.metadata,  # page_number / slide_number / sheet_name / etc.
                }
                points.append(
                    PointStruct(
                        id=_deterministic_point_id(str(document.id), chunk.chunk_index),
                        vector=vector,
                        payload=payload,
                    )
                )

            qdrant_service.upsert_points(points)
            logger.info(
                f"Stored {len(points)} vectors in Qdrant for document {document.id}"
            )

            document.status = DocumentStatus.COMPLETED
            self.db.commit()

        except Exception as e:
            logger.exception(f"Processing failed for document {document.id}: {e}")
            document.status = DocumentStatus.FAILED
            self.db.commit()