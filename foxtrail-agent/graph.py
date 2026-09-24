from langgraph.graph import StateGraph, START, END
from state import CaseState

from investigate_node import investigate_node
from gather_evidence_node import gather_evidence_node
from assess_node import assess_node
from decide_node import decide_node
from explain_node import explain_node
from memory_node import memory_node


# LangGraph nodes must be async-compatible; decide_node is sync, so we wrap it.
async def decide_node_wrapped(state: CaseState) -> CaseState:
    return decide_node(state)


def build_graph():
    builder = StateGraph(CaseState)

    builder.add_node("investigate", investigate_node)
    builder.add_node("gather_evidence", gather_evidence_node)
    builder.add_node("assess", assess_node)
    builder.add_node("decide", decide_node_wrapped)
    builder.add_node("explain", explain_node)
    builder.add_node("memory", memory_node)

    builder.add_edge(START, "investigate")
    builder.add_edge("investigate", "gather_evidence")
    builder.add_edge("gather_evidence", "assess")
    builder.add_edge("assess", "decide")
    builder.add_edge("decide", "explain")
    builder.add_edge("explain", "memory")
    builder.add_edge("memory", END)

    return builder.compile()