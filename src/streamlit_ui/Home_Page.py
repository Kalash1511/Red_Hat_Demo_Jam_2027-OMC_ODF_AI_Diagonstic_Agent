from __future__ import annotations

import streamlit as st

from src.streamlit_ui.components.sidebar import render_sidebar
from src.streamlit_ui.components.theme import inject_theme

st.set_page_config(
    page_title="OMC ODF Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()
render_sidebar()

st.title("OMC ODF AI Agent")
st.caption("Ceph ODF diagnostics and troubleshooting AI agents for OMC must-gather data")

st.markdown(
    """
    ## Welcome

    LangGraph Based AI Agents.

    ### The application is organized around three AI agent experiences:

    - **Ceph Health Diagnostic Agent** — AI Agent configured to return a comprehensive health assessment of the Ceph cluster.
    - **Cluster Chat** — AI Agent configured to answer questions about the Ceph cluster based on the collected evidence.
    - **Troubleshooting Chat** — AI Agent configured for root-cause investigation and guided actions for any troubleshooting needs.
    """
)

col1, col2, col3 = st.columns(3)
with col1:
    st.subheader("🔎 Ceph Health")
    st.write("AI diagnostic workflow against must gather evidence.")
    if st.button("Open Ceph Health", use_container_width=True):
        st.switch_page("pages/01_Ceph_Health.py")

with col2:
    st.subheader("💬 Cluster Chat")
    st.write("AI Agent for querying the collected cluster evidence.")
    if st.button("Open Cluster Chat",use_container_width=True,):
        st.switch_page("pages/02_Cluster_Chat.py")

with col3:
    st.subheader("🛠 Troubleshooting Chat")
    st.write("AI Agent for root-cause investigation and guided actions.")
    if st.button("Open Troubleshooting Chat",use_container_width=True,):
            st.switch_page("pages/03_Troubleshooting_Chat.py")

st.divider()
#st.caption("Architecture: Streamlit UI → agent services → LangGraph / LangChain → OMC + LLM")
