from __future__ import annotations

from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class ODFAgentState(TypedDict):
    """
    Shared state for the ODF troubleshooting agent.

    Raw OMC command output remains in ToolMessage/audit context.
    Only compact diagnostic information should be persisted in the
    LLM-facing state fields below.
    """

    messages: Annotated[list[AnyMessage], add_messages]

    # Original user problem
    user_query: NotRequired[str]

    # Domain / issue classification
    domains: NotRequired[list[str]]
    issue_class: NotRequired[str]

    # Investigation control
    investigation_round: NotRequired[int]
    max_investigation_rounds: NotRequired[int]

    # Tool control
    available_tools: NotRequired[list[str]]
    collected_tools: NotRequired[list[str]]
    recommended_tools: NotRequired[list[str]]
    last_tool_name: NotRequired[str]

    # Compact evidence
    evidence: NotRequired[list[dict[str, str]]]
    investigation_summary: NotRequired[str]
    findings: NotRequired[list[str]]

    # Diagnosis
    diagnosis: NotRequired[str]
    severity: NotRequired[str]
    confidence: NotRequired[float]

    # Evidence critic
    critic_decision: NotRequired[str]
    critic_reason: NotRequired[str]
    missing_evidence: NotRequired[list[str]]

    # Solution
    proposed_solution: NotRequired[str]
    remediation: NotRequired[list[str]]
    verification_steps: NotRequired[list[str]]

    # Solution review
    solution_critic_decision: NotRequired[str]
    solution_critic_reason: NotRequired[str]
    solution_revision: NotRequired[int]
    max_solution_revisions: NotRequired[int]

    # Final response
    final_response: NotRequired[str]
