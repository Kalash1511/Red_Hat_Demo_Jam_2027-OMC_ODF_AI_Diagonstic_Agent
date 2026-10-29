from __future__ import annotations

from pathlib import Path
from typing import Any


# =============================================================================
# GRAPH VISUALIZATION
# =============================================================================

GRAPH_OUTPUT_DIR = Path("graph_visualization")


def _save_graph_png(
    graph: Any,
    file_name: str,
    display_name: str,
) -> None:
    """
    Generate a PNG representation of a compiled LangGraph.

    Args:
        graph:
            Compiled LangGraph instance.

        file_name:
            PNG file name.

        display_name:
            Human-readable graph name for logging.
    """

    GRAPH_OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_file = GRAPH_OUTPUT_DIR / file_name

    try:
        graph.get_graph().draw_mermaid_png(
            output_file_path=str(output_file)
        )

        print(
            f"[graph] {display_name} visualization saved to: "
            f"{output_file.resolve()}"
        )

    except Exception as exc:
        print(
            f"[graph] Could not generate visualization for "
            f"{display_name}."
        )
        print(
            f"[graph] {type(exc).__name__}: {exc}"
        )


def save_odf_troubleshooting_graph(graph: Any) -> None:
    """
    Save the ODF Troubleshooting Agent graph.
    """

    _save_graph_png(
        graph=graph,
        file_name="odf_troubleshooting_graph.png",
        display_name="ODF Troubleshooting Agent",
    )


def save_odf_chat_graph(graph: Any) -> None:
    """
    Save the ODF Chat Agent graph.
    """

    _save_graph_png(
        graph=graph,
        file_name="odf_chat_graph.png",
        display_name="ODF Chat Agent",
    )


def save_ceph_health_graph(graph: Any) -> None:
    """
    Save the Ceph Health Diagnostic graph.
    """

    _save_graph_png(
        graph=graph,
        file_name="ceph_health_graph.png",
        display_name="Ceph Health Diagnostic Agent",
    )


def save_all_graphs(
    *,
    odf_troubleshooting_graph: Any,
    odf_chat_graph: Any,
    ceph_health_graph: Any,
) -> None:
    """
    Generate PNG visualizations for all three LangGraph agents.
    """

    save_odf_troubleshooting_graph(
        odf_troubleshooting_graph
    )

    save_odf_chat_graph(
        odf_chat_graph
    )

    save_ceph_health_graph(
        ceph_health_graph
    )