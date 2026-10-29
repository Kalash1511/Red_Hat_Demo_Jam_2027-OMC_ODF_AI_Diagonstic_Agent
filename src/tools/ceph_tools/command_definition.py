from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class CommandDefinition:
    """Metadata and callable implementation for an allow-listed OMC command.

    ``execute`` intentionally accepts arbitrary arguments and return types so
    the registry can contain both no-argument Ceph commands and parameterized
    pod commands, which may return strings or structured diagnostic data.
    Argument validation should be performed by each command method and/or by
    the registry dispatch layer before execution.
    """

    name: str
    description: str
    domains: frozenset[str]
    execute: Callable[..., Any]
    when_to_use: str
    evidence_type: str
    priority: int = 100

    @property
    def tool_name(self) -> str:
        return f"omc_{self.name}"
