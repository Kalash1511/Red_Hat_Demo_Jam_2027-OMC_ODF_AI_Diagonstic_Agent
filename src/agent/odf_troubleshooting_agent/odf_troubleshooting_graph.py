from __future__ import annotations

from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode

from src.agent.odf_troubleshooting_agent.nodes import (
    create_troubleshooting_critic,
    create_troubleshooting_evidence_analyst,
    create_troubleshooting_investigator,
    create_troubleshooting_solution_critic,
    create_troubleshooting_solution_generator,
    finalize_troubleshooting_response,
)
from src.state.odf_troubleshoot_chat_state import ODFAgentState


# The full tool registry can still be supplied to the investigator, but these
# maps constrain which tools are preferred for each detected issue class.
ISSUE_TOOL_MAP: dict[str, list[str]] = {
    "pg_damage": [
        "omc_ceph_health_detail",
        "omc_ceph_osd_stat",
        "omc_ceph_osd_tree",
        "omc_ceph_osd_dump",
        "omc_ceph_osd_perf",
    ],
    "osd_health": [
        "omc_ceph_health_detail",
        "omc_ceph_osd_stat",
        "omc_ceph_osd_tree",
        "omc_ceph_osd_df",
        "omc_ceph_osd_dump",
    ],
    "capacity": [
        "omc_ceph_health_detail",
        "omc_ceph_osd_stat",
        "omc_ceph_osd_df",
        "omc_ceph_osd_df_tree",
    ],
    "pool": [
        "omc_ceph_health_detail",
        "omc_ceph_osd_lspools",
        "omc_ceph_osd_pool_autoscale_status",
        "omc_ceph_osd_pool_ls_detail",
    ],
    "crush": [
        "omc_ceph_health_detail",
        "omc_ceph_osd_tree",
        "omc_ceph_osd_crush_dump",
        "omc_ceph_osd_crush_rule_dump",
        "omc_ceph_osd_crush_rule_ls",
        "omc_ceph_osd_crush_weight_set_dump",
    ],
    "mgr": [
        "omc_ceph_health_detail",
        "omc_ceph_mgr_dump",
        "omc_ceph_mgr_module_ls",
        "omc_ceph_mgr_services",
    ],
    "general": [
        "omc_ceph_health_detail",
        "omc_ceph_osd_stat",
        "omc_ceph_osd_tree",
        "omc_ceph_osd_df",
    ],
}


def classify_ceph_issue(evidence: list[dict[str, str]]) -> str:
    """Classify the current Ceph issue from compact evidence."""
    text = "\n".join(
        value
        for item in evidence
        for value in item.values()
        if value
    ).lower()

    if any(
        marker in text
        for marker in (
            "pg_damaged",
            "inconsistent",
            "scrub error",
            "scrub_errors",
            "possible data damage",
        )
    ):
        return "pg_damage"

    if any(
        marker in text
        for marker in (
            "osd down",
            "osds down",
            "osd is down",
            "recovery blocked",
        )
    ):
        return "osd_health"

    if any(
        marker in text
        for marker in (
            "nearfull",
            "near-full",
            "full",
        )
    ):
        return "capacity"

    if any(
        marker in text
        for marker in (
            "autoscale",
            "pool ",
            "pool:",
        )
    ):
        return "pool"

    if any(
        marker in text
        for marker in (
            "crush",
            "placement rule",
        )
    ):
        return "crush"

    if any(
        marker in text
        for marker in (
            "mgr",
            "manager",
        )
    ):
        return "mgr"

    return "general"


def recommended_tools_for_state(state: ODFAgentState) -> list[str]:
    """Return available, relevant, and not-yet-collected tools."""
    issue_class = state.get("issue_class", "general")
    available = set(state.get("available_tools", []))
    collected = set(state.get("collected_tools", []))

    candidates = ISSUE_TOOL_MAP.get(
        issue_class,
        ISSUE_TOOL_MAP["general"],
    )

    return [
        tool
        for tool in candidates
        if tool in available and tool not in collected
    ]


def _extract_tool_calls(state: ODFAgentState) -> list[dict]:
    """Return tool calls from the latest AI message."""
    messages = state.get("messages", [])
    if not messages:
        return []

    tool_calls = getattr(messages[-1], "tool_calls", None)
    if not tool_calls:
        return []

    return list(tool_calls)


def _route_after_investigator(state: ODFAgentState) -> str:
    """
    Route investigator output to ToolNode only when at least one new,
    registered, relevant tool call is present.
    """
    tool_calls = _extract_tool_calls(state)

    if not tool_calls:
        return "critic"

    collected = set(state.get("collected_tools", []))
    available = set(state.get("available_tools", []))
    recommended = set(state.get("recommended_tools", []))

    for call in tool_calls:
        tool_name = call.get("name")

        if not tool_name:
            continue
        if tool_name not in available:
            continue
        if tool_name in collected:
            continue

        # A recommendation set is a preference, not an absolute prohibition.
        # The hard boundaries are: registered and not already collected.
        if not recommended or tool_name in recommended:
            return "tools"

    return "critic"


def _route_after_critic(state: ODFAgentState) -> str:
    """
    Continue only when the critic identifies valid, uncollected evidence.
    """
    decision = state.get(
        "critic_decision",
        "need_more_evidence",
    )

    rounds = state.get("investigation_round", 0)
    maximum = state.get(
        "max_investigation_rounds",
        5,
    )

    if decision == "ready":
        return "solution"

    if rounds >= maximum:
        return "solution"

    missing = state.get("missing_evidence", [])
    available = set(state.get("available_tools", []))
    collected = set(state.get("collected_tools", []))

    actionable_missing = [
        item
        for item in missing
        if item in available and item not in collected
    ]

    if not actionable_missing:
        return "solution"

    return "investigator"


def _route_after_solution_critic(state: ODFAgentState) -> str:
    """Limit solution revisions to avoid an unbounded solution loop."""
    decision = state.get(
        "solution_critic_decision",
        "pass",
    )
    revisions = state.get(
        "solution_revision",
        0,
    )
    maximum = state.get(
        "max_solution_revisions",
        1,
    )

    if decision == "revise" and revisions < maximum:
        return "solution"

    return "finalize"


def build_odf_troubleshooting_graph(llm, tools):
    """Build the bounded ODF troubleshooting graph."""
    builder = StateGraph(ODFAgentState)

    builder.add_node(
        "investigator",
        create_troubleshooting_investigator(llm, tools),
    )
    builder.add_node(
        "tools",
        ToolNode(tools),
    )
    builder.add_node(
        "evidence_analyst",
        create_troubleshooting_evidence_analyst(llm),
    )
    builder.add_node(
        "critic",
        create_troubleshooting_critic(llm),
    )
    builder.add_node(
        "solution",
        create_troubleshooting_solution_generator(llm),
    )
    builder.add_node(
        "solution_critic",
        create_troubleshooting_solution_critic(llm),
    )
    builder.add_node(
        "finalize",
        finalize_troubleshooting_response,
    )

    builder.add_edge(START, "investigator")

    builder.add_conditional_edges(
        "investigator",
        _route_after_investigator,
        {
            "tools": "tools",
            "critic": "critic",
        },
    )

    builder.add_edge("tools", "evidence_analyst")
    builder.add_edge("evidence_analyst", "critic")

    builder.add_conditional_edges(
        "critic",
        _route_after_critic,
        {
            "investigator": "investigator",
            "solution": "solution",
        },
    )

    builder.add_edge("solution", "solution_critic")

    builder.add_conditional_edges(
        "solution_critic",
        _route_after_solution_critic,
        {
            "solution": "solution",
            "finalize": "finalize",
        },
    )

    builder.add_edge("finalize", END)

    return builder.compile()
