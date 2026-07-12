from fastapi import APIRouter, BackgroundTasks, Depends, UploadFile, File
from sqlalchemy.orm import Session

from app.api.v1.dependencies import get_current_user
from app.core.database import get_db, SessionLocal
from app.models.user import User, UserRole
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService
from app.services.ingestion_service import IngestionService

import logging

logger = logging.getLogger(__name__)

router = APIRouter()





def run_ingestion(document_id: str) -> None:
    logger.info(f"Background ingestion task STARTED for document {document_id}")
    db = SessionLocal()
    try:
        IngestionService(db).process_document(document_id)
        logger.info(f"Background ingestion task FINISHED for document {document_id}")
    except Exception:
        logger.exception(f"Background ingestion task CRASHED for document {document_id}")
    finally:
        db.close()


@router.post("/upload", response_model=DocumentResponse, status_code=201)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    document = service.upload(owner_id=current_user.id, file=file)

    background_tasks.add_task(run_ingestion, str(document.id))

    return document


@router.get("/", response_model=list[DocumentResponse])
def list_my_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    return service.list_my_documents(owner_id=current_user.id)


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = DocumentService(db)
    service.delete(
        document_id=document_id,
        owner_id=current_user.id,
        is_admin=(current_user.role == UserRole.ADMIN),
    )