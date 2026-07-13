import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.chunking.text_chunker import text_chunker
from app.services.extraction.extractor_factory import ExtractorFactory

logger = logging.getLogger(__name__)


class IngestionService:
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
            extractor = ExtractorFactory.get_extractor(document.file_type)
            extracted_chunks = extractor.extract(Path(document.storage_path))

            if not extracted_chunks:
                raise ValueError("No extractable text found in document.")

            logger.info(
                f"Extracted {len(extracted_chunks)} raw segments from document "
                f"{document.id} ({document.filename})"
            )

            all_text_chunks = []
            for extracted_chunk in extracted_chunks:
                all_text_chunks.extend(text_chunker.split(extracted_chunk))

            logger.info(
                f"Chunked into {len(all_text_chunks)} final chunks "
                f"(avg {sum(c.token_count for c in all_text_chunks) // len(all_text_chunks)} "
                f"tokens/chunk) for document {document.id}"
            )

            # Phase 4 (embeddings + Qdrant storage) plugs in right here,
            # operating on `all_text_chunks`.

            document.status = DocumentStatus.COMPLETED
            self.db.commit()

        except Exception as e:
            logger.exception(f"Processing failed for document {document.id}: {e}")
            document.status = DocumentStatus.FAILED
            self.db.commit()