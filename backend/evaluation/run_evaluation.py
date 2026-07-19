"""
Runs the golden dataset against the live system and reports metrics.
Run with: python evaluation/run_evaluation.py
"""

import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.services.generation.answer_service import answer_service
from evaluation.metrics import (
    check_contains_expected,
    check_retrieval_hit,
    score_faithfulness,
    score_relevance,
)

TEST_USER_EMAIL = "user@example.com"
DATASET_PATH = Path(__file__).parent / "golden_dataset.json"


def run_evaluation():
    db = SessionLocal()
    user = UserRepository(db).get_by_email(TEST_USER_EMAIL)
    if not user:
        print(f"Test user {TEST_USER_EMAIL} not found.")
        return

    with open(DATASET_PATH) as f:
        dataset = json.load(f)

    results = []

    for case in dataset:
        print(f"\nRunning {case['id']}: {case['query']}")

        response = answer_service.ask(query=case["query"], limit=5, current_user=user)

        retrieval_hit = check_retrieval_hit(
            [s.filename for s in response.sources], case.get("expected_source_filename")
        )
        contains_expected = check_contains_expected(
            response.answer, case["expected_answer_contains"]
        )

        sources_text = "\n\n".join(s.content for s in response.sources)
        faithfulness = score_faithfulness(response.answer, sources_text) if sources_text else None
        relevance = score_relevance(case["query"], response.answer)

        result = {
            "id": case["id"],
            "category": case["category"],
            "retrieval_hit": retrieval_hit,
            "contains_expected": contains_expected,
            "faithfulness": faithfulness,
            "relevance": relevance,
            "answer_preview": response.answer[:150],
        }
        results.append(result)

        print(f"  retrieval_hit={retrieval_hit} contains_expected={contains_expected} "
              f"faithfulness={faithfulness} relevance={relevance}")

    db.close()
    print_summary(results)
    return results


def print_summary(results: list[dict]):
    print("\n" + "=" * 70)
    print("EVALUATION SUMMARY")
    print("=" * 70)

    total = len(results)
    contains_expected_rate = sum(1 for r in results if r["contains_expected"]) / total

    retrieval_applicable = [r for r in results if r["retrieval_hit"] is not None]
    retrieval_hit_rate = (
        sum(1 for r in retrieval_applicable if r["retrieval_hit"]) / len(retrieval_applicable)
        if retrieval_applicable else None
    )

    faithfulness_scores = [r["faithfulness"] for r in results if r["faithfulness"]]
    avg_faithfulness = sum(faithfulness_scores) / len(faithfulness_scores) if faithfulness_scores else None

    relevance_scores = [r["relevance"] for r in results if r["relevance"]]
    avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else None

    print(f"Total cases: {total}")
    print(f"Contains-expected-fact rate: {contains_expected_rate:.1%}")
    if retrieval_hit_rate is not None:
        print(f"Retrieval hit rate: {retrieval_hit_rate:.1%} (n={len(retrieval_applicable)})")
    if avg_faithfulness is not None:
        print(f"Average faithfulness (1-5): {avg_faithfulness:.2f}")
    if avg_relevance is not None:
        print(f"Average relevance (1-5): {avg_relevance:.2f}")

    print("\nPer-case breakdown:")
    for r in results:
        flag = "PASS" if r["contains_expected"] else "FAIL"
        print(f"  [{flag}] {r['id']} ({r['category']}) - faithfulness={r['faithfulness']} relevance={r['relevance']}")


if __name__ == "__main__":
    run_evaluation()