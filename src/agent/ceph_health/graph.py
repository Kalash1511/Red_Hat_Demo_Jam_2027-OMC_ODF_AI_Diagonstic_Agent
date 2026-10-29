from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from src.ceph.osd_commands import CephOSDCommands
from src.ceph.cluster_diagnostic import CephClusterDiagnostic
from src.ceph.osd_diagnostic import CephOSDDiagnostic
from src.agent.ceph_health.nodes import (
    CephGraphState,
    aggregate_ceph,
    create_cluster_diagnostic,
    create_collect_ceph,
    create_diagnose_current_osd,
    finalize_ceph_report,
    parse_ceph,
    route_after_osd_diagnostic,
    route_after_osd_selection,
    select_next_osd,
    validate_ceph,
)
from src.llm.groq_llm import GroqLLM
from src.omc_client import OMCClient


def build_ceph_graph(must_gather_path: str,):
    """
    Build the complete Ceph diagnostic LangGraph.

    The must-gather path is supplied as graph input.
    There is no dedicated must-gather initialization node.
    """

    # --------------------------------------------------------------
    # Dependencies
    # --------------------------------------------------------------

    client = OMCClient()
    client.use(must_gather_path)

    ceph_commands = CephOSDCommands(
        client
    )


    llm = GroqLLM().get_llm()

    osd_diagnostic = CephOSDDiagnostic(
        llm
    )

    cluster_diagnostic = (
        CephClusterDiagnostic(
            llm
        )
    )

    # --------------------------------------------------------------
    # Create graph nodes
    # --------------------------------------------------------------

    collect_ceph = create_collect_ceph(
        ceph_commands
    )

    diagnose_current_osd = (
        create_diagnose_current_osd(
            osd_diagnostic
        )
    )

    run_cluster_diagnostic = (
        create_cluster_diagnostic(
            cluster_diagnostic
        )
    )

    # --------------------------------------------------------------
    # Build graph
    # --------------------------------------------------------------

    builder = StateGraph(
        CephGraphState
    )

    builder.add_node(
        "collect_ceph",
        collect_ceph,
    )

    builder.add_node(
        "parse_ceph",
        parse_ceph,
    )

    builder.add_node(
        "aggregate_ceph",
        aggregate_ceph,
    )

    builder.add_node(
        "validate_ceph",
        validate_ceph,
    )

    builder.add_node(
        "select_next_osd",
        select_next_osd,
    )

    builder.add_node(
        "diagnose_current_osd",
        diagnose_current_osd,
    )

    builder.add_node(
        "cluster_diagnostic",
        run_cluster_diagnostic,
    )

    builder.add_node(
        "finalize_ceph_report",
        finalize_ceph_report,
    )

    # --------------------------------------------------------------
    # Graph edges
    # --------------------------------------------------------------

    builder.add_edge(
        START,
        "collect_ceph",
    )

    builder.add_edge(
        "collect_ceph",
        "parse_ceph",
    )

    builder.add_edge(
        "parse_ceph",
        "aggregate_ceph",
    )

    builder.add_edge(
        "aggregate_ceph",
        "validate_ceph",
    )

    builder.add_conditional_edges(
        "validate_ceph",
        lambda state: (
            "select_next_osd"
            if not state.validation_errors
            else "finalize_ceph_report"
        ),
        {
            "select_next_osd":
                "select_next_osd",

            "finalize_ceph_report":
                "finalize_ceph_report",
        },
    )

    builder.add_conditional_edges(
        "select_next_osd",
        route_after_osd_selection,
        {
            "diagnose_current_osd":
                "diagnose_current_osd",

            "cluster_diagnostic":
                "cluster_diagnostic",
        },
    )

    builder.add_conditional_edges(
        "diagnose_current_osd",
        route_after_osd_diagnostic,
        {
            "select_next_osd":
                "select_next_osd",

            "cluster_diagnostic":
                "cluster_diagnostic",
        },
    )

    builder.add_edge(
        "cluster_diagnostic",
        "finalize_ceph_report",
    )

    builder.add_edge(
        "finalize_ceph_report",
        END,
    )

    return builder.compile()