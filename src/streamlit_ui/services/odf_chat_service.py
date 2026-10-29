from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, cast

from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import BaseTool

from src.agent.odf_chat_agent.odf_chat_graph import (
    build_odf_chat_graph,
    invoke_chat,
)
from src.llm.groq_llm import GroqLLM
from src.omc_client import OMCClient
from src.state.odf_chat_state import ODFChatState
from src.tools.ceph_tools.ceph_tool_registry import (
    build_ceph_command_registry,
)
from src.tools.ceph_tools.command_tool_factory import (
    command_to_tool,
)


class ODFChatService:
    """
    Streamlit application service for the ODF LangGraph chat agent.

    One service instance owns:

    - The OMC client loaded with one must-gather
    - The registered Ceph tools
    - The LLM
    - The compiled LangGraph
    - The LangGraph checkpointer/memory
    """

    def __init__(self, must_gather_path: str) -> None:
        path = must_gather_path.strip()

        if not path:
            raise ValueError("Must-gather path is required.")

        self.must_gather_path = path

        # -------------------------------------------------
        # Create and load OMC client
        # -------------------------------------------------
        self.client = OMCClient()
        self.client.use(path)

        # -------------------------------------------------
        # Build Ceph tools
        # -------------------------------------------------
        self.tools = self._build_tools()

        # -------------------------------------------------
        # Create LLM
        # -------------------------------------------------
        self.llm = GroqLLM().get_llm()

        # -------------------------------------------------
        # Build validated ODF chat graph
        # -------------------------------------------------
        self.graph = build_odf_chat_graph(
            llm=self.llm,
            tools=self.tools,
        )

    @staticmethod
    def _registry_definitions(
        registry: Any,
    ) -> list[Any]:
        """
        Extract CommandDefinition objects from the existing registry.

        Explicit type narrowing is used so Pylance can safely accept
        list(...) for Mapping/Sequence values.
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

            if isinstance(
                value,
                Sequence,
            ) and not isinstance(
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

            if isinstance(
                value,
                Sequence,
            ) and not isinstance(
                value,
                (str, bytes),
            ):
                return list(value)

        if isinstance(
            registry,
            Sequence,
        ) and not isinstance(
            registry,
            (str, bytes),
        ):
            return list(registry)

        raise TypeError(
            "Could not obtain CommandDefinition objects from "
            "OMCCommandRegistry. Update "
            "ODFChatService._registry_definitions() "
            "to match the current registry API."
        )

    def _build_tools(self) -> list[BaseTool]:
        """
        Convert the registered Ceph command definitions into
        LangChain tools.
        """

        registry = build_ceph_command_registry(
            self.client,
        )

        definitions = self._registry_definitions(
            registry,
        )

        tools: list[BaseTool] = []

        for definition in definitions:
            tool = command_to_tool(
                definition,
            )
            tools.append(tool)

        if not tools:
            raise RuntimeError(
                "No OMC Ceph tools were created."
            )

        return tools

    def ask(
        self,
        query: str,
        thread_id: str,
    ) -> ODFChatState:
        """
        Submit a user query to the current LangGraph
        conversation thread.

        The same thread_id preserves the same MemorySaver
        conversation.
        """

        query = query.strip()

        if not query:
            raise ValueError("Chat query is required.")

        thread_id = thread_id.strip()

        if not thread_id:
            raise ValueError("Thread ID is required.")

        return invoke_chat(
            graph=self.graph,
            user_query=query,
            thread_id=thread_id,
            must_gather_path=self.must_gather_path,
        )

    def get_state(
        self,
        thread_id: str,
    ) -> ODFChatState | None:
        """
        Retrieve the checkpointed state for a LangGraph thread.

        LangGraph exposes snapshot.values as a generic dictionary,
        so the value is explicitly narrowed/cast at this service
        boundary into the application's ODFChatState TypedDict.
        """

        thread_id = thread_id.strip()

        if not thread_id:
            return None

        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
            }
        }

        snapshot = self.graph.get_state(
            config,
        )

        values = snapshot.values

        if not isinstance(
            values,
            dict,
        ):
            return None

        return cast(
            ODFChatState,
            values,
        )

    def tool_names(self) -> list[str]:
        """
        Return the registered OMC Ceph tool names.
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

    @staticmethod
    def display_messages(
        state: ODFChatState,
    ) -> list[dict[str, str]]:
        """
        Convert LangChain messages into simple GUI messages.

        Tool messages and AI tool-call-only messages are excluded
        from the normal conversational transcript.
        """

        display: list[dict[str, str]] = []

        messages = state.get(
            "messages",
            [],
        )

        for message in messages:
            if isinstance(
                message,
                ToolMessage,
            ):
                continue

            message_type = getattr(
                message,
                "type",
                "",
            )

            content = str(
                getattr(
                    message,
                    "content",
                    "",
                )
                or ""
            ).strip()

            if not content:
                continue

            if message_type == "human":
                display.append(
                    {
                        "role": "user",
                        "content": content,
                    }
                )

            elif isinstance(
                message,
                AIMessage,
            ):
                display.append(
                    {
                        "role": "assistant",
                        "content": content,
                    }
                )

        return display

    @staticmethod
    def tool_activity(
        state: ODFChatState,
    ) -> list[dict[str, str]]:
        """
        Return tool calls and tool results from the current
        LangGraph state.
        """

        activity: list[dict[str, str]] = []

        messages = state.get(
            "messages",
            [],
        )

        for message in messages:
            tool_calls = getattr(
                message,
                "tool_calls",
                None,
            )

            if tool_calls:
                for call in tool_calls:
                    if not isinstance(
                        call,
                        dict,
                    ):
                        continue

                    name = call.get(
                        "name",
                        "",
                    )

                    args = call.get(
                        "args",
                        {},
                    )

                    activity.append(
                        {
                            "type": "call",
                            "tool": str(name),
                            "content": str(args),
                        }
                    )

            if isinstance(
                message,
                ToolMessage,
            ):
                activity.append(
                    {
                        "type": "result",
                        "tool": str(
                            message.name
                            or "unknown"
                        ),
                        "content": str(
                            message.content
                        ),
                    }
                )

        return activity
