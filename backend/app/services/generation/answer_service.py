import json
import logging
from typing import Iterator

from app.core.config import settings
from app.models.user import User
from app.schemas.answer import AskResponse
from app.services.generation.citation_parser import parse_citations
from app.services.generation.confidence_service import confidence_service
from app.services.generation.prompt_builder import build_messages
from app.services.llm.llm_factory import LLMProviderFactory
from app.services.search_service import search_service

logger = logging.getLogger(__name__)


class AnswerService:
    def __init__(self):
        self.provider = LLMProviderFactory.get_provider(task="quality")

    def ask(self, query: str, limit: int, current_user: User) -> AskResponse:
        sources = search_service.search_for_llm_context(query=query, limit=limit, current_user=current_user)
        messages = build_messages(query, sources)

        try:
            answer = self.provider.generate(
                messages=messages, temperature=settings.ANSWER_TEMPERATURE, max_tokens=settings.ANSWER_MAX_TOKENS,
            )
        except Exception as e:
            logger.exception(f"Answer generation failed for query='{query}': {e}")
            answer = "I'm unable to generate an answer right now due to a technical issue. Please try again shortly."

        citations = parse_citations(answer, sources)
        confidence = confidence_service.assess(answer, sources, citations)

        logger.info(
            f"Answer generated for user {current_user.id}: query='{query}' "
            f"citations={len(citations)} confidence={confidence.level.value}"
        )

        return AskResponse(
            query=query, answer=answer, citations=citations, sources=sources, confidence=confidence
        )

    # ask_stream from Step 26 unchanged for now - confidence scoring for
    # the streaming path is a reasonable future enhancement (would need
    # its own final SSE event), noted honestly rather than built now to
    # avoid scope creep on this already-multi-part step.


    def ask_stream(self, query: str, limit: int, current_user: User) -> Iterator[str]:
        """
        Yields SSE-formatted event strings. Streams raw text tokens as
        they're generated, then emits a final 'citations' event once the
        full answer is known, then a 'done' event.
        """
        sources = search_service.search_for_llm_context(query=query, limit=limit, current_user=current_user)
        messages = build_messages(query, sources)

        full_answer = ""
        try:
            for token in self.provider.generate_stream(
                messages=messages, temperature=settings.ANSWER_TEMPERATURE, max_tokens=settings.ANSWER_MAX_TOKENS,
            ):
                full_answer += token
                yield _sse_event({"type": "token", "content": token})

        except Exception as e:
            logger.exception(f"Streaming answer generation failed for query='{query}': {e}")
            error_msg = "I'm unable to generate an answer right now due to a technical issue."
            yield _sse_event({"type": "token", "content": error_msg})
            full_answer = error_msg

        citations = parse_citations(full_answer, sources)
        citations_payload = [c.model_dump(mode="json") for c in citations]

        logger.info(
            f"Streamed answer generated for user {current_user.id}: query='{query}' "
            f"sources_used={len(sources)} citations_parsed={len(citations)}"
        )

        yield _sse_event({"type": "citations", "citations": citations_payload})
        yield _sse_event({"type": "done"})


def _sse_event(data: dict) -> str:
    """Formats a dict as a proper SSE 'data: ...' line."""
    return f"data: {json.dumps(data)}\n\n"


answer_service = AnswerService()