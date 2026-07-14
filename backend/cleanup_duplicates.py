# cleanup_duplicates.py
from app.core.database import SessionLocal
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.services.document_service import DocumentService

db = SessionLocal()
user = UserRepository(db).get_by_email("user@example.com")
docs = DocumentRepository(db).list_by_owner(user.id)

seen_filenames = set()
service = DocumentService(db)

for doc in docs:
    if doc.filename in seen_filenames or doc.status.value == "failed":
        print(f"Deleting duplicate/failed: {doc.filename} ({doc.id})")
        service.delete(str(doc.id), owner_id=user.id, is_admin=True)
    else:
        seen_filenames.add(doc.filename)

db.close()
print("Cleanup complete.")