from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from src.agent.odf_troubleshooting_agent.nodes import create_investigator
from src.state.odf_troubleshoot_chat_state import ODFAgentState


def build_odf_graph(llm, tools):

    builder = StateGraph(ODFAgentState)

    investigator = create_investigator(
        llm,
        tools,
    )

    builder.add_node(
        "investigator",
        investigator,
    )

    builder.add_node(
        "tools",
        ToolNode(tools),
    )

    builder.add_edge(
        START,
        "investigator",
    )

    builder.add_conditional_edges(
        "investigator",
        tools_condition,
        {
            "tools": "tools",
            END: END,
        },
    )

    builder.add_edge(
        "tools",
        "investigator",
    )

    return builder.compile()