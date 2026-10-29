from __future__ import annotations

import streamlit as st

from src.streamlit_ui.components.ceph_view import (
    render_cluster_summary,
    render_findings,
    render_full_state,
    render_osds,
)
from src.streamlit_ui.components.sidebar import render_sidebar
from src.streamlit_ui.components.theme import inject_theme
from src.streamlit_ui.services.ceph_service import CephDiagnosticService


st.set_page_config(
    page_title="Ceph Cluster Diagnostic Agent",
    page_icon="🔎",
    layout="wide",
)

inject_theme()
render_sidebar()

st.title("🔎 Ceph Cluster Diagnostic Agent")
st.caption(
    "Run the complete Ceph diagnostic LangGraph AI workflow"
)

with st.sidebar:
    st.subheader("Diagnostic Input")

    must_gather_path_input = st.text_input(
        "Must-gather path",
        value=st.session_state.get(
            "must_gather_path",
            "",
        ),
        placeholder=(
            r"A:\OMC_Tool\odf_must_gather\health_err_must_gather"
        ),
        help="Windows path to the OMC Ceph/ODF must-gather.",
    )

    must_gather_path = (
        must_gather_path_input or ""
    ).strip()

    st.session_state["must_gather_path"] = must_gather_path

    run_diagnostic = st.button(
        "Run Ceph Diagnostic",
        type="primary",
        width="stretch",
        disabled=not must_gather_path,
    )

    st.divider()

    if st.session_state.get("graph_result"):
        st.success("Diagnostic result loaded")

if not must_gather_path:
    st.info(
        "Enter a must-gather path in the sidebar "
        "and run the diagnostic."
    )
    st.stop()

if run_diagnostic:
    progress_box = st.empty()
    status_box = st.status(
        "Starting Ceph diagnostic...",
        expanded=True,
    )
    completed_nodes: list[str] = []

    def on_node(node_name: str) -> None:
        completed_nodes.append(node_name)
        progress_box.info(
            f"Completed: `{node_name}`"
        )
        status_box.write(
            f"✓ `{node_name}`"
        )

    try:
        with st.spinner(
            "Executing Ceph diagnostic graph..."
        ):
            service = CephDiagnosticService(
                must_gather_path
            )
            result = service.run(
                on_node=on_node
            )

        st.session_state["graph_result"] = result
        st.session_state["completed_nodes"] = completed_nodes

        status_box.update(
            label="Ceph diagnostic completed",
            state="complete",
        )
        progress_box.success(
            "Diagnostic completed successfully."
        )

    except Exception as exc:
        status_box.update(
            label="Ceph diagnostic failed",
            state="error",
        )
        st.exception(exc)
        st.stop()

result = st.session_state.get("graph_result")

if not isinstance(result, dict):
    st.info(
        "Run the diagnostic to see the cluster "
        "assessment and OSD details."
    )
    st.stop()

cluster = result.get("cluster")
osd_data = result.get("osd_data")

if not isinstance(cluster, dict):
    cluster = {}

if not isinstance(osd_data, dict):
    osd_data = {}

st.divider()
render_cluster_summary(cluster)

st.divider()
render_findings(cluster)

st.divider()
render_osds(osd_data)

st.divider()
render_full_state(result)
