from __future__ import annotations

from collections.abc import Iterable

from src.tools.ceph_tools.command_definition import CommandDefinition


class OMCCommandRegistry:
    """Central registry and domain view for available OMC commands."""

    def __init__(self, commands: Iterable[CommandDefinition]):
        self._commands = {command.name: command for command in commands}

    def get(self, name: str) -> CommandDefinition:
        return self._commands[name]

    def all(self) -> list[CommandDefinition]:
        return list(self._commands.values())

    def for_domain(self, domain: str) -> list[CommandDefinition]:
        return [c for c in self._commands.values() if domain in c.domains]

    def names(self) -> list[str]:
        return list(self._commands.keys())
