from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from src.ceph.osd_aggregator import (
    CephOSDAggregator,
    aggregate_cluster_data,
)
from src.ceph.osd_commands import CephOSDCommands
from src.ceph.osd_parser import (
    parse_health_detail,
    parse_osd_df,
    parse_osd_df_statistics,
    parse_osd_df_total,
    parse_osd_stat,
    parse_osd_tree,
)
from src.ceph.cluster_diagnostic import CephClusterDiagnostic
from src.ceph.osd_diagnostic import CephOSDDiagnostic
from src.state.ceph_osd_state import CephState


class CephGraphState(BaseModel):
    """
    LangGraph workflow state for Ceph diagnostics.
    """

    must_gather_path: str = ""

    # Raw OMC output
    health_detail_raw: str = ""
    osd_stat_raw: str = ""
    osd_tree_raw: str = ""
    osd_df_raw: str = ""

    # Parsed data
    parsed_health: str = ""
    parsed_health_detail: str = ""

    parsed_osd_stat: dict[str, int] = Field(
        default_factory=dict
    )

    parsed_osd_tree: dict[int, str] = Field(
        default_factory=dict
    )

    parsed_osd_df: list[dict] = Field(
        default_factory=list
    )

    parsed_capacity: dict = Field(
        default_factory=dict
    )

    parsed_statistics: dict = Field(
        default_factory=dict
    )

    # GUI/report state
    ceph_state: CephState = Field(
        default_factory=CephState
    )

    # Workflow state
    current_osd_index: int = 0

    osd_diagnostic_errors: list[str] = Field(
        default_factory=list
    )

    validation_errors: list[str] = Field(
        default_factory=list
    )

def create_collect_ceph( ceph_commands: CephOSDCommands,):
    """
    Collect all Ceph command output.

    Raw command output is kept in the graph state only long enough
    for parsing.
    """

    def collect_ceph( state: CephGraphState,) -> dict[str, Any]:

        print(
            "\n[collect_ceph] Collecting Ceph data"
        )

        try:
            print(
                "\n[collect_ceph] Running: "
                "ceph health detail"
            )

            health_detail_raw = (
                ceph_commands.health_detail()
            )

            print(
                "[collect_ceph] Running: "
                "ceph osd stat"
            )

            osd_stat_raw = (
                ceph_commands.osd_stat()
            )

            print(
                "[collect_ceph] Running: "
                "ceph osd tree"
            )

            osd_tree_raw = (
                ceph_commands.osd_tree()
            )

            print(
                "[collect_ceph] Running: "
                "ceph osd df"
            )

            osd_df_raw = (
                ceph_commands.osd_df()
            )

        except Exception as exc:

            print(
                f"[collect_ceph] ERROR: {exc}"
            )

            return {
                "validation_errors": [
                    *state.validation_errors,
                    f"Failed to collect Ceph data: {exc}",
                ]
            }

        print(
            "\n[collect_ceph] Ceph data collection completed."
        )

        return {
            "health_detail_raw": health_detail_raw,
            "osd_stat_raw": osd_stat_raw,
            "osd_tree_raw": osd_tree_raw,
            "osd_df_raw": osd_df_raw,
        }

    return collect_ceph


def parse_ceph( state: CephGraphState,) -> dict[str, Any]:
    """
    Parse the collected Ceph command output.

    Existing Ceph parsers are reused without modification.
    """

    print(
        "\n[parse_ceph] Parsing Ceph data"
    )

    errors = list(
        state.validation_errors
    )

    try:
        health, health_detail = (
            parse_health_detail(
                state.health_detail_raw
            )
        )

        osd_stat_data = parse_osd_stat(
            state.osd_stat_raw
        )

        osd_tree_hosts = parse_osd_tree(
            state.osd_tree_raw
        )

        osd_df_data = parse_osd_df(
            state.osd_df_raw
        )

        capacity_data = parse_osd_df_total(
            state.osd_df_raw
        )

        statistics_data = (
            parse_osd_df_statistics(
                state.osd_df_raw
            )
        )

    except Exception as exc:

        print(
            f"[parse_ceph] ERROR: {exc}"
        )

        errors.append(
            f"Failed to parse Ceph data: {exc}"
        )

        return {
            "validation_errors": errors
        }

    print(
        "[parse_ceph] Ceph data parsing completed."
    )

    return {
        "parsed_health": health,
        "parsed_health_detail": health_detail,
        "parsed_osd_stat": osd_stat_data,
        "parsed_osd_tree": osd_tree_hosts,
        "parsed_osd_df": osd_df_data,
        "parsed_capacity": capacity_data,
        "parsed_statistics": statistics_data,
        "validation_errors": errors,
    }


def aggregate_ceph(state: CephGraphState,) -> dict[str, Any]:
    """
    Aggregate parsed OSD and cluster information
    into CephState.
    """

    print(
        "\n[aggregate_ceph] Aggregating Ceph data"
    )

    errors = list(
        state.validation_errors
    )

    try:
        aggregator = CephOSDAggregator()

        osd_data = aggregator.aggregate(
            osd_df_data=state.parsed_osd_df,
            osd_tree_hosts=state.parsed_osd_tree,
            osd_stat_data=state.parsed_osd_stat,
        )

        cluster_data = aggregate_cluster_data(
            health=state.parsed_health,
            health_detail=state.parsed_health_detail,
            osd_stat_data=state.parsed_osd_stat,
            capacity_data=state.parsed_capacity,
            statistics_data=state.parsed_statistics,
        )

        ceph_state = CephState(
            must_gather_path=state.must_gather_path,
            cluster=cluster_data,
            osd_data=osd_data,
            validation_errors=errors,
            cluster_validated=not errors,
            osds_validated=not errors,
        )

    except Exception as exc:

        print(
            f"[aggregate_ceph] ERROR: {exc}"
        )

        errors.append(
            f"Failed to aggregate Ceph data: {exc}"
        )

        return {
            "validation_errors": errors
        }

    print(
        "[aggregate_ceph] Ceph aggregation completed."
    )

    print(
        f"  Total OSDs: "
        f"{ceph_state.osd_data.total_osds}"
    )

    return {
        "ceph_state": ceph_state,
        "current_osd_index": 0,
        "validation_errors": errors,
    }


def validate_ceph(
    state: CephGraphState,
) -> dict[str, Any]:
    """
    Validate the aggregated Ceph state before OSD analysis.
    """

    print(
        "\n[validate_ceph] Validating Ceph state"
    )

    errors = list(
        state.validation_errors
    )

    if not state.ceph_state.osd_data.osds:
        errors.append(
            "No OSDs are available for diagnostic analysis."
        )

    if (
        state.ceph_state.osd_data.total_osds
        < 1
    ):
        errors.append(
            "Ceph OSD count is zero."
        )

    if errors:
        print(
            "[validate_ceph] Validation failed."
        )

    else:
        print(
            "[validate_ceph] Validation successful."
        )

    return {
        "validation_errors": errors,
        "ceph_state": state.ceph_state,
    }


def select_next_osd(
    state: CephGraphState,
) -> dict[str, Any]:
    """
    Select the next OSD for individual diagnosis.
    """

    osds = state.ceph_state.osd_data.osds

    if (
        state.current_osd_index
        >= len(osds)
    ):
        print(
            "\n[select_next_osd] "
            "No OSDs remaining."
        )

        return {}

    osd = osds[
        state.current_osd_index
    ]

    print(
        "\n[select_next_osd] "
        f"Selected OSD: {osd.id}"
    )

    print(
        f"[select_next_osd] "
        f"Progress: "
        f"{state.current_osd_index + 1}/"
        f"{len(osds)}"
    )

    return {}


def route_after_osd_selection(
    state: CephGraphState,
) -> str:
    """
    Route to OSD analysis while OSDs remain.
    Otherwise move to cluster analysis.
    """

    if (
        state.current_osd_index
        < len(
            state.ceph_state.osd_data.osds
        )
    ):
        return "diagnose_current_osd"

    return "cluster_diagnostic"


def create_diagnose_current_osd(
    osd_diagnostic: CephOSDDiagnostic,
):
    """
    Diagnose one OSD at a time.

    The resulting findings and recommendations are stored
    directly on the corresponding OSD.
    """

    def diagnose_current_osd(
        state: CephGraphState,
    ) -> dict[str, Any]:

        osds = (
            state.ceph_state.osd_data.osds
        )

        if (
            state.current_osd_index
            >= len(osds)
        ):
            return {}

        osd = osds[
            state.current_osd_index
        ]

        print(
            "\n[diagnose_current_osd] "
            f"Processing OSD {osd.id}"
        )

        errors = list(
            state.osd_diagnostic_errors
        )

        try:

            print(
                "[diagnose_current_osd] "
                "Sending OSD data to LLM..."
            )

            result = (
                osd_diagnostic.analyze(
                    osd
                )
            )

            osd.findings = (
                result.findings
            )

            osd.recommendations = (
                result.recommendations
            )

            print(
                "[diagnose_current_osd] "
                f"Completed OSD {osd.id}"
            )

            print(
                f"  Findings: "
                f"{len(osd.findings)}"
            )

            print(
                f"  Recommendations: "
                f"{len(osd.recommendations)}"
            )

        except Exception as exc:

            error = (
                f"OSD {osd.id} diagnostic failed: "
                f"{exc}"
            )

            print(
                f"[diagnose_current_osd] "
                f"FAILED: {error}"
            )

            errors.append(error)

        return {
            "ceph_state": state.ceph_state,
            "osd_diagnostic_errors": errors,
            "current_osd_index": (
                state.current_osd_index + 1
            ),
        }

    return diagnose_current_osd


def route_after_osd_diagnostic(
    state: CephGraphState,
) -> str:
    """
    Continue processing OSDs or move to cluster diagnosis.
    """

    if (
        state.current_osd_index
        < len(
            state.ceph_state.osd_data.osds
        )
    ):
        return "select_next_osd"

    return "cluster_diagnostic"


def create_cluster_diagnostic(
    cluster_diagnostic: CephClusterDiagnostic,
):
    """
    Generate the overall cluster diagnostic.

    The cluster diagnostic itself receives only OSD ID,
    findings and recommendations.
    """

    def run_cluster_diagnostic(state: CephGraphState,) -> dict[str, Any]:

        print(
            "\n[cluster_diagnostic] "
            "Running cluster-level diagnostic"
        )

        try:

            result = (
                cluster_diagnostic.analyze(
                    state.ceph_state
                )
            )

            state.ceph_state.cluster.assessment = (
                result.assessment
            )

            state.ceph_state.cluster.findings = (
                result.findings
            )

            state.ceph_state.cluster.recommendations = (
                result.recommendations
            )

            print(
                "[cluster_diagnostic] "
                "Cluster analysis completed."
            )

        except Exception as exc:

            error = (
                f"Cluster diagnostic failed: "
                f"{exc}"
            )

            print(
                f"[cluster_diagnostic] "
                f"ERROR: {error}"
            )

            return {
                "validation_errors": [
                    *state.validation_errors,
                    error,
                ],
                "ceph_state": state.ceph_state,
            }

        return {
            "ceph_state": state.ceph_state
        }

    return run_cluster_diagnostic


def finalize_ceph_report(state: CephGraphState,) -> dict[str, Any]:
    """
    Finalize the GUI-ready CephState.

    No transformation is performed here. The structured
    CephState is already the report consumed by the GUI.
    """

    print(
        "\n[finalize_ceph_report] "
        "Ceph report finalized."
    )

    return {
        "ceph_state": state.ceph_state
    }