from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.agent.ceph_health.graph import build_ceph_graph
from src.agent.ceph_health.nodes import CephGraphState


NodeCallback = Callable[[str], None]


class CephDiagnosticService:
    """Application service around the existing Ceph LangGraph."""

    def __init__(self, must_gather_path: str):
        self.must_gather_path = must_gather_path
        self.graph = build_ceph_graph(
            must_gather_path=must_gather_path
        )

    def initial_state(self) -> CephGraphState:
        return CephGraphState(
            must_gather_path=self.must_gather_path,
        )

    @staticmethod
    def _model_dump(value: Any) -> dict[str, Any] | None:
        """Convert a Pydantic state object to a plain dictionary."""
        if value is None:
            return None

        dump = getattr(value, "model_dump", None)
        if callable(dump):
            data = dump()
            if isinstance(data, dict):
                return data

        if isinstance(value, dict):
            return value

        return None

    @classmethod
    def _normalize_result(
        cls,
        final_state: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Normalize the graph output into a GUI-friendly structure.

        The graph currently exposes the final CephState under
        ``ceph_state``. This method extracts its cluster and OSD data
        while preserving the original graph/debug fields.
        """
        normalized = dict(final_state)

        ceph_state = final_state.get("ceph_state")
        ceph_state_data = cls._model_dump(ceph_state)

        if ceph_state_data is not None:
            normalized["cluster"] = ceph_state_data.get("cluster", {})
            normalized["osd_data"] = ceph_state_data.get("osd_data", {})
            normalized["validation_errors"] = ceph_state_data.get(
                "validation_errors", []
            )
            normalized["cluster_validated"] = ceph_state_data.get(
                "cluster_validated", False
            )
            normalized["osds_validated"] = ceph_state_data.get(
                "osds_validated", False
            )
            normalized["must_gather_path"] = ceph_state_data.get(
                "must_gather_path",
                normalized.get("must_gather_path", self_must_gather_path(final_state)),
            )

        # Defensive fallback for graphs that already expose the GUI fields.
        normalized.setdefault("cluster", {})
        normalized.setdefault("osd_data", {})

        # Convert nested Pydantic models to plain dictionaries if required.
        cluster_data = cls._model_dump(normalized.get("cluster"))
        if cluster_data is not None:
            normalized["cluster"] = cluster_data

        osd_data = cls._model_dump(normalized.get("osd_data"))
        if osd_data is not None:
            normalized["osd_data"] = osd_data

        return normalized

    def run(self, on_node: NodeCallback | None = None) -> dict[str, Any]:
        """Execute the graph and return a normalized GUI-ready state."""
        state = self.initial_state()
        final_state: dict[str, Any] = {}

        for event in self.graph.stream(
            state,
            stream_mode="updates",
        ):
            if not isinstance(event, dict):
                continue

            for node_name, update in event.items():
                if on_node:
                    on_node(str(node_name))

                if isinstance(update, dict):
                    final_state.update(update)

        return self._normalize_result(final_state)


def self_must_gather_path(final_state: dict[str, Any]) -> str:
    """Return the must-gather path already present in the graph state."""
    value = final_state.get("must_gather_path", "")
    return value if isinstance(value, str) else ""
