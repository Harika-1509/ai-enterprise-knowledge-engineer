from app.services.compression.context_compressor import context_compressor
from app.services.embedding.embedding_service import embedding_service
import numpy as np
from app.services.search_service import search_service
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository


db = SessionLocal()
user = UserRepository(db).get_by_email("user@example.com")

plain = search_service.search(
    "OCR",
    limit=5,
    current_user=user,
)
sentences = context_compressor._split_sentences(plain[2].content)

query_vec = np.array(
    embedding_service.embed_query("OCR")
)

sent_vecs = np.array(
    embedding_service.embed_documents(sentences)
)

sims = sent_vecs @ query_vec

for s, sim in sorted(zip(sentences, sims), key=lambda x: -x[1]):
    print(f"{sim:.3f}  {s[:70]}")



user = UserRepository(db).get_by_email("user@example.com")

plain = search_service.search("OCR", limit=5, current_user=user)
compressed = search_service.search_for_llm_context("OCR", limit=5, current_user=user)

for i, (p, c) in enumerate(zip(plain, compressed), start=1):
    print(f"\n--- Chunk {i} ---")
    print(f"Original chars   : {len(p.content)}")
    print(f"Compressed chars : {len(c.content)}")
    reduction = (1 - len(c.content) / len(p.content)) * 100 if len(p.content) else 0
    print(f"Reduction        : {reduction:.1f}%")

db.close()