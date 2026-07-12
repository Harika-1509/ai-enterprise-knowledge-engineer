import uuid

from sqlalchemy.orm import Session

from app.models.document import Document, DocumentStatus, FileType


class DocumentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(
        self, owner_id: uuid.UUID, filename: str, file_type: FileType, storage_path: str
    ) -> Document:
        document = Document(
            owner_id=owner_id,
            filename=filename,
            file_type=file_type,
            storage_path=storage_path,
            status=DocumentStatus.PENDING,
        )
        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_by_id(self, document_id: str) -> Document | None:
        return self.db.query(Document).filter(Document.id == document_id).first()

    def list_by_owner(self, owner_id: uuid.UUID) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.owner_id == owner_id)
            .order_by(Document.created_at.desc())
            .all()
        )

    def delete(self, document: Document) -> None:
        self.db.delete(document)
        self.db.commit()