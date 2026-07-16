import logging

from app.agents.state import AgentState
from app.services.llm.llm_factory import LLMProviderFactory

logger = logging.getLogger(__name__)

_SUPERVISOR_PROMPT = """You are a routing classifier for an enterprise knowledge assistant.

Classify the user's request into EXACTLY ONE of these intents:
- "qa": a question that should be answered using retrieved document content (the default for most questions)
- "summarize": a request to summarize a document or set of documents
- "document_search": a request to simply find/list documents, not answer a question
- "unknown": doesn't fit any category above, or is unclear

Respond with ONLY the intent label, nothing else."""

_VALID_INTENTS = {"qa", "summarize", "document_search", "unknown"}


def supervisor_node(state: AgentState) -> AgentState:
    """
    Classifies the incoming query's intent, deciding which specialized
    node should handle it next. Uses the fast/cheap model tier - this
    is a narrow classification task, not open-ended generation.
    """
    provider = LLMProviderFactory.get_provider(task="fast")

    try:
        raw_intent = provider.generate(
            messages=[
                {"role": "system", "content": _SUPERVISOR_PROMPT},
                {"role": "user", "content": state["query"]},
            ],
            temperature=0.0,
            max_tokens=10,
        )
        intent = raw_intent.strip().lower()
        if intent not in _VALID_INTENTS:
            logger.warning(f"Supervisor produced unrecognized intent '{intent}', defaulting to 'qa'.")
            intent = "qa"

    except Exception as e:
        logger.exception(f"Supervisor classification failed, defaulting to 'qa': {e}")
        intent = "qa"

    logger.info(f"Supervisor routed query='{state['query']}' -> intent='{intent}'")

    return {**state, "intent": intent, "intent_reasoning": f"Classified as '{intent}'"}