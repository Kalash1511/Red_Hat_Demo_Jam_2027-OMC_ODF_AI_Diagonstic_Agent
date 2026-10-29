from __future__ import annotations

from src.state.odf_troubleshoot_chat_state import ODFAgentState


def route_after_investigator(state: ODFAgentState) -> str:
    messages = state.get("messages", [])
    if messages:
        last = messages[-1]
        if getattr(last, "tool_calls", None):
            return "tools"
    return "critic"


def route_after_critic(state: ODFAgentState) -> str:
    decision = state.get("critic_decision", "need_more_evidence")
    rounds = state.get("investigation_round", 0)
    maximum = state.get("max_investigation_rounds", 8)

    if decision == "ready":
        return "solution"

    if rounds >= maximum:
        return "solution"

    return "investigator"


def route_after_solution_critic(state: ODFAgentState) -> str:
    decision = state.get("solution_critic_decision", "pass")
    revisions = state.get("solution_revision", 0)
    maximum = state.get("max_solution_revisions", 2)

    if decision == "revise" and revisions < maximum:
        return "solution"

    return "finalize"
