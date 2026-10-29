from __future__ import annotations

from pathlib import Path
from pprint import pformat

from langchain_core.messages import HumanMessage

from src.llm.gemini_llm import GeminiLLM
from src.omc_client import OMCClient
from src.tools.ceph_tools.ceph_tool_registry import (
    build_ceph_command_registry,
)
from src.state.odf_troubleshoot_chat_state import ODFAgentState
from src.tools.ceph_tools.command_tool_factory import command_to_tool
from src.agent.odf_troubleshooting_agent.odf_troubleshooting_graph import (
    build_odf_troubleshooting_graph,
)


CORE_TROUBLESHOOTING_COMMANDS = [
    "ceph_health_detail",
    "ceph_osd_stat",
    "ceph_osd_tree",
    "ceph_osd_df",
    "ceph_osd_df_tree",
    "ceph_osd_dump",
    "ceph_osd_perf",
    "ceph_osd_utilization",
    "ceph_osd_blocked_by",
    "ceph_osd_lspools",
    "ceph_osd_pool_autoscale_status",
    "ceph_osd_pool_ls_detail",
    "ceph_mgr_dump",
    "ceph_mgr_module_ls",
    "ceph_mgr_services",
    "ceph_osd_crush_class_ls",
    "ceph_osd_crush_dump",
    "ceph_osd_crush_rule_dump",
    "ceph_osd_crush_rule_ls",
    "ceph_osd_crush_show_tunables",
    "ceph_osd_crush_weight_set_dump",
]


# =============================================================================
# TOOL SETUP
# =============================================================================

def _build_tools(registry):
    tools = []

    for name in CORE_TROUBLESHOOTING_COMMANDS:
        tool_definition = registry.get(name)

        if tool_definition is None:
            print(f"[WARNING] Tool not found in registry: {name}")
            continue

        tools.append(
            command_to_tool(tool_definition)
        )

    return tools


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

    output_file = output_dir / "odf_troubleshooting_gemini_graph.png"

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


def _print_graph_structure(graph) -> None:
    """
    Print the graph nodes and edges to the terminal.
    """

    graph_structure = graph.get_graph()

    print("\n" + "=" * 80)
    print("LANGGRAPH STRUCTURE")
    print("=" * 80)

    print("\nNodes:")
    print("-" * 80)

    for node in graph_structure.nodes:
        print(f"  • {node}")

    print("\nEdges:")
    print("-" * 80)

    for edge in graph_structure.edges:
        print(
            f"  {edge.source}  -->  {edge.target}"
        )


# =============================================================================
# MESSAGE VISUALIZATION
# =============================================================================

def _print_message(message, indent: str = "    ") -> None:
    """
    Print a LangChain message in a readable format.
    """

    message_type = type(message).__name__

    print(
        f"{indent}[MESSAGE] {message_type}"
    )

    content = getattr(message, "content", "")

    if content:
        if isinstance(content, str):
            print(
                f"{indent}Content:"
            )

            for line in content.splitlines():
                print(
                    f"{indent}  {line}"
                )
        else:
            print(
                f"{indent}Content:"
            )
            print(
                f"{indent}  {pformat(content)}"
            )

    tool_calls = getattr(
        message,
        "tool_calls",
        None,
    )

    if tool_calls:
        print(
            f"{indent}Tool calls:"
        )

        for call in tool_calls:
            print(
                f"{indent}  ├─ Name: "
                f"{call.get('name')}"
            )

            print(
                f"{indent}  └─ Args: "
                f"{pformat(call.get('args'))}"
            )

    tool_call_id = getattr(
        message,
        "tool_call_id",
        None,
    )

    if tool_call_id:
        print(
            f"{indent}Tool call ID: "
            f"{tool_call_id}"
        )


# =============================================================================
# NODE UPDATE VISUALIZATION
# =============================================================================

def _print_node_update(
    node_name: str,
    update,
    step_number: int,
) -> None:
    """
    Display one LangGraph node execution/update.
    """

    print("\n" + "=" * 80)
    print(
        f"EXECUTION STEP {step_number}"
    )
    print("=" * 80)

    print(
        f"\n[LANGGRAPH NODE]"
    )
    print(
        f"  └── {node_name}"
    )

    if not isinstance(update, dict):
        print(
            "\n[UPDATE]"
        )
        print(
            pformat(update)
        )
        return

    print(
        "\n[STATE UPDATE]"
    )
    print("-" * 80)

    for key, value in update.items():

        print(
            f"\n  {key}:"
        )

        if key == "messages":

            if isinstance(value, list):

                for message in value:
                    _print_message(
                        message,
                        indent="    ",
                    )

            else:
                _print_message(
                    value,
                    indent="    ",
                )

        elif isinstance(value, list):

            print(
                f"    {pformat(value)}"
            )

        else:

            print(
                f"    {pformat(value)}"
            )


# =============================================================================
# LIVE EXECUTION TRACE
# =============================================================================

def _run_with_visual_trace(
    graph,
    initial: ODFAgentState,
):
    """
    Execute the LangGraph using streaming updates.

    This allows us to visualize the actual execution order.
    """

    print("\n" + "=" * 80)
    print("LIVE LANGGRAPH EXECUTION")
    print("=" * 80)

    print(
        "\nExecution flow:"
    )

    print(
        "  START"
    )

    step_number = 0

    final_state = {}

    for update in graph.stream(
        initial,
        stream_mode="updates",
    ):

        step_number += 1

        if not isinstance(update, dict):
            print(
                f"\n[STREAM UPDATE]"
            )
            print(
                pformat(update)
            )
            continue

        # Each update normally contains:
        #
        # {
        #     "node_name": {
        #         ...
        #     }
        # }

        for node_name, node_update in update.items():

            print(
                f"      │"
            )

            print(
                f"      ▼"
            )

            print(
                f"  [{step_number}] {node_name}"
            )

            _print_node_update(
                node_name=node_name,
                update=node_update,
                step_number=step_number,
            )

            print(
                f"\n  └── Completed: {node_name}"
            )

            if isinstance(node_update, dict):
                final_state.update(
                    node_update
                )

    print(
        "\n      │"
    )

    print(
        "      ▼"
    )

    print(
        "     END"
    )

    print("\n" + "=" * 80)
    print("LANGGRAPH EXECUTION COMPLETE")
    print("=" * 80)

    print(
        f"\nTotal execution steps: {step_number}"
    )

    return final_state


# =============================================================================
# FINAL TRACE
# =============================================================================

def _print_final_messages(messages) -> None:
    """
    Print all messages after graph execution.
    """

    print("\n" + "=" * 80)
    print("COMPLETE MESSAGE TRACE")
    print("=" * 80)

    if not messages:
        print("\nNo messages returned.")
        return

    for index, message in enumerate(
        messages,
        start=1,
    ):

        print(
            f"\n[{index}] "
            f"{type(message).__name__}"
        )

        print("-" * 80)

        _print_message(
            message,
            indent="  ",
        )


# =============================================================================
# INITIAL STATE
# =============================================================================

def _build_initial_state(
    query: str,
) -> ODFAgentState:

    return {
        "messages": [
            HumanMessage(
                content=query
            )
        ],
        "user_query": query,
        "domains": [],
        "investigation_round": 0,
        "evidence": [],
        "findings": [],
        "diagnosis": "",
        "severity": "",
        "confidence": 0.0,
        "critic_decision": "",
        "critic_reason": "",
        "missing_evidence": [],
        "remediation": [],
        "verification_steps": [],
        "final_response": "",
    }


# =============================================================================
# MAIN
# =============================================================================

def main() -> None:

    print("=" * 80)
    print("ODF TROUBLESHOOTING AGENT")
    print("Gemini + LangGraph + Ceph Tools")
    print("=" * 80)

    # -------------------------------------------------------------------------
    # MUST-GATHER
    # -------------------------------------------------------------------------

    must_gather_path = input(
        "\nEnter must-gather path: "
    ).strip()

    if not must_gather_path:
        raise ValueError(
            "Must-gather path is required."
        )

    path = Path(must_gather_path)

    if not path.exists():
        raise ValueError(
            f"Must-gather path does not exist: "
            f"{must_gather_path}"
        )

    print(
        f"\n[setup] Loading must-gather:"
    )

    print(
        f"        {must_gather_path}"
    )

    # -------------------------------------------------------------------------
    # OMC
    # -------------------------------------------------------------------------

    print(
        "\n[setup] Initializing OMCClient..."
    )

    client = OMCClient()

    client.use(
        must_gather_path
    )

    print(
        "[setup] OMCClient ready."
    )

    # -------------------------------------------------------------------------
    # TOOLS
    # -------------------------------------------------------------------------

    print(
        "\n[setup] Building Ceph command registry..."
    )

    registry = build_ceph_command_registry(
        client
    )

    tools = _build_tools(
        registry
    )

    print(
        f"[setup] Troubleshooting tools: "
        f"{len(tools)}"
    )

    print(
        "\n[setup] Available tools:"
    )

    for tool in tools:
        print(
            f"  • {tool.name}"
        )

    # -------------------------------------------------------------------------
    # GEMINI
    # -------------------------------------------------------------------------

    print(
        "\n[setup] Initializing Gemini..."
    )

    llm_wrapper = GeminiLLM()

    llm = llm_wrapper.get_gemini_llm()

    print(
        f"[setup] Gemini model: "
        f"{llm_wrapper.model}"
    )

    print(
        f"[setup] Temperature: "
        f"{llm_wrapper.temperature}"
    )

    # -------------------------------------------------------------------------
    # GRAPH
    # -------------------------------------------------------------------------

    print(
        "\n[setup] Building ODF troubleshooting graph..."
    )

    graph = build_odf_troubleshooting_graph(
        llm=llm,
        tools=tools,
    )

    print(
        "[setup] LangGraph compiled successfully."
    )

    # -------------------------------------------------------------------------
    # GRAPH VISUALIZATION
    # -------------------------------------------------------------------------

    _print_graph_structure(
        graph
    )

    _save_graph_png(
        graph
    )

    # -------------------------------------------------------------------------
    # INTERACTIVE LOOP
    # -------------------------------------------------------------------------

    print("\n" + "=" * 80)
    print("ODF TROUBLESHOOTING")
    print("=" * 80)

    print(
        "\nEnter one ODF issue to troubleshoot."
    )

    print(
        "The agent will investigate the issue "
        "using the available Ceph tools."
    )

    print(
        "\nType 'exit' to stop."
    )

    while True:

        query = input(
            "\nODF-TROUBLESHOOT> "
        ).strip()

        if query.lower() == "exit":
            break

        if not query:
            continue

        print("\n" + "=" * 80)
        print("NEW INVESTIGATION")
        print("=" * 80)

        print(
            f"\nUser query:\n"
            f"  {query}"
        )

        initial = _build_initial_state(
            query
        )

        try:

            # -----------------------------------------------------------------
            # RUN GRAPH WITH LIVE EXECUTION
            # -----------------------------------------------------------------

            result = _run_with_visual_trace(
                graph,
                initial,
            )

            # -----------------------------------------------------------------
            # MESSAGE TRACE
            # -----------------------------------------------------------------

            messages = result.get(
                "messages",
                [],
            )

            _print_final_messages(
                messages
            )

            # -----------------------------------------------------------------
            # DIAGNOSTIC SUMMARY
            # -----------------------------------------------------------------

            print("\n" + "=" * 80)
            print("DIAGNOSTIC SUMMARY")
            print("=" * 80)

            print(
                result.get(
                    "investigation_summary",
                    "No summary.",
                )
            )

            # -----------------------------------------------------------------
            # DIAGNOSIS
            # -----------------------------------------------------------------

            print("\n" + "=" * 80)
            print("DIAGNOSIS")
            print("=" * 80)

            print(
                result.get(
                    "diagnosis",
                    "No diagnosis generated.",
                )
            )

            # -----------------------------------------------------------------
            # SEVERITY
            # -----------------------------------------------------------------

            print("\n" + "=" * 80)
            print("SEVERITY")
            print("=" * 80)

            print(
                result.get(
                    "severity",
                    "Not determined.",
                )
            )

            # -----------------------------------------------------------------
            # CONFIDENCE
            # -----------------------------------------------------------------

            print("\n" + "=" * 80)
            print("CONFIDENCE")
            print("=" * 80)

            print(
                result.get(
                    "confidence",
                    0.0,
                )
            )

            # -----------------------------------------------------------------
            # FINDINGS
            # -----------------------------------------------------------------

            print("\n" + "=" * 80)
            print("FINDINGS")
            print("=" * 80)

            findings = result.get(
                "findings",
                [],
            )

            if findings:
                for index, finding in enumerate(
                    findings,
                    start=1,
                ):
                    print(
                        f"\n[{index}]"
                    )
                    print(
                        pformat(finding)
                    )
            else:
                print(
                    "No findings generated."
                )

            # -----------------------------------------------------------------
            # REMEDIATION
            # -----------------------------------------------------------------

            print("\n" + "=" * 80)
            print("REMEDIATION")
            print("=" * 80)

            remediation = result.get(
                "remediation",
                [],
            )

            if remediation:
                for index, step in enumerate(
                    remediation,
                    start=1,
                ):
                    print(
                        f"{index}. {step}"
                    )
            else:
                print(
                    "No remediation generated."
                )

            # -----------------------------------------------------------------
            # VERIFICATION
            # -----------------------------------------------------------------

            print("\n" + "=" * 80)
            print("VERIFICATION STEPS")
            print("=" * 80)

            verification_steps = result.get(
                "verification_steps",
                [],
            )

            if verification_steps:
                for index, step in enumerate(
                    verification_steps,
                    start=1,
                ):
                    print(
                        f"{index}. {step}"
                    )
            else:
                print(
                    "No verification steps generated."
                )

            # -----------------------------------------------------------------
            # FINAL RESPONSE
            # -----------------------------------------------------------------

            print("\n" + "=" * 80)
            print("FINAL TROUBLESHOOTING SOLUTION")
            print("=" * 80)

            print(
                result.get(
                    "final_response",
                    "No response generated.",
                )
            )

        except Exception as exc:

            print("\n" + "=" * 80)
            print("EXECUTION ERROR")
            print("=" * 80)

            print(
                f"\n[{type(exc).__name__}]"
            )

            print(
                str(exc)
            )


if __name__ == "__main__":
    main()
