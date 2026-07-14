"""
End-to-end pipeline validation for Phase 5.
Run with: python test_e2e_pipeline.py

Requires: a running Postgres/Redis/Qdrant (docker compose up), and at
least one registered test user with documents already uploaded and
processed (status=completed).
"""

from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.repositories.document_repository import DocumentRepository
from app.services.search_service import search_service
from app.services.generation.answer_service import answer_service

TEST_USER_EMAIL = "user@example.com"

results = []


def check(label: str, condition: bool, detail: str = ""):
    status = "PASS" if condition else "FAIL"
    results.append((label, status, detail))
    print(f"[{status}] {label}" + (f" - {detail}" if detail and not condition else ""))


db = SessionLocal()
user = UserRepository(db).get_by_email(TEST_USER_EMAIL)

if not user:
    print(f"No user found: {TEST_USER_EMAIL}")
    exit(1)

docs = DocumentRepository(db).list_by_owner(user.id)
completed_docs = [d for d in docs if d.status.value == "completed"]

check("At least one document successfully ingested", len(completed_docs) > 0,
      f"found {len(completed_docs)} completed documents")

# ---- Test 1: Plain search returns results for a relevant query ----
plain_results = search_service.search("OCR model", limit=5, current_user=user)
check("Plain search returns results for relevant query", len(plain_results) > 0)

# ---- Test 2: Search respects access control (empty for unrelated user) ----
# (Requires a second, document-less test user - skip if not present)
other_user = UserRepository(db).get_by_email("second_user@example.com")
if other_user:
    other_results = search_service.search("OCR model", limit=5, current_user=other_user)
    check("Access control: other user gets no results from first user's docs",
          len(other_results) == 0, f"got {len(other_results)} results")
else:
    print("[SKIP] Access control test - no second_user@example.com found")

# ---- Test 3: Full ask pipeline produces a grounded, cited answer ----
response = answer_service.ask("What OCR model is used in the system?", limit=5, current_user=user)
check("Ask pipeline returns non-empty answer", len(response.answer.strip()) > 0)
check("Ask pipeline returns at least one citation for an answerable question",
      len(response.citations) > 0,
      f"answer was: {response.answer[:150]}")

# ---- Test 4: Guardrail - refuses to answer unrelated/unknown questions ----
refusal_response = answer_service.ask("What is the capital of France?", limit=5, current_user=user)
refusal_phrases = ["don't have enough information", "cannot answer", "no information"]
is_refusal = any(p in refusal_response.answer.lower() for p in refusal_phrases)
check("Guardrail: refuses to answer from outside knowledge", is_refusal,
      f"answer was: {refusal_response.answer[:150]}")

# ---- Test 5: Citations map to real documents ----
if response.citations:
    valid_doc_ids = {str(d.id) for d in completed_docs}
    all_valid = all(str(c.document_id) in valid_doc_ids for c in response.citations)
    check("All citations reference real, owned documents", all_valid)

# ---- Test 6: Empty-knowledge-base user handled gracefully ----
# (Only meaningful if other_user exists and has no docs)
if other_user:
    empty_response = answer_service.ask("anything at all", limit=5, current_user=other_user)
    check("Empty knowledge base handled without crashing", True)  # if we got here, no exception
    check("Empty knowledge base produces a refusal, not a hallucination",
          len(empty_response.citations) == 0)

db.close()

# ---- Summary ----
print("\n" + "=" * 60)
passed = sum(1 for _, s, _ in results if s == "PASS")
total = len(results)
print(f"SUMMARY: {passed}/{total} checks passed")
print("=" * 60)
for label, status, detail in results:
    print(f"  [{status}] {label}")