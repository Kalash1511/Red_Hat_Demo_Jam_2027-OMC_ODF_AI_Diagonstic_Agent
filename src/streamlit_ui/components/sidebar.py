from __future__ import annotations

import streamlit as st


def render_sidebar() -> None:
    with st.sidebar:
        st.title("LangGraph AI Agent")
        st.caption("Diagnostic center")
        st.divider()

        st.subheader("Agents")
        st.page_link("pages/01_Ceph_Health.py", label="Ceph Health", icon="🔎")
        st.page_link("pages/02_Cluster_Chat.py", label="Cluster Chat", icon="💬")
        st.page_link("pages/03_Troubleshooting_Chat.py", label="Troubleshooting Chat", icon="🛠")

        st.divider()
        st.caption("Future agents can reuse the same services, state, and evidence model.")
