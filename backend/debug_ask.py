"""
Full diagnostic script for the OCR-model retrieval gap.
Run with: python debug_ask.py
"""

from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.embedding.embedding_service import embedding_service
from app.services.vectorstore.qdrant_service import qdrant_service
from app.services.query.query_rewriter_service import query_rewriter_service
from app.services.search_service import search_service

# ---- CONFIG: adjust this email to match the user you've been testing with ----
TEST_USER_EMAIL = "user@example.com"

FAILING_QUERY = "What OCR model is used in the system?"
DIRECT_QUERY = "PaddleOCR"

db = SessionLocal()
user = UserRepository(db).get_by_email(TEST_USER_EMAIL)

if not user:
    print(f"!! No user found with email {TEST_USER_EMAIL} - fix TEST_USER_EMAIL and rerun.")
    exit(1)

print(f"Testing as user: {user.email} ({user.id})\n")

# =========================================================================
# 1. Check for duplicate/near-duplicate documents
# =========================================================================
print("=" * 70)
print("1. DOCUMENT LIST FOR THIS USER")
print("=" * 70)

from app.repositories.document_repository import DocumentRepository

docs = DocumentRepository(db).list_by_owner(user.id)
for d in docs:
    print(f"  - {d.filename} | status={d.status.value} | id={d.id}")

# =========================================================================
# 2. Query rewriter output
# =========================================================================
print("\n" + "=" * 70)
print("2. QUERY REWRITER OUTPUT")
print("=" * 70)

rewritten = query_rewriter_service.rewrite(FAILING_QUERY)
print(f"Original : {FAILING_QUERY}")
print(f"Rewritten: {rewritten}")

# =========================================================================
# 3. Raw dense search (wide, no rerank/compression) for the failing query
# =========================================================================
print("\n" + "=" * 70)
print("3. RAW DENSE SEARCH (top 20, failing query) - is PaddleOCR chunk in here at all?")
print("=" * 70)

from qdrant_client.http.models import FieldCondition, Filter, MatchValue

access_filter = Filter(
    must=[FieldCondition(key="owner_id", match=MatchValue(value=str(user.id)))]
)

dense_vec = embedding_service.embed_query(FAILING_QUERY)
raw_dense = qdrant_service.search_dense(
    query_vector=dense_vec, limit=20, query_filter=access_filter
)

found_at_rank = None
for rank, point in enumerate(raw_dense, start=1):
    content_preview = point.payload.get("content", "")[:60].replace("\n", " ")
    is_paddle = "PaddleOCR" in point.payload.get("content", "")
    marker = "  <-- PaddleOCR chunk!" if is_paddle else ""
    print(f"  #{rank:2d}  score={point.score:.4f}  {content_preview}{marker}")
    if is_paddle and found_at_rank is None:
        found_at_rank = rank

if found_at_rank:
    print(f"\n  RESULT: PaddleOCR chunk found at dense rank #{found_at_rank}")
else:
    print(f"\n  RESULT: PaddleOCR chunk NOT in top 20 dense results at all.")

# =========================================================================
# 4. Raw sparse (BM25) search for the failing query
# =========================================================================
print("\n" + "=" * 70)
print("4. RAW SPARSE (BM25) SEARCH (top 20, failing query)")
print("=" * 70)

from qdrant_client.http.models import SparseVector

sparse_raw = embedding_service.embed_sparse_query(FAILING_QUERY)
sparse_vector = SparseVector(
    indices=sparse_raw.indices.tolist(), values=sparse_raw.values.tolist()
)
raw_sparse = qdrant_service.search_sparse(
    sparse_vector=sparse_vector, limit=20, query_filter=access_filter
)

found_at_rank_sparse = None
for rank, point in enumerate(raw_sparse, start=1):
    content_preview = point.payload.get("content", "")[:60].replace("\n", " ")
    is_paddle = "PaddleOCR" in point.payload.get("content", "")
    marker = "  <-- PaddleOCR chunk!" if is_paddle else ""
    print(f"  #{rank:2d}  score={point.score:.4f}  {content_preview}{marker}")
    if is_paddle and found_at_rank_sparse is None:
        found_at_rank_sparse = rank

if found_at_rank_sparse:
    print(f"\n  RESULT: PaddleOCR chunk found at sparse rank #{found_at_rank_sparse}")
else:
    print(f"\n  RESULT: PaddleOCR chunk NOT in top 20 sparse results at all.")

# =========================================================================
# 5. Direct query for "PaddleOCR" - sanity check it's retrievable at all
# =========================================================================
print("\n" + "=" * 70)
print("5. DIRECT QUERY: 'PaddleOCR' (sanity check)")
print("=" * 70)

direct_results = search_service.search(DIRECT_QUERY, limit=5, current_user=user)
for i, r in enumerate(direct_results, 1):
    print(f"  [{i}] ({r.filename}) score={r.score:.4f}")
    print(f"      {r.content[:100]}")

# =========================================================================
# 6. Full pipeline - before and after compression - for the failing query
# =========================================================================
print("\n" + "=" * 70)
print("6. FULL PIPELINE: BEFORE vs AFTER COMPRESSION (failing query)")
print("=" * 70)

plain = search_service.search(FAILING_QUERY, limit=5, current_user=user)
compressed = search_service.search_for_llm_context(FAILING_QUERY, limit=5, current_user=user)

print("\n--- BEFORE COMPRESSION ---")
for i, s in enumerate(plain, 1):
    print(f"\n[{i}] ({s.filename}) score={s.score:.4f}")
    print(s.content[:300])

print("\n--- AFTER COMPRESSION ---")
for i, s in enumerate(compressed, 1):
    print(f"\n[{i}] ({s.filename})")
    print(s.content[:300])

db.close()

print("\n" + "=" * 70)
print("DIAGNOSTIC COMPLETE")
print("=" * 70)