from __future__ import annotations

from src.agent.ceph_health.nodes import CephGraphState
from src.agent.ceph_health.graph import build_ceph_graph
from pathlib import Path

# =============================================================================
# GRAPH VISUALIZATION
# =============================================================================

def _save_graph_png(graph) -> None:
    """
    Generate a PNG representation of the compiled LangGraph.

    The PNG is saved in a dedicated graph_visualization directory.
    """

    output_dir = Path("graph_visualization")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "ceph_health_graph.png"

    try:
        graph.get_graph().draw_mermaid_png(
            output_file_path=str(output_file)
        )

        print(
            f"[graph] Graph visualization saved to: "
            f"{output_file.resolve()}"
        )

    except Exception as exc:
        print(
            "[graph] Could not generate graph PNG."
        )
        print(
            f"[graph] {type(exc).__name__}: {exc}"
        )



def main() -> None:

    print("=" * 80)
    print("CEPH DIAGNOSTIC LANGGRAPH TEST")
    print("=" * 80)

    must_gather_path = input(
        "\nEnter must-gather path: "
    ).strip()

    if not must_gather_path:
        print(
            "\nMust-gather path is required."
        )
        return

    # --------------------------------------------------------------
    # Build graph
    # --------------------------------------------------------------

    print(
        "\n[1] Building Ceph diagnostic graph"
    )
    print("-" * 80)

    try:

        graph = build_ceph_graph(
            must_gather_path
        )

        print(
            "✓ Ceph diagnostic graph created."
        )

    except Exception as exc:

        print(
            "\n✗ Failed to build Ceph graph."
        )

        print(
            f"  Error: {exc}"
        )

        return


    # -------------------------------------------------------------------------
    # GRAPH VISUALIZATION
    # -------------------------------------------------------------------------


    _save_graph_png(
        graph
    )
    # --------------------------------------------------------------
    # Execute graph
    # --------------------------------------------------------------

    print(
        "\n[2] Executing Ceph diagnostic graph"
    )
    print("-" * 80)

    try:

        result = graph.invoke(
            CephGraphState(
                must_gather_path=must_gather_path
            )
        )

    except Exception as exc:

        print(
            "\n✗ Ceph diagnostic graph failed."
        )

        print(
            f"  Error: {exc}"
        )

        return

    # --------------------------------------------------------------
    # Get final GUI-ready state
    # --------------------------------------------------------------

    state = result.get(
        "ceph_state"
    )

    if state is None:

        print(
            "\n✗ Graph completed but "
            "CephState was not returned."
        )

        return

    # --------------------------------------------------------------
    # Final summary
    # --------------------------------------------------------------

    print(
        "\n" + "=" * 80
    )

    print(
        "CEPH DIAGNOSTIC RESULT"
    )

    print(
        "=" * 80
    )

    print(
        "\nCluster Health:"
    )

    print(
        f"  {state.cluster.health}"
    )

    print(
        "\nCluster Assessment:"
    )

    print(
        f"  {state.cluster.assessment or 'Not available'}"
    )

    print(
        "\nOSD Counts:"
    )

    print(
        f"  Total : "
        f"{state.osd_data.total_osds}"
    )

    print(
        f"  Up    : "
        f"{state.osd_data.up_osds}"
    )

    print(
        f"  In    : "
        f"{state.osd_data.in_osds}"
    )

    print(
        f"  Down  : "
        f"{state.osd_data.down_osds}"
    )

    print(
        f"  Out   : "
        f"{state.osd_data.out_osds}"
    )

    # --------------------------------------------------------------
    # Cluster findings
    # --------------------------------------------------------------

    print(
        "\nCluster Findings:"
    )

    if state.cluster.findings:

        for finding in state.cluster.findings:
            print(
                f"  - {finding}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------------
    # Cluster recommendations
    # --------------------------------------------------------------

    print(
        "\nCluster Recommendations:"
    )

    if state.cluster.recommendations:

        for recommendation in (
            state.cluster.recommendations
        ):
            print(
                f"  - {recommendation}"
            )

    else:

        print(
            "  None"
        )

    # --------------------------------------------------------------
    # OSD results
    # --------------------------------------------------------------

    print(
        "\n" + "=" * 80
    )

    print(
        "OSD DIAGNOSTIC RESULTS"
    )

    print(
        "=" * 80
    )

    for osd in state.osd_data.osds:

        print(
            f"\nOSD {osd.id}"
        )

        print(
            "-" * 40
        )

        print(
            f"Host         : {osd.host}"
        )

        print(
            f"Status       : {osd.status}"
        )

        print(
            f"Percent Used : {osd.percent_used}%"
        )

        print(
            f"Variance     : {osd.variance}"
        )

        print(
            f"PGs          : {osd.pgs}"
        )

        print(
            "\nFindings:"
        )

        if osd.findings:

            for finding in osd.findings:
                print(
                    f"  - {finding}"
                )

        else:

            print(
                "  None"
            )

        print(
            "\nRecommendations:"
        )

        if osd.recommendations:

            for recommendation in (
                osd.recommendations
            ):
                print(
                    f"  - {recommendation}"
                )

        else:

            print(
                "  None"
            )

    # --------------------------------------------------------------
    # GUI-ready JSON
    # --------------------------------------------------------------

    print(
        "\n" + "=" * 80
    )

    print(
        "GUI-READY CEPH STATE"
    )

    print(
        "=" * 80
    )

    print(
        state.model_dump_json(
            indent=2
        )
    )

    print(
        "\n" + "=" * 80
    )

    print(
        "CEPH DIAGNOSTIC COMPLETED"
    )

    print(
        "=" * 80
    )


if __name__ == "__main__":
    main()