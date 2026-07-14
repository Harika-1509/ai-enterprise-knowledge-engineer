import logging

from groq import Groq

from app.core.config import settings
from app.models.user import User
from app.schemas.answer import AskResponse
from app.services.generation.citation_parser import parse_citations
from app.services.generation.prompt_builder import build_messages
from app.services.search_service import search_service

logger = logging.getLogger(__name__)


class AnswerService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)

    def ask(self, query: str, limit: int, current_user: User) -> AskResponse:
        sources = search_service.search_for_llm_context(
            query=query, limit=limit, current_user=current_user
        )

        messages = build_messages(query, sources)

        try:
            response = self.client.chat.completions.create(
                model=settings.ANSWER_MODEL,
                messages=messages,
                temperature=settings.ANSWER_TEMPERATURE,
                max_tokens=settings.ANSWER_MAX_TOKENS,
            )
            answer = response.choices[0].message.content.strip()

        except Exception as e:
            logger.exception(f"Answer generation failed for query='{query}': {e}")
            answer = (
                "I'm unable to generate an answer right now due to a technical issue. "
                "Please try again shortly."
            )

        citations = parse_citations(answer, sources)

        logger.info(
            f"Answer generated for user {current_user.id}: query='{query}' "
            f"sources_used={len(sources)} citations_parsed={len(citations)}"
        )

        return AskResponse(query=query, answer=answer, citations=citations, sources=sources)


answer_service = AnswerService()