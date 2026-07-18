import logging

from langgraph.graph import StateGraph, END

from app.agents.document_node import document_node
from app.agents.planner_node import planner_node
from app.agents.rag_node import rag_node
from app.agents.research_node import research_node
from app.agents.state import AgentState
from app.agents.supervisor_node import supervisor_node

logger = logging.getLogger(__name__)


def route_after_supervisor(state: AgentState) -> str:
    intent = state.get("intent", "qa")
    if intent == "complex_qa":
        return "planner"
    if intent == "research":
        return "research"
    if intent in ("summarize", "document_search"):
        return "document"
    # TODO (Step 33): route to a dedicated Security Agent once built
    return "rag_pipeline"


def build_agent_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("rag_pipeline", rag_node)
    graph.add_node("planner", planner_node)
    graph.add_node("research", research_node)
    graph.add_node("document", document_node)

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges(
        "supervisor",
        route_after_supervisor,
        {
            "rag_pipeline": "rag_pipeline",
            "planner": "planner",
            "research": "research",
            "document": "document",
        },
    )
    graph.add_edge("rag_pipeline", END)
    graph.add_edge("planner", END)
    graph.add_edge("research", END)
    graph.add_edge("document", END)

    compiled = graph.compile()
    logger.info(
        "Agent graph compiled: supervisor -> "
        "{rag_pipeline | planner | research | document} -> END"
    )
    return compiled


agent_graph = build_agent_graph()