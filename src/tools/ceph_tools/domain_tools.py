# src/tools/domain_tools.py

from __future__ import annotations

from src.tools.ceph_tools.command_registry import OMCCommandRegistry
from src.tools.ceph_tools.command_tool_factory import commands_to_tools


def build_domain_tools(registry: OMCCommandRegistry,domains: list[str],):
    """
    Build a deduplicated set of LangChain tools for the
    requested diagnostic domains.
    """

    commands = {}

    for domain in domains:
        for command in registry.for_domain(domain):
            commands[command.name] = command

    return commands_to_tools(
        list(commands.values())
    )