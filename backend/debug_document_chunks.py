from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.vectorstore.qdrant_service import qdrant_service

db = SessionLocal()
user = UserRepository(db).get_by_email("user@example.com")  # adjust if needed

document_id = "4d235715-6dcc-4528-a218-7cba49acb095"  # from your response

# Scroll through ALL points for this specific document
points, _ = qdrant_service.client.scroll(
    collection_name="documents",
    scroll_filter={
        "must": [
            {"key": "document_id", "match": {"value": document_id}}
        ]
    },
    limit=100,
)

print(f"Total chunks stored for this document: {len(points)}\n")
for i, p in enumerate(points, 1):
    content = p.payload.get("content", "")
    print(f"[{i}] {content[:150]}")
    print()

db.close()