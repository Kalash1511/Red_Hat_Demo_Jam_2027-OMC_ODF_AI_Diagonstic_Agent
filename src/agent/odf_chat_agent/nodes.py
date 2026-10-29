from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AnyMessage, SystemMessage
from langchain_core.tools import BaseTool

from src.state.odf_chat_state import ODFChatState


SYSTEM_PROMPT = """
You are an OpenShift Data Foundation (ODF) and Ceph support chat agent.

Your job is to answer the user's questions using the registered READ-ONLY
OMC Ceph tools connected to a historical must-gather.

Rules:
- Use OMC Ceph tools whenever cluster data is required.
- Never invent cluster facts, OSD IDs, hosts, pools, capacity values,
  health states, metrics, or command output.
- Treat the must-gather as historical/read-only evidence.
- Never claim that a live-cluster action was executed.
- Prefer the smallest number of tools needed to answer the question.
- If the question asks about a specific OSD, use the aggregated OSD/topology
  tools that are already available rather than inventing a per-OSD command.
- Answer directly from the tool output.
- Preserve exact OSD IDs, host names, status values, capacity values, and units.
- Distinguish facts observed in the must-gather from explanations or hypotheses.
- For follow-up questions, use the previous conversation as session context.
""".strip()


def _tool_names(tools: Sequence[BaseTool]) -> list[str]:
    """Return canonical names exposed by the registered LangChain tools."""
    names: list[str] = []

    for tool in tools:
        name = getattr(tool, "name", None)
        if isinstance(name, str) and name:
            names.append(name)

    return names


def _compact_messages(
    messages: list[AnyMessage],
    max_messages: int = 12,
    max_tool_chars: int = 12000,
) -> list[AnyMessage]:
    """
    Limit the amount of history sent to the LLM.

    LangGraph still keeps the complete message state in the checkpoint.
    This only limits the prompt size sent to the model.
    """
    selected = messages[-max_messages:]
    compacted: list[AnyMessage] = []

    for message in selected:
        if getattr(message, "type", None) != "tool":
            compacted.append(message)
            continue

        content = str(getattr(message, "content", ""))

        if len(content) > max_tool_chars:
            content = (
                content[:max_tool_chars]
                + "\n\n[Tool output truncated before LLM processing.]"
            )

        try:
            compacted.append(
                message.model_copy(
                    update={"content": content}
                )
            )
        except AttributeError:
            compacted.append(message)

    return compacted


def create_chat_node(
    llm: Any,
    tools: Sequence[BaseTool],
):
    """
    Create the main ODF chat node.

    The model can either:
      1. answer directly, or
      2. request one or more registered OMC Ceph tools.
    """
    tool_list = list(tools)
    model = llm.bind_tools(tool_list)
    registered_tools = _tool_names(tool_list)

    def chat_node(
        state: ODFChatState,
    ) -> dict[str, Any]:
        messages = state.get("messages", [])

        system_context = (
            f"{SYSTEM_PROMPT}\n\n"
            f"Registered OMC Ceph tools:\n"
            f"{', '.join(registered_tools)}\n\n"
            f"Must-gather path:\n"
            f"{state.get('must_gather_path', 'not supplied')}"
        )

        response = model.invoke(
            [
                SystemMessage(content=system_context),
                *_compact_messages(messages),
            ]
        )

        tool_calls = getattr(response, "tool_calls", None) or []

        last_tool_name = ""
        if tool_calls:
            first_call = tool_calls[0]
            if isinstance(first_call, dict):
                name = first_call.get("name")
                if isinstance(name, str):
                    last_tool_name = name

        response_content = getattr(response, "content", "")

        return {
            "messages": [response],
            "last_tool_name": last_tool_name,
            "last_response": str(response_content or ""),
        }

    return chat_node


def build_tool_node(tools: Sequence[BaseTool]):
    """
    Create a LangGraph ToolNode from the existing OMC Ceph tools.
    """
    from langgraph.prebuilt import ToolNode

    return ToolNode(list(tools))