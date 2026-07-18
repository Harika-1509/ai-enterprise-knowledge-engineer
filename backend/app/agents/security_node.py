import logging

from app.agents.state import AgentState

logger = logging.getLogger(__name__)

# Basic query-level red flags: attempts to directly reference another
# user's identifier, or common social-engineering phrasing targeting
# the assistant itself. This is a lightweight pre-check, NOT a
# replacement for the real access control already enforced at the
# retrieval layer (Step 17's owner_id filtering) - even if a malicious
# query slipped past this check, retrieval would still only return
# the requesting user's own documents.
_SUSPICIOUS_QUERY_PATTERNS = [
    "show me all users",
    "list every document in the system",
    "bypass access control",
    "admin password",
    "act as an admin",
]


def security_node_precheck(state: AgentState) -> AgentState:
    """
    Runs BEFORE supervisor routing, as a first pass over the raw query
    itself. Logs and flags suspicious patterns but does NOT block by
    default - the real enforcement remains the owner_id filtering at
    retrieval (Step 17) and RBAC (Step 6). This is a visibility/logging
    layer, not the primary defense.
    """
    query_lower = state["query"].lower()
    matched = [p for p in _SUSPICIOUS_QUERY_PATTERNS if p in query_lower]

    if matched:
        logger.warning(
            f"Suspicious query pattern(s) detected for user {state.get('user_id')}: "
            f"{matched} - query='{state['query']}'"
        )

    return state