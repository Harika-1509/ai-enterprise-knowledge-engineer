import logging

from langgraph.graph import StateGraph, END

from app.agents.planner_node import planner_node
from app.agents.rag_node import rag_node
from app.agents.state import AgentState
from app.agents.supervisor_node import supervisor_node

logger = logging.getLogger(__name__)


def route_after_supervisor(state: AgentState) -> str:
    """
    Conditional edge function: examines state['intent'] and returns the
    name of the next node. "complex_qa" now has a real destination
    (planner); "summarize" and "document_search" still fall through to
    rag_pipeline as an explicitly-flagged interim behavior pending
    Steps 30-33.
    """
    intent = state.get("intent", "qa")
    if intent == "complex_qa":
        return "planner"
    # TODO (Steps 30-33): route "summarize" and "document_search" to
    # their own dedicated nodes once those agents exist.
    return "rag_pipeline"


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("rag_pipeline", rag_node)
    graph.add_node("planner", planner_node)

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {"rag_pipeline": "rag_pipeline", "planner": "planner"},
    )
    graph.add_edge("rag_pipeline", END)
    graph.add_edge("planner", END)

    compiled = graph.compile()
    logger.info("Agent graph compiled: supervisor -> {rag_pipeline | planner} -> END")
    return compiled


agent_graph = build_agent_graph()