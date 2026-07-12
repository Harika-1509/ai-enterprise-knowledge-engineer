import uuid

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.storage import storage_service
from app.models.document import FileType
from app.repositories.document_repository import DocumentRepository


class DocumentService:
    def __init__(self, db: Session):
        self.repo = DocumentRepository(db)

    def upload(self, owner_id: uuid.UUID, file: UploadFile):
        storage_path, extension = storage_service.save_file(file)
        document = self.repo.create(
            owner_id=owner_id,
            filename=file.filename,
            file_type=FileType(extension),
            storage_path=storage_path,
        )
        return document

    def list_my_documents(self, owner_id: uuid.UUID):
        return self.repo.list_by_owner(owner_id)

    def delete(self, document_id: str, owner_id: uuid.UUID, is_admin: bool):
        document = self.repo.get_by_id(document_id)
        if not document:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found.")

        # Ownership check: only the uploader or an admin can delete
        if document.owner_id != owner_id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to delete this document.",
            )

        storage_service.get_full_path(document.storage_path).unlink(missing_ok=True)
        self.repo.delete(document)