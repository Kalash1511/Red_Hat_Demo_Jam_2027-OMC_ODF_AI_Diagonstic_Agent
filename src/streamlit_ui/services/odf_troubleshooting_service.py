from __future__ import annotations

import ast
from collections.abc import Iterator, Mapping, Sequence
from pathlib import Path
from pprint import pformat
from typing import Any

from langchain_core.messages import HumanMessage
from langchain_core.tools import BaseTool

from src.agent.odf_troubleshooting_agent.odf_troubleshooting_graph import (
    build_odf_troubleshooting_graph,
)
from src.llm.gemini_llm import GeminiLLM
from src.omc_client import OMCClient
from src.state.odf_troubleshoot_chat_state import ODFAgentState
from src.tools.ceph_tools.ceph_tool_registry import (
    build_ceph_command_registry,
)
from src.tools.ceph_tools.command_tool_factory import command_to_tool


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


class ODFTroubleshootingService:
    """
    Service layer for the Gemini-based ODF troubleshooting agent.

    The service owns:

    - OMC client
    - Read-only Ceph troubleshooting tools
    - Gemini LLM
    - Compiled LangGraph

    The service does not execute remediation commands.
    """

    def __init__(
        self,
        must_gather_path: str,
    ) -> None:
        path = (
            must_gather_path or ""
        ).strip()

        if not path:
            raise ValueError(
                "Must-gather path is required."
            )

        must_gather = Path(path)

        if not must_gather.exists():
            raise ValueError(
                f"Must-gather path does not exist: {path}"
            )

        if not must_gather.is_dir():
            raise ValueError(
                f"Must-gather path is not a directory: {path}"
            )

        self.must_gather_path = str(
            must_gather
        )

        # ---------------------------------------------------------------------
        # OMC
        # ---------------------------------------------------------------------

        self.client = OMCClient()

        self.client.use(
            self.must_gather_path
        )

        # ---------------------------------------------------------------------
        # Ceph troubleshooting tools
        # ---------------------------------------------------------------------

        self.tools = self._build_tools()

        # ---------------------------------------------------------------------
        # Gemini
        # ---------------------------------------------------------------------

        self.llm_wrapper = GeminiLLM()

        self.llm = (
            self.llm_wrapper.get_gemini_llm()
        )

        # ---------------------------------------------------------------------
        # LangGraph
        # ---------------------------------------------------------------------

        self.graph = (
            build_odf_troubleshooting_graph(
                llm=self.llm,
                tools=self.tools,
            )
        )

    # =========================================================================
    # TOOL SETUP
    # =========================================================================

    def _build_tools(self) -> list[BaseTool]:
        """
        Build the restricted troubleshooting tool set.
        """

        registry = build_ceph_command_registry(
            self.client
        )

        tools: list[BaseTool] = []

        for command_name in (
            CORE_TROUBLESHOOTING_COMMANDS
        ):
            tool_definition = registry.get(
                command_name
            )

            if tool_definition is None:
                continue

            tools.append(
                command_to_tool(
                    tool_definition
                )
            )

        if not tools:
            raise RuntimeError(
                "No ODF troubleshooting Ceph tools were created."
            )

        return tools

    # =========================================================================
    # AGENT INFORMATION
    # =========================================================================

    @property
    def model_name(self) -> str:
        """
        Return the configured Gemini model name.
        """

        return str(
            getattr(
                self.llm_wrapper,
                "model",
                "Gemini",
            )
        )

    def tool_names(self) -> list[str]:
        """
        Return the available troubleshooting tool names.
        """

        return [
            tool.name
            for tool in self.tools
            if getattr(
                tool,
                "name",
                None,
            )
        ]

    # =========================================================================
    # INITIAL STATE
    # =========================================================================

    @staticmethod
    def build_initial_state(
        query: str,
    ) -> ODFAgentState:
        """
        Build the initial troubleshooting state.
        """

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

    # =========================================================================
    # CONTENT NORMALIZATION
    # =========================================================================

    @classmethod
    def _content_to_text(
        cls,
        content: Any,
    ) -> str:
        """
        Convert Gemini / LangChain content into plain Markdown text.

        Handles:

        - normal strings
        - content blocks
        - lists of content blocks
        - dictionaries
        - stringified Python representations of content blocks
        """

        if content is None:
            return ""

        if isinstance(
            content,
            str,
        ):
            text = content.strip()

            if not text:
                return ""

            # Gemini content may already have been converted into
            # a string representation such as:
            #
            # "[{'type': 'text', 'text': '...'}]"

            if text.startswith(
                "["
            ) or text.startswith(
                "{"
            ):
                try:
                    parsed = ast.literal_eval(
                        text
                    )
                except (
                    ValueError,
                    SyntaxError,
                ):
                    return text

                if parsed != content:
                    return cls._content_to_text(
                        parsed
                    )

            return text

        if isinstance(
            content,
            Mapping,
        ):
            text = content.get(
                "text"
            )

            if text is not None:
                return cls._content_to_text(
                    text
                )

            nested_content = content.get(
                "content"
            )

            if nested_content is not None:
                return cls._content_to_text(
                    nested_content
                )

            return ""

        if isinstance(
            content,
            Sequence,
        ) and not isinstance(
            content,
            (str, bytes),
        ):
            parts: list[str] = []

            for item in content:
                text = cls._content_to_text(
                    item
                )

                if text:
                    parts.append(
                        text
                    )

            return "\n".join(
                parts
            ).strip()

        return str(
            content
        ).strip()

    # =========================================================================
    # TOOL ACTIVITY
    # =========================================================================

    @classmethod
    def _extract_tool_activity(
        cls,
        messages: Any,
        tool_activity: list[dict[str, Any]],
        fingerprints: set[str],
    ) -> None:
        """
        Extract unique tool calls and tool results from graph messages.
        """

        if not isinstance(
            messages,
            Sequence,
        ) or isinstance(
            messages,
            (str, bytes),
        ):
            return

        for message in messages:
            # -----------------------------------------------------------------
            # Tool calls
            # -----------------------------------------------------------------

            tool_calls = getattr(
                message,
                "tool_calls",
                None,
            )

            if tool_calls:
                for call in tool_calls:
                    if not isinstance(
                        call,
                        Mapping,
                    ):
                        continue

                    tool_name = str(
                        call.get(
                            "name",
                            "unknown",
                        )
                    )

                    args = call.get(
                        "args",
                        {},
                    )

                    call_id = (
                        call.get(
                            "id"
                        )
                        or call.get(
                            "tool_call_id"
                        )
                    )

                    if call_id:
                        fingerprint = (
                            f"call-id|{call_id}"
                        )
                    else:
                        fingerprint = (
                            f"call|"
                            f"{tool_name}|"
                            f"{pformat(args)}"
                        )

                    if fingerprint in fingerprints:
                        continue

                    fingerprints.add(
                        fingerprint
                    )

                    tool_activity.append(
                        {
                            "type": "call",
                            "tool": tool_name,
                            "content": args,
                            "id": (
                                str(
                                    call_id
                                )
                                if call_id
                                else ""
                            ),
                        }
                    )

            # -----------------------------------------------------------------
            # Tool result
            # -----------------------------------------------------------------

            message_type = getattr(
                message,
                "type",
                "",
            )

            if message_type != "tool":
                continue

            tool_name = str(
                getattr(
                    message,
                    "name",
                    None,
                )
                or "unknown"
            )

            tool_call_id = getattr(
                message,
                "tool_call_id",
                None,
            )

            content = getattr(
                message,
                "content",
                "",
            )

            if tool_call_id:
                fingerprint = (
                    f"result-id|{tool_call_id}"
                )
            else:
                fingerprint = (
                    f"result|"
                    f"{tool_name}|"
                    f"{pformat(content)}"
                )

            if fingerprint in fingerprints:
                continue

            fingerprints.add(
                fingerprint
            )

            tool_activity.append(
                {
                    "type": "result",
                    "tool": tool_name,
                    "content": content,
                    "id": (
                        str(
                            tool_call_id
                        )
                        if tool_call_id
                        else ""
                    ),
                }
            )

    # =========================================================================
    # GRAPH EXECUTION
    # =========================================================================

    def stream_run(
        self,
        query: str,
    ) -> Iterator[dict[str, Any]]:
        """
        Execute the troubleshooting LangGraph.

        The UI receives lightweight progress events while the complete
        final state and unique tool activity are accumulated internally.
        """

        query = (
            query or ""
        ).strip()

        if not query:
            raise ValueError(
                "Troubleshooting query is required."
            )

        initial = self.build_initial_state(
            query
        )

        final_state: dict[str, Any] = {}

        tool_activity: list[
            dict[str, Any]
        ] = []

        fingerprints: set[str] = set()

        step_number = 0

        for update in self.graph.stream(
            initial,
            stream_mode="updates",
        ):
            if not isinstance(
                update,
                Mapping,
            ):
                continue

            for node_name, node_update in (
                update.items()
            ):
                step_number += 1

                if isinstance(
                    node_update,
                    Mapping,
                ):
                    for key, value in (
                        node_update.items()
                    ):
                        key_string = str(
                            key
                        )

                        if key_string == "messages":
                            self._extract_tool_activity(
                                messages=value,
                                tool_activity=tool_activity,
                                fingerprints=fingerprints,
                            )

                            existing_messages = (
                                final_state.get(
                                    "messages",
                                    [],
                                )
                            )

                            if not isinstance(
                                existing_messages,
                                list,
                            ):
                                existing_messages = []

                            if isinstance(
                                value,
                                Sequence,
                            ) and not isinstance(
                                value,
                                (str, bytes),
                            ):
                                existing_messages.extend(
                                    value
                                )
                            else:
                                existing_messages.append(
                                    value
                                )

                            final_state[
                                "messages"
                            ] = existing_messages

                        else:
                            final_state[
                                key_string
                            ] = value

                yield {
                    "type": "progress",
                    "step": step_number,
                    "node": str(
                        node_name
                    ),
                }

        final_state[
            "tool_activity"
        ] = tool_activity

        yield {
            "type": "complete",
            "steps": step_number,
            "result": final_state,
        }

    # =========================================================================
    # FINAL RESPONSE
    # =========================================================================

    @classmethod
    def final_response_text(
        cls,
        result: Mapping[str, Any],
    ) -> str:
        """
        Normalize final_response into Markdown text.
        """

        return cls._content_to_text(
            result.get(
                "final_response"
            )
        )

    # =========================================================================
    # USER-FACING DOCUMENTATION
    # =========================================================================

    @classmethod
    def resolution_documentation(
        cls,
        result: Mapping[str, Any],
    ) -> str:
        """
        Build the user-facing troubleshooting document.

        Displayed sections:

        - Root Cause Analysis
        - Resolution Steps
        - Additional Checks
        - Verification Steps
        - Cautions / Conditions

        Excluded sections:

        - Issue Summary
        - Confirmed Findings

        This keeps the UI focused on actionable troubleshooting
        information rather than internal investigation details.
        """

        response = cls.final_response_text(
            result
        )

        if not response:
            return ""

        lines = response.splitlines()

        section_titles = {
            "### 3.": "## Root Cause Analysis",
            "### 4.": "## Resolution Steps",
            "### 5.": "## Additional Checks",
            "### 6.": "## Verification Steps",
            "### 7.": "## Cautions / Conditions",
        }

        sections: list[str] = []

        current_title = ""
        current_lines: list[str] = []

        for line in lines:
            stripped = line.strip()

            matched_title: str | None = None

            for prefix, title in (
                section_titles.items()
            ):
                if stripped.startswith(
                    prefix
                ):
                    matched_title = title
                    break

            if matched_title is not None:
                if current_title:
                    body = "\n".join(
                        current_lines
                    ).strip()

                    if body:
                        sections.append(
                            f"{current_title}\n\n{body}"
                        )

                current_title = matched_title
                current_lines = []

                continue

            if current_title:
                current_lines.append(
                    line
                )

        if current_title:
            body = "\n".join(
                current_lines
            ).strip()

            if body:
                sections.append(
                    f"{current_title}\n\n{body}"
                )

        if sections:
            return "\n\n".join(
                sections
            ).strip()

        return response.strip()
