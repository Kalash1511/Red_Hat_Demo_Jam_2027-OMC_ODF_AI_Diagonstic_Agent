from __future__ import annotations

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage,AnyMessage
from pydantic import BaseModel, Field

from src.agent.odf_troubleshooting_agent.prompts import (
    CRITIC_PROMPT,
    SOLUTION_CRITIC_PROMPT,
    SOLUTION_PROMPT,
    SYSTEM_PROMPT,
)
from src.state.odf_troubleshoot_chat_state import ODFAgentState


# ============================================================================
# Structured outputs
# ============================================================================


class DiagnosticCritique(BaseModel):
    decision: str = Field(
        description="Either 'ready' or 'need_more_evidence'."
    )
    reason: str = Field(default="")
    missing_evidence: list[str] = Field(default_factory=list)


class SolutionCritique(BaseModel):
    decision: str = Field(
        description="Either 'pass' or 'revise'."
    )
    reason: str = Field(default="")


class EvidenceSummary(BaseModel):
    """Compact summary of only the latest OMC observations."""

    summary: str = Field(default="")
    confirmed_findings: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)


# ============================================================================
# Troubleshooting prompts
# ============================================================================


TROUBLESHOOTING_INVESTIGATOR_PROMPT = """
You are the investigation agent for a Red Hat OpenShift and Ceph/ODF
troubleshooting workflow.

A user has reported ONE problem. Investigate only that problem using the
available READ-ONLY OMC must-gather tools.

Rules:
- Use the smallest useful number of tools.
- Prefer the recommended tools for the current issue class.
- Never repeat an already collected tool unless the previous execution failed.
- Never invent command names, command output, OSDs, PGs, pools, nodes, metrics,
  events, or configuration.
- Only call tools whose exact names are listed in Available tools.
- Only call tools that provide evidence relevant to the reported issue.
- If the current evidence is already sufficient, do not call another tool.
- The must-gather is historical/read-only. Do not claim that any live-cluster
  action has been performed.
"""


TROUBLESHOOTING_EVIDENCE_PROMPT = """
You are the evidence analyst for a Red Hat OpenShift Ceph/ODF troubleshooting
agent.

Analyze ONLY the latest OMC ToolMessage output supplied below.

Rules:
- Preserve exact names, IDs, states, and values.
- Do not invent missing information.
- Do not turn a hypothesis into a confirmed fact.
- Do not repeat old evidence unless needed for context.
- Keep the result compact.
"""


TROUBLESHOOTING_CRITIC_PROMPT = """
You are the diagnostic critic for a Red Hat OpenShift Ceph/ODF support agent.

Review the user issue and compact evidence.

Return:
- ready: enough evidence exists for a defensible diagnosis/remediation plan.
- need_more_evidence: another registered OMC tool is required.

Important:
- missing_evidence MUST contain canonical tool names from Available tools.
- Never invent a tool name.
- Never request a tool already listed in Already collected tools.
- Never request commands that are not registered in Available tools.
- Prefer the minimum additional evidence needed.
- Do not request generic Kubernetes/OpenShift commands when they are not
  available through the current tool registry.
"""


TROUBLESHOOTING_SOLUTION_PROMPT = """
You are the remediation advisor for a Red Hat OpenShift and Ceph/ODF
troubleshooting agent.

Using ONLY the collected evidence, create a complete and actionable response.

Structure:

1. Issue summary
2. Confirmed findings
3. Likely root cause
4. Immediate remediation steps
5. Additional checks if remediation is unsuccessful
6. Verification steps
7. Important cautions / conditions

Rules:
- Distinguish confirmed facts from hypotheses.
- Do not claim that a remediation has already been executed.
- The current source is a historical/read-only must-gather.
- Do not invent cluster facts or command output.
- Do not recommend destructive actions without preconditions.
"""


TROUBLESHOOTING_SOLUTION_CRITIC_PROMPT = """
You are the final safety and quality reviewer for a Ceph/ODF remediation plan.

PASS when the plan is:
- supported by the collected evidence,
- technically coherent,
- actionable against a live cluster,
- explicit about assumptions and conditions,
- clear about verification,
- and does not claim that actions have already been performed.

REVISE when it contains unsupported claims, skips important checks, or proposes
an unsafe or unjustified action.
"""


# ============================================================================
# Helpers
# ============================================================================


def _tool_names(tools: list[Any]) -> list[str]:
    """Return canonical registered tool names."""
    return [
        name
        for name in (
            getattr(tool, "name", None)
            for tool in tools
        )
        if name
    ]


def _latest_tool_messages(messages: list[AnyMessage]) -> list[ToolMessage]:
    """
    Return only ToolMessages produced by the most recent tool-call turn.

    This avoids repeatedly sending the complete historical ToolMessage
    transcript to the evidence-analysis LLM.
    """
    latest: list[ToolMessage] = []

    for message in reversed(messages):
        if isinstance(message, ToolMessage):
            latest.append(message)
            continue

        if latest:
            break

    latest.reverse()
    return latest


def _merge_unique_evidence(
    existing: list[dict[str, str]],
    new_items: list[dict[str, str]],
) -> list[dict[str, str]]:
    """Merge evidence without duplicating identical tool/output pairs."""
    merged = list(existing)

    known = {
        (
            item.get("tool", ""),
            item.get("output", ""),
        )
        for item in merged
    }

    for item in new_items:
        key = (
            item.get("tool", ""),
            item.get("output", ""),
        )

        if key not in known:
            merged.append(item)
            known.add(key)

    return merged


def _classify_issue_from_text(text: str) -> str:
    """Classify common high-confidence Ceph/ODF failure signatures."""
    lowered = text.lower()

    if any(
        marker in lowered
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
        marker in lowered
        for marker in (
            "osd down",
            "osds down",
            "osd is down",
            "recovery blocked",
        )
    ):
        return "osd_health"

    if any(
        marker in lowered
        for marker in (
            "nearfull",
            "near-full",
            "full",
        )
    ):
        return "capacity"

    if any(
        marker in lowered
        for marker in (
            "autoscale",
            "pool ",
            "pool:",
        )
    ):
        return "pool"

    if any(
        marker in lowered
        for marker in (
            "crush",
            "placement rule",
        )
    ):
        return "crush"

    if any(
        marker in lowered
        for marker in (
            "mgr",
            "manager",
        )
    ):
        return "mgr"

    return "general"


def _issue_from_evidence(evidence: list[dict[str, str]]) -> str:
    text = "\n".join(
        value
        for item in evidence
        for value in item.values()
        if value
    )
    return _classify_issue_from_text(text)


def _recommended_tools(
    available_tools: list[str],
    collected_tools: list[str],
    issue_class: str,
) -> list[str]:
    """
    Return relevant registered tools which have not already been collected.

    NOTE: this intentionally accepts explicit typed arguments instead of an
    `ODFAgentState` so Pylance does not reject temporary dicts constructed by
    callers.
    """
    local_map: dict[str, list[str]] = {
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

    available = set(available_tools)
    collected = set(collected_tools)

    candidates = local_map.get(
        issue_class,
        local_map["general"],
    )

    return [
        tool
        for tool in candidates
        if tool in available and tool not in collected
    ]


def _investigator_context(
    state: ODFAgentState,
    issue_class: str,
    recommended_tools: list[str],
    available_tools: list[str],
) -> str:
    """Build compact investigator context without replaying raw history."""
    evidence = state.get("evidence", [])

    evidence_lines: list[str] = []
    for item in evidence:
        tool = item.get("tool", "unknown")
        output = item.get("output", "")
        evidence_lines.append(
            f"[{tool}]\n{output}"
        )

    compact_evidence = "\n\n".join(evidence_lines)
    if not compact_evidence:
        compact_evidence = (
            state.get("investigation_summary", "")
            or "No compact evidence has been gathered yet."
        )

    return (
        f"Issue class: {issue_class}\n"
        f"Recommended tools: {recommended_tools or 'None'}\n"
        f"Already collected: {state.get('collected_tools', []) or 'None'}\n"
        f"Available tools: {available_tools or 'None'}\n"
        f"Compact evidence:\n{compact_evidence}"
    )


# ============================================================================
# Generic compatibility nodes
# ============================================================================


def create_investigator(llm, tools):
    """Create the older generic ReAct investigator."""
    llm_with_tools = llm.bind_tools(tools)

    def investigator(state: ODFAgentState) -> dict[str, Any]:
        domains = state.get("domains", [])
        domain_hint = (
            ", ".join(domains)
            if domains
            else "cluster_health"
        )
        round_number = (
            state.get("investigation_round", 0)
            + 1
        )

        system = SystemMessage(
            content=(
                f"{SYSTEM_PROMPT}\n"
                f"Relevant diagnostic domains: {domain_hint}\n"
                f"Investigation round: {round_number}\n"
            )
        )

        messages = state.get("messages", [])
        response = llm_with_tools.invoke(
            [system, *messages]
        )

        return {
            "messages": [response],
            "investigation_round": round_number,
        }

    return investigator


def create_critic(llm):
    """Create the older generic diagnostic critic."""
    structured = llm.with_structured_output(
        DiagnosticCritique
    )

    def critic(state: ODFAgentState) -> dict[str, Any]:
        response = structured.invoke(
            [
                SystemMessage(content=CRITIC_PROMPT),
                *state.get("messages", []),
            ]
        )

        return {
            "critic_decision": response.decision,
            "critic_reason": response.reason,
            "missing_evidence": response.missing_evidence,
        }

    return critic


def create_solution_generator(llm):
    """Create the older generic solution generator."""
    def generate_solution(
        state: ODFAgentState,
    ) -> dict[str, Any]:
        messages = state.get("messages", [])
        critic_feedback = state.get(
            "solution_critic_reason",
            "",
        )
        revision = state.get(
            "solution_revision",
            0,
        )

        response = llm.invoke(
            [
                SystemMessage(content=SOLUTION_PROMPT),
                SystemMessage(
                    content=(
                        f"Solution revision: {revision}.\n"
                        f"Previous solution critic feedback: "
                        f"{critic_feedback or 'None'}"
                    )
                ),
                *messages,
            ]
        )

        content = (
            response.content
            if hasattr(response, "content")
            else str(response)
        )

        return {
            "proposed_solution": (
                content
                or "No remediation plan was generated."
            ),
            "solution_revision": revision + 1,
        }

    return generate_solution


def create_solution_critic(llm):
    """Create the older generic solution critic."""
    structured = llm.with_structured_output(
        SolutionCritique
    )

    def solution_critic(
        state: ODFAgentState,
    ) -> dict[str, Any]:
        proposed = state.get(
            "proposed_solution",
            "",
        )
        messages = state.get(
            "messages",
            [],
        )

        response = structured.invoke(
            [
                SystemMessage(content=SOLUTION_CRITIC_PROMPT),
                SystemMessage(
                    content=f"Evidence transcript:\n{messages}"
                ),
                SystemMessage(
                    content=f"Proposed plan:\n{proposed}"
                ),
            ]
        )

        return {
            "solution_critic_decision": response.decision,
            "solution_critic_reason": response.reason,
        }

    return solution_critic


def finalize_response(
    state: ODFAgentState,
) -> dict[str, Any]:
    """Create the final response from the proposed solution."""
    solution = state.get(
        "proposed_solution",
        "",
    ).strip()

    if not solution:
        solution = (
            "The investigation completed without enough information to "
            "produce a remediation plan."
        )

    return {
        "final_response": solution
    }


# ============================================================================
# Troubleshooting-agent nodes
# ============================================================================


def create_troubleshooting_investigator(llm, tools):
    """
    Create the bounded ReAct investigator used by the troubleshooting graph.

    The model sees the issue class, registered tools, already-collected tools,
    recommended tools, and compact evidence. It does not need the complete
    historical transcript.
    """
    model = llm.bind_tools(tools)
    registered_tools = _tool_names(tools)

    def investigator(state: ODFAgentState) -> dict[str, Any]:
        round_number = (
            state.get("investigation_round", 0)
            + 1
        )

        available_tools = state.get(
            "available_tools",
            registered_tools,
        )

        evidence = state.get(
            "evidence",
            [],
        )

        issue_class = state.get(
            "issue_class",
        )

        if not issue_class:
            issue_class = _issue_from_evidence(evidence)

        recommended_tools = _recommended_tools(
            available_tools=available_tools,
            collected_tools=state.get(
                "collected_tools",
                [],
            ),
            issue_class=issue_class,
        )

        query = state.get("user_query", "").strip()

        if not query:
            for message in state.get("messages", []):
                if isinstance(message, HumanMessage):
                    query = str(message.content).strip()
                    break

        if not query:
            raise ValueError(
                "No user query provided for troubleshooting."
            )

        context = _investigator_context(
            state,
            issue_class,
            recommended_tools,
            available_tools,
        )

        system = SystemMessage(
            content=(
                f"{TROUBLESHOOTING_INVESTIGATOR_PROMPT}\n\n"
                f"Investigation round: {round_number}\n\n"
                f"{context}"
            )
        )

        response = model.invoke(
            [
                system,
                HumanMessage(
                    content=(
                        f"Original user issue:\n{query}\n\n"
                        "Select only the minimum next tool(s) needed."
                    )
                ),
            ]
        )

        return {
            "messages": [response],
            "investigation_round": round_number,
            "available_tools": available_tools,
            "issue_class": issue_class,
            "recommended_tools": recommended_tools,
        }

    return investigator


def create_troubleshooting_evidence_analyst(llm):
    """
    Compress the newest ToolMessage output and persist it into state.

    This fixes the critical failure where the previous evidence analyst could
    return no state update, causing the critic to see an empty evidence set.
    """
    structured = llm.with_structured_output(
        EvidenceSummary
    )

    def evidence_analyst(
        state: ODFAgentState,
    ) -> dict[str, Any]:
        latest_tools = _latest_tool_messages(
            state.get("messages", [])
        )

        if not latest_tools:
            return {
                "evidence": state.get(
                    "evidence",
                    [],
                ),
            }

        latest_evidence_items = [
            {
                "tool": message.name or "unknown",
                "output": str(message.content),
            }
            for message in latest_tools
        ]

        merged_evidence = _merge_unique_evidence(
            state.get("evidence", []),
            latest_evidence_items,
        )

        latest_text = "\n\n".join(
            f"Tool: {item['tool']}\n"
            f"Output:\n{item['output']}"
            for item in latest_evidence_items
        )

        prompt = (
            f"{TROUBLESHOOTING_EVIDENCE_PROMPT}\n\n"
            f"User issue:\n{state.get('user_query', '')}\n\n"
            f"Previous compact summary:\n"
            f"{state.get('investigation_summary', '') or 'None'}\n\n"
            f"Latest OMC observations:\n{latest_text}"
        )

        confirmed_findings: list[str] = []
        summary = ""

        try:
            result = structured.invoke(
                [HumanMessage(content=prompt)]
            )

            summary = result.summary.strip()
            confirmed_findings = [
                item.strip()
                for item in result.confirmed_findings
                if item.strip()
            ]
            unresolved_questions = [
                item.strip()
                for item in result.unresolved_questions
                if item.strip()
            ]

            if confirmed_findings:
                summary += (
                    "\nConfirmed findings:\n- "
                    + "\n- ".join(confirmed_findings)
                )

            if unresolved_questions:
                summary += (
                    "\nUnresolved questions:\n- "
                    + "\n- ".join(unresolved_questions)
                )

        except Exception as exc:
            # Preserve evidence even when the summarizer fails. This prevents
            # a temporary LLM formatting/rate-limit error from erasing state.
            summary = (
                f"Evidence summarization failed: {exc}\n\n"
                f"{latest_text}"
            )

        issue_class = _issue_from_evidence(
            merged_evidence
        )

        collected = list(
            state.get("collected_tools", [])
        )

        for message in latest_tools:
            tool_name = message.name
            if tool_name and tool_name not in collected:
                collected.append(tool_name)

        available = state.get(
            "available_tools",
            [],
        )

        next_recommended = _recommended_tools(
            available_tools=available,
            collected_tools=collected,
            issue_class=issue_class,
        )

        existing_findings = list(
            state.get("findings", [])
        )

        for finding in confirmed_findings:
            if finding not in existing_findings:
                existing_findings.append(finding)

        return {
            "evidence": merged_evidence,
            "investigation_summary": summary.strip(),
            "issue_class": issue_class,
            "findings": existing_findings,
            "collected_tools": collected,
            "last_tool_name": (
                latest_tools[-1].name
                or "unknown"
            ),
            "recommended_tools": next_recommended,
        }

    return evidence_analyst


def create_troubleshooting_critic(llm):
    """
    Review compact evidence while restricting missing_evidence to actual,
    registered, not-yet-collected tools.
    """
    structured = llm.with_structured_output(
        DiagnosticCritique
    )

    def critic(state: ODFAgentState) -> dict[str, Any]:
        available = state.get(
            "available_tools",
            [],
        )
        collected = state.get(
            "collected_tools",
            [],
        )
        evidence = state.get(
            "investigation_summary",
            "",
        )

        prompt = (
            f"{TROUBLESHOOTING_CRITIC_PROMPT}\n\n"
            f"User issue:\n{state.get('user_query', '')}\n\n"
            f"Issue class:\n{state.get('issue_class', 'general')}\n\n"
            f"Evidence:\n{evidence or 'None'}\n\n"
            f"Available tools:\n{available}\n\n"
            f"Already collected tools:\n{collected}\n"
        )

        try:
            response = structured.invoke(
                [HumanMessage(content=prompt)]
            )
        except Exception as exc:
            # Safe stop: do not create an LLM-error-driven investigation loop.
            return {
                "critic_decision": "ready",
                "critic_reason": (
                    "Diagnostic critic invocation failed; stopping the "
                    "investigation safely with the evidence collected so far. "
                    f"Error: {exc}"
                ),
                "missing_evidence": [],
            }

        valid_missing = [
            item
            for item in response.missing_evidence
            if item in available and item not in collected
        ]

        decision = response.decision

        # A request for unavailable/already-collected evidence cannot drive
        # another investigation round.
        if decision == "need_more_evidence" and not valid_missing:
            decision = "ready"

        return {
            "critic_decision": decision,
            "critic_reason": response.reason,
            "missing_evidence": valid_missing,
        }

    return critic


def create_troubleshooting_solution_generator(llm):
    """Generate the remediation plan from compact evidence only."""
    def solution(
        state: ODFAgentState,
    ) -> dict[str, Any]:
        revision = state.get(
            "solution_revision",
            0,
        )

        critic_feedback = state.get(
            "solution_critic_reason",
            "",
        )

        prompt = (
            f"User issue:\n"
            f"{state.get('user_query', '')}\n\n"
            f"Issue class:\n"
            f"{state.get('issue_class', 'general')}\n\n"
            f"Collected evidence:\n"
            f"{state.get('investigation_summary', '') or 'No compact evidence available.'}\n\n"
            f"Confirmed findings:\n"
            f"{state.get('findings', [])}\n\n"
            f"Diagnostic critic reason:\n"
            f"{state.get('critic_reason', '') or 'None'}\n\n"
            f"Solution revision:\n"
            f"{revision}\n\n"
            f"Previous solution critic feedback:\n"
            f"{critic_feedback or 'None'}"
        )

        response = llm.invoke(
            [
                SystemMessage(
                    content=TROUBLESHOOTING_SOLUTION_PROMPT
                ),
                HumanMessage(content=prompt),
            ]
        )

        content = (
            response.content
            if hasattr(response, "content")
            else str(response)
        )

        return {
            "proposed_solution": (
                str(content).strip()
                or "No remediation plan was generated."
            ),
            "solution_revision": revision + 1,
        }

    return solution


def create_troubleshooting_solution_critic(llm):
    """Review the proposed remediation plan against compact evidence."""
    structured = llm.with_structured_output(
        SolutionCritique
    )

    def solution_critic(
        state: ODFAgentState,
    ) -> dict[str, Any]:
        prompt = (
            f"User issue:\n"
            f"{state.get('user_query', '')}\n\n"
            f"Evidence:\n"
            f"{state.get('investigation_summary', '')}\n\n"
            f"Confirmed findings:\n"
            f"{state.get('findings', [])}\n\n"
            f"Proposed remediation plan:\n"
            f"{state.get('proposed_solution', '')}"
        )

        try:
            response = structured.invoke(
                [
                    SystemMessage(
                        content=TROUBLESHOOTING_SOLUTION_CRITIC_PROMPT
                    ),
                    HumanMessage(content=prompt),
                ]
            )
        except Exception as exc:
            return {
                "solution_critic_decision": "pass",
                "solution_critic_reason": (
                    "Solution critic invocation failed; finalizing the "
                    "generated plan without another revision. "
                    f"Error: {exc}"
                ),
            }

        return {
            "solution_critic_decision": response.decision,
            "solution_critic_reason": response.reason,
        }

    return solution_critic


def finalize_troubleshooting_response(
    state: ODFAgentState,
) -> dict[str, Any]:
    """Return the final troubleshooting response."""
    solution = state.get(
        "proposed_solution",
        "",
    ).strip()

    if not solution:
        evidence = state.get(
            "investigation_summary",
            "",
        ).strip()

        if evidence:
            solution = (
                "The investigation completed, but a complete remediation "
                "plan could not be generated.\n\n"
                f"Collected evidence:\n{evidence}"
            )
        else:
            solution = (
                "The investigation completed, but there was not enough "
                "evidence to produce a remediation plan."
            )

    return {
        "final_response": solution
    }
