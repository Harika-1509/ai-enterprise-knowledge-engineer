import logging

from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.schemas.answer import AskResponse
from app.services.generation.answer_service import answer_service
from app.services.generation.citation_parser import parse_citations
from app.services.generation.confidence_service import confidence_service
from app.services.llm.llm_factory import LLMProviderFactory

logger = logging.getLogger(__name__)

_DECOMPOSE_PROMPT = """You break complex questions into 2-4 simpler, focused \
sub-questions that can each be answered independently by searching documents.

Rules:
- Each sub-question must be fully self-contained (never use pronouns like "it" \
or "the other one" that refer back to another sub-question).
- Only decompose if genuinely necessary. If the question is already simple and \
answerable in one pass, output it unchanged as the ONLY sub-question.
- Preserve the original question's intent exactly - do not add scope that wasn't asked for.
- Output ONLY the sub-questions, one per line, no numbering, no bullet points, no extra commentary."""

_SYNTHESIZE_PROMPT = """You combine multiple independently-generated sub-answers \
into one coherent, well-organized final answer to the user's original question.

Rules:
- Preserve every [Source N] citation marker EXACTLY as it appears in the sub-answers \
- do not renumber, remove, or paraphrase them away.
- Organize the answer logically - for comparative questions, structure the answer \
point-by-point rather than just concatenating the sub-answers.
- Do not add any information not present in the sub-answers themselves.
- If any sub-answer indicates missing/insufficient information, reflect that \
honestly in the final answer rather than silently dropping that part."""


def _decompose(query: str) -> list[str]:
    """
    Stage 1: asks a small/fast model to split the query into sub-questions.
    Falls back to treating the original query as a single "sub-question"
    if decomposition fails for any reason - this degrades gracefully to
    exactly the same behavior as Step 28's direct rag_node path, rather
    than blocking the request entirely.
    """
    provider = LLMProviderFactory.get_provider(task="fast")
    try:
        raw = provider.generate(
            messages=[
                {"role": "system", "content": _DECOMPOSE_PROMPT},
                {"role": "user", "content": query},
            ],
            temperature=0.0,
            max_tokens=300,
        )
        sub_questions = [line.strip() for line in raw.split("\n") if line.strip()]
        if not sub_questions:
            return [query]
        return sub_questions[:4]  # hard cap - prevents runaway decomposition
    except Exception as e:
        logger.exception(f"Decomposition failed for query='{query}', falling back to single question: {e}")
        return [query]


def _synthesize(original_query: str, sub_answers: list[str]) -> str:
    """
    Stage 3: combines multiple sub-answers into one final response.
    Falls back to simple concatenation if the synthesis call itself
    fails - a degraded but still informative result, rather than losing
    the sub-answers entirely.
    """
    provider = LLMProviderFactory.get_provider(task="quality")
    combined = "\n\n".join(f"Sub-answer {i + 1}: {a}" for i, a in enumerate(sub_answers))

    try:
        return provider.generate(
            messages=[
                {"role": "system", "content": _SYNTHESIZE_PROMPT},
                {
                    "role": "user",
                    "content": f"ORIGINAL QUESTION: {original_query}\n\n{combined}",
                },
            ],
            temperature=0.1,
            max_tokens=1000,
        )
    except Exception as e:
        logger.exception(f"Synthesis failed for query='{original_query}', concatenating as fallback: {e}")
        return "\n\n".join(sub_answers)


def planner_node(state: AgentState) -> AgentState:
    """
    Orchestrates query decomposition and multi-step RAG synthesis:
    decompose -> run each sub-question through the full existing
    Phase 5/6 pipeline -> synthesize into one final answer. This node
    deliberately REUSES answer_service.ask() rather than reimplementing
    retrieval/generation logic - every sub-question benefits from all
    of Steps 17-27's work (hybrid search, reranking, compression,
    guardrails, citations, confidence scoring) automatically.
    """
    db = SessionLocal()
    try:
        user = UserRepository(db).get_by_id(str(state["user_id"]))
        if not user:
            return {**state, "error": "User not found."}

        # Stage 1: Decompose
        sub_questions = _decompose(state["query"])
        logger.info(
            f"Planner decomposed query='{state['query']}' into "
            f"{len(sub_questions)} sub-question(s): {sub_questions}"
        )

        # Stage 2: Execute each sub-question through the existing RAG pipeline
        sub_answers: list[AskResponse] = []
        all_sources = []
        for sub_question in sub_questions:
            answer = answer_service.ask(
                query=sub_question, limit=state.get("limit", 5), current_user=user
            )
            sub_answers.append(answer)
            all_sources.extend(answer.sources)
            logger.info(
                f"Sub-question answered: '{sub_question}' -> "
                f"{len(answer.citations)} citations, confidence={answer.confidence.level.value}"
            )

        # Stage 3: Synthesize (skipped entirely if decomposition determined
        # only one sub-question was actually needed - avoids a wasted LLM call)
        if len(sub_answers) == 1:
            final_result = sub_answers[0]
            logger.info("Single sub-question - skipping synthesis, using direct answer.")
        else:
            synthesized_text = _synthesize(state["query"], [a.answer for a in sub_answers])
            citations = parse_citations(synthesized_text, all_sources)
            confidence = confidence_service.assess(synthesized_text, all_sources, citations)

            final_result = AskResponse(
                query=state["query"],
                answer=synthesized_text,
                citations=citations,
                sources=all_sources,
                confidence=confidence,
            )
            logger.info(
                f"Synthesized {len(sub_answers)} sub-answers into final response "
                f"with {len(citations)} citations."
            )

        return {**state, "sub_questions": sub_questions, "sub_answers": sub_answers, "result": final_result}

    except Exception as e:
        logger.exception(f"planner_node failed for query='{state.get('query')}': {e}")
        return {**state, "error": str(e)}
    finally:
        db.close()