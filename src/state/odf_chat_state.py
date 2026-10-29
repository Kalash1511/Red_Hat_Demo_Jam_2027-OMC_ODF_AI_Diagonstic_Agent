from __future__ import annotations

from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ODFChatState(TypedDict):
    """
    State for the interactive ODF Ceph chat agent.

    `messages` is managed by LangGraph's add_messages reducer so each
    invocation appends HumanMessage, AIMessage, and ToolMessage objects
    to the current session.
    """

    messages: Annotated[list[AnyMessage], add_messages]

    # Cluster/session context.
    must_gather_path: NotRequired[str]
    session_id: NotRequired[str]

    # Optional diagnostic metadata.
    last_tool_name: NotRequired[str]
    last_response: NotRequired[str]