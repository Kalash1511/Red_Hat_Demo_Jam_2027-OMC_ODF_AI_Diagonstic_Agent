# src/tools/command_tool_factory.py

from __future__ import annotations

from pydantic import BaseModel
from langchain_core.tools import StructuredTool

from src.tools.ceph_tools.command_definition import CommandDefinition


class NoArguments(BaseModel):
    """Schema for OMC commands that take no arguments."""


def command_to_tool(command: CommandDefinition,) -> StructuredTool:
    """Convert an allow-listed OMC command into a LangChain tool."""

    return StructuredTool.from_function(
        func=command.execute,
        name=command.tool_name,
        description=(
            f"{command.description} "
            f"{command.when_to_use}"
        ).strip(),
        args_schema=NoArguments,
    )


def commands_to_tools(commands: list[CommandDefinition],) -> list[StructuredTool]:
    return [
        command_to_tool(command)
        for command in commands
    ]