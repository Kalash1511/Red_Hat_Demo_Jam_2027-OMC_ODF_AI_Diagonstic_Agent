from __future__ import annotations

from typing import Any, Sequence

from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from src.agent.odf_chat_agent.nodes import build_tool_node, create_chat_node
from src.state.odf_chat_state import ODFChatState


def _route_after_chat(
    state: ODFChatState,
) -> str:
    """
    Route to the tool node only when the latest AI message has tool calls.
    """
    messages = state.get("messages", [])

    if not messages:
        return "end"

    latest = messages[-1]

    if getattr(latest, "tool_calls", None):
        return "tools"

    return "end"


def build_odf_chat_graph(
    llm: Any,
    tools: Sequence[BaseTool],
    checkpointer: MemorySaver | None = None,
):
    """
    Build a session-aware ODF Ceph chat graph.

    Graph:

        START -> chat
                   |
                   +-- no tool call --> END
                   |
                   +-- tool call -----> tools
                                          |
                                          +----> chat

    Reusing the same `thread_id` restores the same LangGraph session.
    """
    tool_list = list(tools)

    if not tool_list:
        raise ValueError(
            "At least one OMC Ceph tool is required."
        )

    builder = StateGraph(ODFChatState)

    builder.add_node(
        "chat",
        create_chat_node(
            llm=llm,
            tools=tool_list,
        ),
    )

    builder.add_node(
        "tools",
        build_tool_node(tool_list),
    )

    builder.add_edge(
        START,
        "chat",
    )

    builder.add_conditional_edges(
        "chat",
        _route_after_chat,
        {
            "tools": "tools",
            "end": END,
        },
    )

    builder.add_edge(
        "tools",
        "chat",
    )

    return builder.compile(
        checkpointer=checkpointer or MemorySaver()
    )


def invoke_chat(
    graph: Any,
    user_query: str,
    thread_id: str,
    *,
    must_gather_path: str = "",
) -> ODFChatState:
    """
    Submit one user question into the current LangGraph session.

    The same `thread_id` continues the same MemorySaver conversation.
    """
    query = user_query.strip()

    if not query:
        raise ValueError(
            "User query cannot be empty."
        )

    state: ODFChatState = {
        "messages": [
            HumanMessage(content=query)
        ]
    }

    if must_gather_path:
        state["must_gather_path"] = must_gather_path

    result = graph.invoke(
        state,
        config={
            "configurable": {
                "thread_id": thread_id,
            }
        },
    )

    return result