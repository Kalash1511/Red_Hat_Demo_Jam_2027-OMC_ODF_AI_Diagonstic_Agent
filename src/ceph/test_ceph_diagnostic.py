from __future__ import annotations

from src.ceph.osd_commands import CephOSDCommands
from src.ceph.osd_parser import (
    parse_health_detail,
    parse_osd_df,
    parse_osd_df_statistics,
    parse_osd_df_total,
    parse_osd_stat,
    parse_osd_tree,
)
from src.ceph.osd_aggregator import (
    CephOSDAggregator,
    aggregate_cluster_data,
)
from src.ceph.osd_diagnostic import CephOSDDiagnostic
from src.ceph.cluster_diagnostic import CephClusterDiagnostic
from src.llm.groq_llm import GroqLLM
from src.omc_client import OMCClient
from src.state.ceph_osd_state import CephState


def main() -> None:

    print("=" * 80)
    print("CEPH DIAGNOSTIC TEST")
    print("=" * 80)

    must_gather_path = input(
        "\nEnter must-gather path: "
    ).strip()

    if not must_gather_path:
        print(
            "\nMust-gather path is required."
        )
        return

    # ------------------------------------------------------------------
    # 1. Initialize OMC client
    # ------------------------------------------------------------------

    print(
        "\n[1] Initializing OMC client"
    )
    print("-" * 80)

    client = OMCClient()
    client.use(must_gather_path)

    commands = CephOSDCommands(
        client
    )

    print(
        "✓ OMC client initialized"
    )

    # ------------------------------------------------------------------
    # 2. Collect Ceph data
    # ------------------------------------------------------------------

    print(
        "\n[2] Collecting Ceph data"
    )
    print("-" * 80)

    print(
        "\nRunning: ceph health detail"
    )
    health_detail_raw = commands.health_detail()

    print(
        "Running: ceph osd stat"
    )
    osd_stat_raw = commands.osd_stat()

    print(
        "Running: ceph osd tree"
    )
    osd_tree_raw = commands.osd_tree()

    print(
        "Running: ceph osd df"
    )
    osd_df_raw = commands.osd_df()

    print(
        "\n✓ Ceph data collection completed"
    )

    # ------------------------------------------------------------------
    # 3. Parse Ceph data
    # ------------------------------------------------------------------

    print(
        "\n[3] Parsing Ceph data"
    )
    print("-" * 80)

    health, health_detail = parse_health_detail(
        health_detail_raw
    )

    osd_stat_data = parse_osd_stat(
        osd_stat_raw
    )

    osd_tree_hosts = parse_osd_tree(
        osd_tree_raw
    )

    osd_df_data = parse_osd_df(
        osd_df_raw
    )

    capacity_data = parse_osd_df_total(
        osd_df_raw
    )

    statistics_data = parse_osd_df_statistics(
        osd_df_raw
    )

    print(
        "✓ Ceph data parsing completed"
    )

    # ------------------------------------------------------------------
    # 4. Aggregate OSD data
    # ------------------------------------------------------------------

    print(
        "\n[4] Aggregating OSD data"
    )
    print("-" * 80)

    aggregator = CephOSDAggregator()

    osd_data = aggregator.aggregate(
        osd_df_data=osd_df_data,
        osd_tree_hosts=osd_tree_hosts,
        osd_stat_data=osd_stat_data,
    )

    print(
        f"✓ OSD aggregation completed"
    )

    print(
        f"  Total OSDs : {osd_data.total_osds}"
    )
    print(
        f"  Up OSDs    : {osd_data.up_osds}"
    )
    print(
        f"  In OSDs    : {osd_data.in_osds}"
    )
    print(
        f"  Down OSDs  : {osd_data.down_osds}"
    )
    print(
        f"  Out OSDs   : {osd_data.out_osds}"
    )

    # ------------------------------------------------------------------
    # 5. Aggregate cluster data
    # ------------------------------------------------------------------

    print(
        "\n[5] Aggregating cluster data"
    )
    print("-" * 80)

    cluster_data = aggregate_cluster_data(
        health=health,
        health_detail=health_detail,
        osd_stat_data=osd_stat_data,
        capacity_data=capacity_data,
        statistics_data=statistics_data,
    )

    print(
        "✓ Cluster aggregation completed"
    )

    print(
        f"  Health     : {cluster_data.health}"
    )
    print(
        f"  Total OSDs : {cluster_data.total_osds}"
    )
    print(
        f"  Up OSDs    : {cluster_data.up_osds}"
    )
    print(
        f"  In OSDs    : {cluster_data.in_osds}"
    )

    # ------------------------------------------------------------------
    # 6. Build Ceph state
    # ------------------------------------------------------------------

    print(
        "\n[6] Building Ceph state"
    )
    print("-" * 80)

    state = CephState(
        must_gather_path=must_gather_path,
        cluster=cluster_data,
        osd_data=osd_data,
        cluster_validated=True,
        osds_validated=True,
    )

    print(
        "✓ Ceph state created"
    )

    # ------------------------------------------------------------------
    # 7. Initialize LLM
    # ------------------------------------------------------------------

    print(
        "\n[7] Initializing LLM"
    )
    print("-" * 80)

    llm_wrapper = GroqLLM()

    llm = llm_wrapper.get_llm()

    print(
        f"✓ LLM initialized"
    )
    print(
        f"  Model: {llm_wrapper.model}"
    )

    # ------------------------------------------------------------------
    # 8. OSD-by-OSD diagnostic
    # ------------------------------------------------------------------

    print(
        "\n" + "=" * 80
    )
    print(
        "OSD-LEVEL CEPH DIAGNOSTIC"
    )
    print(
        "=" * 80
    )

    print(
        "\n[8] Initializing OSD diagnostic"
    )
    print("-" * 80)

    osd_diagnostic = CephOSDDiagnostic(
        llm
    )

    print(
        "✓ OSD diagnostic initialized"
    )

    print(
        "\nRunning OSD diagnostics one OSD at a time..."
    )

    successful_osds = 0
    failed_osds = 0

    for index, osd in enumerate(
        state.osd_data.osds,
        start=1,
    ):

        print(
            "\n" + "-" * 80
        )

        print(
            f"OSD {index}/{len(state.osd_data.osds)}"
        )

        print(
            "-" * 80
        )

        print(
            f"OSD ID       : {osd.id}"
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

        try:

            print(
                "\nSending OSD data to LLM..."
            )

            result = osd_diagnostic.analyze(
                osd
            )

            # Store the LLM result directly
            # on the OSD.
            osd.findings = (
                result.findings
            )

            osd.recommendations = (
                result.recommendations
            )

            successful_osds += 1

            print(
                "\n✓ OSD analysis completed"
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

        except Exception as exc:

            failed_osds += 1

            print(
                "\n✗ OSD analysis failed"
            )

            print(
                f"  OSD ID: {osd.id}"
            )

            print(
                f"  Error : {exc}"
            )

    # ------------------------------------------------------------------
    # OSD diagnostic summary
    # ------------------------------------------------------------------

    print(
        "\n" + "=" * 80
    )
    print(
        "OSD DIAGNOSTIC SUMMARY"
    )
    print(
        "=" * 80
    )

    print(
        f"\nTotal OSDs       : "
        f"{len(state.osd_data.osds)}"
    )

    print(
        f"Successful OSDs  : "
        f"{successful_osds}"
    )

    print(
        f"Failed OSDs      : "
        f"{failed_osds}"
    )

    # ------------------------------------------------------------------
    # 9. Cluster-level diagnostic
    # ------------------------------------------------------------------

    print(
        "\n" + "=" * 80
    )
    print(
        "CLUSTER-LEVEL CEPH DIAGNOSTIC"
    )
    print(
        "=" * 80
    )

    print(
        "\n[9] Initializing cluster diagnostic"
    )
    print("-" * 80)

    cluster_diagnostic = CephClusterDiagnostic(
        llm
    )

    print(
        "✓ Cluster diagnostic initialized"
    )

    print(
        "\n[10] Running cluster-level LLM diagnostic"
    )
    print("-" * 80)

    try:

        cluster_result = cluster_diagnostic.analyze(
            state
        )

        # Store cluster-level LLM results
        # directly in CephState.
        state.cluster.assessment = (
            cluster_result.assessment
        )

        state.cluster.findings = (
            cluster_result.findings
        )

        state.cluster.recommendations = (
            cluster_result.recommendations
        )

        print(
            "\n✓ Cluster analysis completed"
        )

        print(
            "\nAssessment:"
        )

        print(
            f"  {state.cluster.assessment}"
        )

        print(
            "\nCluster Findings:"
        )

        if state.cluster.findings:

            for finding in (
                state.cluster.findings
            ):
                print(
                    f"  - {finding}"
                )

        else:

            print(
                "  None"
            )

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

    except Exception as exc:

        print(
            "\n✗ Cluster analysis failed"
        )

        print(
            f"  Error: {exc}"
        )

    # ------------------------------------------------------------------
    # Final state summary
    # ------------------------------------------------------------------

    print(
        "\n" + "=" * 80
    )
    print(
        "FINAL CEPH STATE"
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
        "\nOSD Counts:"
    )

    print(
        f"  Total : {state.osd_data.total_osds}"
    )

    print(
        f"  Up    : {state.osd_data.up_osds}"
    )

    print(
        f"  In    : {state.osd_data.in_osds}"
    )

    print(
        f"  Down  : {state.osd_data.down_osds}"
    )

    print(
        f"  Out   : {state.osd_data.out_osds}"
    )

    print(
        "\nOSD Diagnostics:"
    )

    print(
        f"  Successful : {successful_osds}"
    )

    print(
        f"  Failed     : {failed_osds}"
    )

    print(
        "\nCluster Assessment:"
    )

    print(
        f"  {state.cluster.assessment or 'Not available'}"
    )

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