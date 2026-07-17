import logging

from app.agents.state import AgentState
from app.services.llm.llm_factory import LLMProviderFactory

logger = logging.getLogger(__name__)

_SUPERVISOR_PROMPT = """You are a routing classifier for an enterprise knowledge assistant.

Classify the user's request into EXACTLY ONE of these intents:
- "qa": a single, focused question with one specific, known answer
- "complex_qa": a multi-part question or explicit comparison with distinct, \
independently-answerable sub-parts (e.g. "compare X and Y", "what are the \
differences between...")
- "research": an open-ended, broad request for a comprehensive overview or \
briefing on a topic, where the specific sub-topics are NOT explicitly listed \
by the user (e.g. "tell me everything about X", "give me an overview of Y", \
"summarize what we know about Z")
- "summarize": a request to summarize a specific document or set of documents
- "document_search": a request to simply find/list documents, not answer a question
- "unknown": doesn't fit any category above, or is genuinely unclear

Key distinction between "complex_qa" and "research": complex_qa has EXPLICIT, \
named parts to compare or combine. research is OPEN-ENDED with no explicit \
sub-parts named - the assistant must determine what angles to investigate.

Respond with ONLY the intent label, nothing else."""

_VALID_INTENTS = {"qa", "complex_qa", "research", "summarize", "document_search", "unknown"}


def supervisor_node(state: AgentState) -> AgentState:
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