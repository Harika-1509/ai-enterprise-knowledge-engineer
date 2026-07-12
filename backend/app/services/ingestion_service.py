import logging
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.document import DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.extraction.extractor_factory import ExtractorFactory

logger = logging.getLogger(__name__)


class IngestionService:
    """
    Orchestrates the extraction stage of the ingestion pipeline.
    In Step 9 (chunking) and Phase 4 (embeddings), this class will
    grow to call those stages too - this is the natural home for
    'process a document end-to-end' logic.
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
            extractor = ExtractorFactory.get_extractor(document.file_type)
            chunks = extractor.extract(Path(document.storage_path))

            if not chunks:
                raise ValueError("No extractable text found in document.")

            logger.info(
                f"Extracted {len(chunks)} chunks from document {document.id} "
                f"({document.filename})"
            )

            # Step 9 (chunking) and Phase 4 (embeddings) will plug in right here.
            # For now, we just confirm extraction succeeded.

            document.status = DocumentStatus.COMPLETED
            self.db.commit()

        except Exception as e:
            logger.exception(f"Extraction failed for document {document.id}: {e}")
            document.status = DocumentStatus.FAILED
            self.db.commit()