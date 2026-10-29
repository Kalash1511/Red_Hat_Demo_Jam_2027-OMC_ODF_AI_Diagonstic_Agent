from __future__ import annotations

import json
from typing import Any

import streamlit as st


def _health_class(health: str) -> str:
    if health == "HEALTH_OK":
        return "status-ok"
    if health == "HEALTH_WARN":
        return "status-warn"
    if health == "HEALTH_ERR":
        return "status-err"
    return "status-warn"


def render_cluster_summary(cluster: dict[str, Any]) -> None:
    health = str(cluster.get("health", "UNKNOWN"))
    assessment = str(cluster.get("assessment", ""))

    st.markdown(
        f'<div class="{_health_class(health)}"><strong>{health}</strong><br>{assessment}</div>',
        unsafe_allow_html=True,
    )

    st.write("")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("OSDs", cluster.get("total_osds", 0))
    c2.metric("Up", cluster.get("up_osds", 0))
    c3.metric("In", cluster.get("in_osds", 0))
    c4.metric("Used", f"{cluster.get('overall_percent_used', 0)}%")
    c5.metric("Variance", f"{cluster.get('min_variance', 0)} – {cluster.get('max_variance', 0)}")

    with st.expander("Ceph health detail", expanded=health == "HEALTH_ERR"):
        st.code(cluster.get("health_detail", "No health detail available."), language="text")


def render_findings(cluster: dict[str, Any]) -> None:
    findings = cluster.get("findings") or []
    recommendations = cluster.get("recommendations") or []

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Cluster Findings")
        if findings:
            for finding in findings:
                st.warning(finding)
        else:
            st.success("No cluster-level findings.")

    with col2:
        st.subheader("Recommendations")
        if recommendations:
            for recommendation in recommendations:
                st.info(recommendation)
        else:
            st.success("No cluster-level recommendations.")


def render_osds(osd_data: dict[str, Any]) -> None:
    osds = osd_data.get("osds") or []

    st.subheader("OSD Overview")
    st.dataframe(
        [
            {
                "OSD": osd.get("id"),
                "Host": osd.get("host"),
                "Status": osd.get("status"),
                "Class": osd.get("device_class"),
                "Used %": osd.get("percent_used"),
                "Variance": osd.get("variance"),
                "PGs": osd.get("pgs"),
                "Capacity": osd.get("size"),
                "Available": osd.get("avail"),
            }
            for osd in osds
        ],
        use_container_width=True,
        hide_index=True,
    )

    for osd in osds:
        label = f"OSD {osd.get('id')} · {osd.get('host')} · {osd.get('status')}"
        with st.expander(label):
            left, right = st.columns(2)
            with left:
                st.write(f"**Device class:** {osd.get('device_class')}")
                st.write(f"**Size:** {osd.get('size')}")
                st.write(f"**Raw use:** {osd.get('raw_use')}")
                st.write(f"**Available:** {osd.get('avail')}")
                st.write(f"**PGs:** {osd.get('pgs')}")
            with right:
                st.write(f"**Data:** {osd.get('data')}")
                st.write(f"**OMAP:** {osd.get('omap')}")
                st.write(f"**Meta:** {osd.get('meta')}")
                st.write(f"**Percent used:** {osd.get('percent_used')}%")
                st.write(f"**Variance:** {osd.get('variance')}")

            findings = osd.get("findings") or []
            recommendations = osd.get("recommendations") or []

            st.markdown("**Findings**")
            if findings:
                for finding in findings:
                    st.warning(finding)
            else:
                st.success("No findings.")

            st.markdown("**Recommendations**")
            if recommendations:
                for recommendation in recommendations:
                    st.info(recommendation)
            else:
                st.caption("None")


def render_full_state(state: dict[str, Any]) -> None:
    with st.expander("JSON Details", expanded=False):
        st.json(state)

    st.download_button(
        label="Download diagnostic JSON",
        data=json.dumps(state, indent=2, default=str),
        file_name="ceph_diagnostic_report.json",
        mime="application/json",
    )
