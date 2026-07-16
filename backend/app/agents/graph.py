from langgraph.graph import StateGraph, END

from app.agents.rag_node import rag_node
from app.agents.state import AgentState
from app.agents.supervisor_node import supervisor_node


def route_after_supervisor(state: AgentState) -> str:
    """
    Conditional edge function: examines state['intent'] and returns
    the name of the next node to run. Only 'qa' has a real destination
    right now - 'summarize' and 'document_search' will get their own
    nodes in Steps 29-33; for now they also fall through to rag_node
    as a reasonable interim behavior, explicitly noted as provisional.
    """
    intent = state.get("intent", "qa")
    if intent in ("qa", "summarize", "document_search", "unknown"):
        # TODO (Steps 29-33): route "summarize" and "document_search"
        # to their own dedicated nodes once those agents exist.
        return "rag_pipeline"
    return "rag_pipeline"


def build_agent_graph():
    """
    Builds and compiles the LangGraph StateGraph. This is the actual
    'agentic system' entry point going forward - the API layer will
    call graph.invoke(initial_state) instead of calling answer_service
    directly, even though today it still resolves to the same RAG path.
    """
    graph = StateGraph(AgentState)

    graph.add_node("supervisor", supervisor_node)
    graph.add_node("rag_pipeline", rag_node)

    graph.set_entry_point("supervisor")
    graph.add_conditional_edges("supervisor", route_after_supervisor, {"rag_pipeline": "rag_pipeline"})
    graph.add_edge("rag_pipeline", END)

    return graph.compile()


agent_graph = build_agent_graph()