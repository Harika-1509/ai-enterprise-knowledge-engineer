import logging

from app.services.llm.llm_factory import LLMProviderFactory

logger = logging.getLogger(__name__)

_FAITHFULNESS_PROMPT = """You are evaluating whether an AI-generated answer is \
FAITHFUL to its cited sources - meaning every factual claim in the answer is \
actually supported by the source content, with nothing invented or added.

Respond with a single number from 1-5:
5 = Fully faithful, every claim is directly supported by the sources
3 = Partially faithful, some claims are supported but others are not clearly backed
1 = Not faithful, the answer makes claims the sources do not support

Respond with ONLY the number."""

_RELEVANCE_PROMPT = """You are evaluating whether an AI-generated answer is \
RELEVANT to the question that was actually asked - meaning it directly \
addresses what the user wanted to know, not a tangentially related topic.

Respond with a single number from 1-5:
5 = Fully relevant, directly and completely addresses the question
3 = Partially relevant, addresses the question but incompletely or with drift
1 = Not relevant, does not address what was actually asked

Respond with ONLY the number."""


def score_faithfulness(answer: str, sources_text: str) -> int:
    """
    LLM-as-judge: scores whether the answer's claims are supported by
    its sources. Uses the fast/cheap model tier - this is a narrow
    scoring task, not open-ended generation, consistent with our
    cost-matching principle (Step 20, Step 27).
    """
    provider = LLMProviderFactory.get_provider(task="fast")
    try:
        result = provider.generate(
            messages=[
                {"role": "system", "content": _FAITHFULNESS_PROMPT},
                {
                    "role": "user",
                    "content": f"SOURCES:\n{sources_text}\n\nANSWER:\n{answer}",
                },
            ],
            temperature=0.0,
            max_tokens=5,
        )
        return int(result.strip()[0])  # first digit, defensive against extra text
    except Exception as e:
        logger.warning(f"Faithfulness scoring failed: {e}")
        return 0  # 0 = scoring failed, distinct from a real low score of 1


def score_relevance(query: str, answer: str) -> int:
    provider = LLMProviderFactory.get_provider(task="fast")
    try:
        result = provider.generate(
            messages=[
                {"role": "system", "content": _RELEVANCE_PROMPT},
                {
                    "role": "user",
                    "content": f"QUESTION:\n{query}\n\nANSWER:\n{answer}",
                },
            ],
            temperature=0.0,
            max_tokens=5,
        )
        return int(result.strip()[0])
    except Exception as e:
        logger.warning(f"Relevance scoring failed: {e}")
        return 0


def check_retrieval_hit(source_filenames: list[str], expected_filename: str | None) -> bool | None:
    """
    Retrieval hit check: did the expected source document appear
    ANYWHERE in the retrieved sources? Returns None (not applicable)
    for refusal-category test cases with no expected source.
    """
    if expected_filename is None:
        return None
    return expected_filename in source_filenames


def check_contains_expected(answer: str, expected_substrings: list[str]) -> bool:
    """
    Checks whether AT LEAST ONE expected substring appears in the
    answer (case-insensitive) - accounts for the LLM phrasing a fact
    in slightly different but still-correct ways (e.g. "30K" vs "30,000").
    """
    answer_lower = answer.lower()
    return any(s.lower() in answer_lower for s in expected_substrings)