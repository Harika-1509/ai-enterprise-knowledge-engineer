"""
Runs the golden dataset against the live system and reports metrics,
broken down BY CATEGORY so a regression in one agent path can't hide
behind a healthy aggregate average.
Run with: python evaluation/run_evaluation.py
"""

import json
import sys
from collections import defaultdict
from datetime import datetime
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
from app.agents.graph import agent_graph

TEST_USER_EMAIL = "user@example.com"
DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_LOG_PATH = Path(__file__).parent / "results_history.jsonl"


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
        print(f"\nRunning {case['id']} ({case['category']}): {case['query']}")

        initial_state = {
            "query": case["query"],
            "user_id": user.id,
            "limit": 5, 
        }
        final_state = agent_graph.invoke(initial_state)
        
        response = final_state.get("result")

        if response is None:
            print(f"  [ERROR] Agent produced no result: {final_state.get('error')}")
            continue

        actual_intent = final_state.get("intent")
        print(f"  (routed as intent='{actual_intent}')")

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

        flag = "PASS" if contains_expected else "FAIL"
        print(f"  [{flag}] retrieval_hit={retrieval_hit} faithfulness={faithfulness} relevance={relevance}")

    db.close()
    print_summary(results)
    print_category_breakdown(results)
    log_results(results)
    return results


def print_summary(results: list[dict]):
    print("\n" + "=" * 70)
    print("OVERALL SUMMARY")
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


def print_category_breakdown(results: list[dict]):
    print("\n" + "=" * 70)
    print("BREAKDOWN BY CATEGORY (this is what actually matters - a healthy")
    print("overall average can hide a broken agent path)")
    print("=" * 70)

    by_category = defaultdict(list)
    for r in results:
        by_category[r["category"]].append(r)

    for category, cases in by_category.items():
        pass_rate = sum(1 for c in cases if c["contains_expected"]) / len(cases)
        avg_faith = sum(c["faithfulness"] for c in cases if c["faithfulness"]) / max(
            1, sum(1 for c in cases if c["faithfulness"])
        )
        status = "OK" if pass_rate >= 0.8 else "NEEDS ATTENTION"
        print(f"  [{status}] {category}: {pass_rate:.0%} pass rate (n={len(cases)}), avg faithfulness={avg_faith:.1f}")


def log_results(results: list[dict]):
    """
    Appends this run's results to a persistent history file - the
    foundation for detecting regressions across time (did a future
    code change make eval_003 pass, or make a previously-passing case
    start failing?). One line per run, timestamped.
    """
    entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "results": results,
    }
    with open(RESULTS_LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"\nResults appended to {RESULTS_LOG_PATH} for future regression comparison.")


if __name__ == "__main__":
    run_evaluation()