from app.core.database import SessionLocal
from app.services.ingestion_service import IngestionService
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository

db = SessionLocal()
user = UserRepository(db).get_by_email("user@example.com")
docs = DocumentRepository(db).list_by_owner(user.id)

for doc in docs:
    if doc.filename == "miniproject_final_doc.docx":
        print(f"Reprocessing {doc.filename}...")
        IngestionService(db).process_document(str(doc.id))

db.close()
print("Done.")