from app.agents.retriever_agent import retriever_agent
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository

db = SessionLocal()
user = UserRepository(db).get_by_email("user@example.com")

print("=== Single retrieve() ===")
results = retriever_agent.retrieve("What is the stipend?", user, limit=3)
for r in results:
    print(f"- ({r.filename}) {r.content[:100]}")

print("\n=== Batch retrieve_multi() ===")
batch_results = retriever_agent.retrieve_multi(
    ["What is the stipend?", "What is the bond duration?"], user, limit_per_query=3
)
for query, results in batch_results.items():
    print(f"\nQuery: {query}")
    for r in results:
        print(f"  - ({r.filename}) {r.content[:100]}")

db.close()  