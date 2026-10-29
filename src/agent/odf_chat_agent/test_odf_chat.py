from __future__ import annotations

from collections.abc import Mapping
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from src.agent.odf_chat_agent.odf_chat_graph import (
    build_odf_chat_graph,
    invoke_chat,
)
from src.state.odf_chat_state import ODFChatState
from src.llm.groq_llm import GroqLLM
from src.omc_client import OMCClient
from src.tools.ceph_tools.ceph_tool_registry import (
    build_ceph_command_registry,
)
from src.tools.ceph_tools.command_tool_factory import (
    command_to_tool,
)

# =============================================================================
# GRAPH VISUALIZATION
# =============================================================================

def _save_graph_png(graph) -> None:
    """
    Generate a PNG representation of the compiled LangGraph.

    The PNG is saved in a dedicated graph_visualization directory.
    """

    output_dir = Path("graph_visualization")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "odf_chat_agent_graph.png"

    try:
        graph.get_graph().draw_mermaid_png(
            output_file_path=str(output_file)
        )

        print(
            f"[graph] Graph visualization saved to: "
            f"{output_file.resolve()}"
        )

    except Exception as exc:
        print(
            "[graph] Could not generate graph PNG."
        )
        print(
            f"[graph] {type(exc).__name__}: {exc}"
        )



def _registry_definitions(
    registry: Any,
) -> list[Any]:
    """
    Extract command definitions from the current registry.

    The explicit isinstance checks prevent Pylance from treating `value`
    as plain `object` before calling list(value).
    """
    for attr_name in (
        "commands",
        "definitions",
        "_commands",
        "_definitions",
    ):
        value = getattr(
            registry,
            attr_name,
            None,
        )

        if isinstance(value, Mapping):
            return list(value.values())

        if isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes),
        ):
            return list(value)

    for method_name in (
        "all",
        "list_commands",
        "get_all",
    ):
        method = getattr(
            registry,
            method_name,
            None,
        )

        if not callable(method):
            continue

        value = method()

        if isinstance(value, Mapping):
            return list(value.values())

        if isinstance(value, Sequence) and not isinstance(
            value,
            (str, bytes),
        ):
            return list(value)

    if isinstance(registry, Sequence) and not isinstance(
        registry,
        (str, bytes),
    ):
        return list(registry)

    raise TypeError(
        "Could not obtain CommandDefinition objects from "
        "OMCCommandRegistry. Update _registry_definitions() "
        "to match the current registry API."
    )


def build_tools(
    client: OMCClient,
) -> list[Any]:
    """
    Convert the existing Ceph command registry into LangChain tools.
    """
    registry = build_ceph_command_registry(client)

    definitions = _registry_definitions(
        registry
    )

    tools = [
        command_to_tool(definition)
        for definition in definitions
    ]

    if not tools:
        raise RuntimeError(
            "No Ceph tools were created."
        )

    return tools


def print_trace(
    state: ODFChatState,
) -> None:
    """
    Print the current session message history.
    """
    print("\n" + "=" * 80)
    print("SESSION TRACE")
    print("=" * 80)

    messages = state.get(
        "messages",
        [],
    )

    for index, message in enumerate(
        messages,
        start=1,
    ):
        message_type = getattr(
            message,
            "type",
            type(message).__name__,
        )

        print(
            f"\n[{index}] {message_type}"
        )

        tool_calls = getattr(
            message,
            "tool_calls",
            None,
        )

        if tool_calls:
            print("Tool calls:")

            for call in tool_calls:
                if not isinstance(call, dict):
                    print(f"  - {call}")
                    continue

                print(
                    f"  - {call.get('name')} "
                    f"{call.get('args', {})}"
                )

        content = getattr(
            message,
            "content",
            "",
        )

        if content:
            print(
                str(content)[:6000]
            )


def main() -> None:
    print("=" * 80)
    print("ODF CLUSTER CHAT - LANGGRAPH MEMORY TEST")
    print("=" * 80)

    must_gather_path = input(
        "Enter must-gather path: "
    ).strip()

    if not must_gather_path:
        raise ValueError(
            "Must-gather path is required."
        )

    path = Path(
        must_gather_path
    )

    if not path.exists():
        raise FileNotFoundError(
            f"Must-gather path does not exist: "
            f"{must_gather_path}"
        )

    print(
        f"\n[setup] Loading must-gather: "
        f"{must_gather_path}"
    )

    client = OMCClient()
    client.use(
        must_gather_path
    )

    tools = build_tools(client)

    print(
        f"[setup] Registered tools: "
        f"{len(tools)}"
    )

    for tool in tools:
        print(
            f"[setup] Tool: {tool.name}"
        )

    llm = GroqLLM().get_llm()

    graph = build_odf_chat_graph(
        llm=llm,
        tools=tools,
    )

    
    # -------------------------------------------------------------------------
    # GRAPH VISUALIZATION
    # -------------------------------------------------------------------------


    _save_graph_png(
        graph
    )
    # Same thread_id = same MemorySaver session.
    thread_id = "odf-cli-session"

    print("\n" + "=" * 80)
    print("ODF CHAT READY")
    print("=" * 80)

    print(
        "Ask questions about the ODF/Ceph cluster."
    )

    print("Examples:")
    print(
        "  - What is the Ceph cluster health?"
    )
    print(
        "  - How many OSDs are up and in?"
    )
    print(
        "  - What is the status of OSD 3?"
    )
    print(
        "  - What is the total OSD capacity?"
    )
    print(
        "  - Are there any OSD problems?"
    )
    print(
        "  - exit"
    )

    while True:
        try:
            query = input(
                "\nODF> "
            ).strip()
        except (
            EOFError,
            KeyboardInterrupt,
        ):
            print(
                "\nExiting."
            )
            break

        if not query:
            continue

        if query.lower() in {
            "exit",
            "quit",
        }:
            print(
                "Exiting."
            )
            break

        try:
            state = invoke_chat(
                graph,
                query,
                thread_id,
                must_gather_path=must_gather_path,
            )

            print_trace(
                state
            )

            messages = state.get(
                "messages",
                [],
            )

            if not messages:
                continue

            last = messages[-1]

            if (
                getattr(last, "type", "") == "ai"
                and getattr(last, "content", "")
            ):
                print("\n" + "=" * 80)
                print("FINAL RESPONSE")
                print("=" * 80)
                print(last.content)

        except Exception as exc:
            print(
                f"\n[ERROR] "
                f"{type(exc).__name__}: {exc}"
            )


if __name__ == "__main__":
    main()