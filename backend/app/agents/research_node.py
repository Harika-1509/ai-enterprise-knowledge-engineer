import logging

from app.agents.retriever_agent import retriever_agent
from app.agents.state import AgentState
from app.core.database import SessionLocal
from app.repositories.user_repository import UserRepository
from app.schemas.answer import AskResponse
from app.schemas.search import SearchResult
from app.services.generation.citation_parser import parse_citations
from app.services.generation.confidence_service import confidence_service
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.security.security_scanner import security_scanner

logger = logging.getLogger(__name__)

_ANGLES_PROMPT = """You generate 3-5 specific research angles (sub-topics to \
investigate) for a broad, open-ended research request.

Rules:
- Each angle should be phrased as a focused, searchable question.
- Angles should cover genuinely DIFFERENT facets of the topic, not near-duplicates.
- Do not invent angles about information the user didn't ask about.
- Output ONLY the angles, one per line, no numbering, no extra commentary."""

_RESEARCH_SYNTHESIS_PROMPT = """You are writing a research summary using ONLY \
the evidence excerpts provided below. This is the same grounding standard as \
direct question-answering: never use outside knowledge, always cite sources.

Structure your summary with brief section headers matching the research angles \
investigated. Under each section, synthesize the relevant evidence into clear \
prose with [Source N] citations for every claim.

If the evidence is thin or missing for a particular angle, say so explicitly \
under that section rather than omitting it silently or filling the gap with \
outside knowledge."""


def _generate_angles(topic: str) -> list[str]:
    """
    Stage 1: derives specific, searchable angles from a broad topic.
    Falls back to treating the topic itself as the only angle if this
    fails - degrades to a single-angle "mini research" rather than
    blocking the request entirely.
    """
    provider = LLMProviderFactory.get_provider(task="fast")
    try:
        raw = provider.generate(
            messages=[
                {"role": "system", "content": _ANGLES_PROMPT},
                {"role": "user", "content": topic},
            ],
            temperature=0.2,  # slight creativity is appropriate here - angle
            # generation benefits from some variety, unlike the strictly
            # deterministic rewriting/classification tasks elsewhere
            max_tokens=300,
        )
        angles = [line.strip() for line in raw.split("\n") if line.strip()]
        return angles[:5] if angles else [topic]
    except Exception as e:
        logger.exception(f"Angle generation failed for topic='{topic}', using topic as single angle: {e}")
        return [topic]


def _deduplicate_evidence(evidence_by_angle: dict[str, list[SearchResult]]) -> list[SearchResult]:
    """
    Pools evidence across all angles, removing duplicate chunks (the
    same document_id + chunk_index can legitimately surface under
    multiple angles, since a single rich chunk may be relevant to
    several research facets at once).
    """
    seen = set()
    pooled = []
    for results in evidence_by_angle.values():
        for r in results:
            key = (str(r.document_id), r.chunk_index)
            if key not in seen:
                seen.add(key)
                pooled.append(r)
    return pooled


def _build_evidence_block(evidence: list[SearchResult]) -> str:
    """Mirrors prompt_builder.build_context_block (Step 22) for consistency."""
    blocks = []
    for i, source in enumerate(evidence, start=1):
        blocks.append(f"[Source {i}] (from \"{source.filename}\")\n{source.content}")
    return "\n\n".join(blocks)


def research_node(state: AgentState) -> AgentState:
    """
    Handles open-ended research requests: generate angles -> gather
    evidence per angle via retrieval-only (Step 30's RetrieverAgent,
    NO generation per angle) -> pool and deduplicate -> single
    synthesis pass over ALL evidence. Deliberately cheaper and better
    suited to broad topics than planner_node's per-sub-question full
    generation (Step 29), because research angles aren't independently
    "askable" questions - they're facets of one topic meant to be
    woven into one coherent narrative.
    """
    db = SessionLocal()
    try:
        user = UserRepository(db).get_by_id(str(state["user_id"]))
        if not user:
            return {**state, "error": "User not found."}

        # Stage 1: Generate research angles
        angles = _generate_angles(state["query"])
        logger.info(f"Research angles for '{state['query']}': {angles}")

        # Stage 2: Retrieval-only gathering per angle (no generation cost per angle)
        limit_per_angle = state.get("limit", 5)
        evidence_by_angle = retriever_agent.retrieve_multi(angles, user, limit_per_angle)

        # Stage 3: Pool and deduplicate
        pooled_evidence = _deduplicate_evidence(evidence_by_angle)
        logger.info(
            f"Gathered {sum(len(v) for v in evidence_by_angle.values())} raw results "
            f"across {len(angles)} angles, deduplicated to {len(pooled_evidence)} unique chunks"
        )

        # ... inside research_node, after Stage 3 (pooling/deduplication), before Stage 4:

        # Security scan (Step 33) - research_node bypasses answer_service's
        # chokepoint by design (Step 31's efficiency rationale), so this
        # gap must be closed explicitly here rather than assumed covered.
        pooled_evidence, security_flags = security_scanner.scan_chunks(pooled_evidence)
        if security_flags:
            logger.warning(
                f"Research security scan: {len(security_flags)} chunk(s) flagged "
                f"across {len(angles)} angles"
            )

        if not pooled_evidence:
            # No evidence at all - produce an honest, ungrounded refusal
            # rather than calling the synthesis LLM with nothing to work from.
            empty_result = AskResponse(
                query=state["query"],
                answer="I don't have enough information in the provided documents to research this topic.",
                citations=[],
                sources=[],
                confidence=confidence_service.assess("", [], []),
            )
            return {**state, "research_angles": angles, "research_evidence": [], "result": empty_result}

        # Stage 4: Single synthesis pass over the full evidence pool
        provider = LLMProviderFactory.get_provider(task="quality")
        evidence_block = _build_evidence_block(pooled_evidence)
        angles_list = "\n".join(f"- {a}" for a in angles)

        summary_text = provider.generate(
            messages=[
                {"role": "system", "content": _RESEARCH_SYNTHESIS_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"RESEARCH TOPIC: {state['query']}\n\n"
                        f"ANGLES INVESTIGATED:\n{angles_list}\n\n"
                        f"EVIDENCE:\n{evidence_block}"
                    ),
                },
            ],
            temperature=0.2,
            max_tokens=1200,  # research summaries are longer than direct answers
        )

        # Stage 5: Citation parsing + confidence, applied once to the final summary
        citations = parse_citations(summary_text, pooled_evidence)
        confidence = confidence_service.assess(summary_text, pooled_evidence, citations)

        final_result = AskResponse(
            query=state["query"],
            answer=summary_text,
            citations=citations,
            sources=pooled_evidence,
            confidence=confidence,
        )

        logger.info(
            f"Research complete: {len(angles)} angles, {len(pooled_evidence)} evidence "
            f"chunks, {len(citations)} citations, confidence={confidence.level.value}"
        )

        return {
            **state,
            "research_angles": angles,
            "research_evidence": pooled_evidence,
            "result": final_result,
        }

    except Exception as e:
        logger.exception(f"research_node failed for query='{state.get('query')}': {e}")
        return {**state, "error": str(e)}
    finally:
        db.close()