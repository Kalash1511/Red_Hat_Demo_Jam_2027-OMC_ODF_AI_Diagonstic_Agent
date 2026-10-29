from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

import streamlit as st

from src.streamlit_ui.components.sidebar import render_sidebar
from src.streamlit_ui.components.theme import inject_theme
from src.streamlit_ui.services.odf_troubleshooting_service import (
    ODFTroubleshootingService,
)


st.set_page_config(
    page_title="Troubleshooting OMC ODF Agent",
    page_icon="🛠️",
    layout="wide",
)

inject_theme()
render_sidebar()

st.title(
    "🛠️ ODF Troubleshooting AI Agent"
)

st.caption(
    "Evidence-based, read-only troubleshooting for ODF / Ceph issues"
)


# =============================================================================
# SESSION STATE
# =============================================================================

if "odf_troubleshooting_service" not in st.session_state:
    st.session_state[
        "odf_troubleshooting_service"
    ] = None

if "odf_troubleshooting_result" not in st.session_state:
    st.session_state[
        "odf_troubleshooting_result"
    ] = None

if "odf_troubleshooting_query" not in st.session_state:
    st.session_state[
        "odf_troubleshooting_query"
    ] = ""


# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.subheader(
        "ODF Troubleshooting"
    )

    must_gather_path_input = st.text_input(
        "Must-gather path",
        value=st.session_state.get(
            "must_gather_path",
            "",
        ),
        placeholder=(
            r"A:\OMC_Tool\ocp002pp003215-odf-must-gather-20260811"
        ),
        help=(
            "Windows path to the OMC Ceph/ODF must-gather."
        ),
        key="troubleshooting_must_gather_path",
    )

    must_gather_path = (
        must_gather_path_input or ""
    ).strip()

    st.session_state[
        "must_gather_path"
    ] = must_gather_path

    load_agent = st.button(
        "Load Troubleshooting Agent",
        type="primary",
        use_container_width=True,
        disabled=not must_gather_path,
    )

    new_investigation = st.button(
        "New Investigation",
        use_container_width=True,
        disabled=(
            st.session_state.get(
                "odf_troubleshooting_result"
            )
            is None
        ),
    )


# =============================================================================
# NEW INVESTIGATION
# =============================================================================

if new_investigation:
    st.session_state[
        "odf_troubleshooting_result"
    ] = None

    st.session_state[
        "odf_troubleshooting_query"
    ] = ""

    st.rerun()


# =============================================================================
# LOAD AGENT
# =============================================================================

if load_agent:
    try:
        with st.spinner(
            "Loading must-gather and initializing troubleshooting agent..."
        ):
            service = ODFTroubleshootingService(
                must_gather_path
            )

        st.session_state[
            "odf_troubleshooting_service"
        ] = service

        st.session_state[
            "odf_troubleshooting_result"
        ] = None

        st.success(
            "ODF Troubleshooting Agent is ready."
        )

    except Exception as exc:
        st.error(
            "Failed to initialize the ODF Troubleshooting Agent."
        )
        st.exception(exc)
        st.stop()


# =============================================================================
# SERVICE
# =============================================================================

service = st.session_state.get(
    "odf_troubleshooting_service"
)

if not isinstance(
    service,
    ODFTroubleshootingService,
):
    st.info(
        "Enter a must-gather path in the sidebar and click "
        "**Load Troubleshooting Agent**."
    )

    st.markdown(
        """
        ### What this agent can do

        The troubleshooting agent investigates Ceph Cluster issues using read-only OMC tools.

        #### It provides:

        - Root cause analysis
        - Resolution steps
        - Additional diagnostic checks
        - Verification steps
        - Important cautions and conditions

        """
    )

    st.stop()


# =============================================================================
# AGENT INFORMATION
# =============================================================================

st.success(
    f"Connected to must-gather: `{must_gather_path}`"
)

info_col1, info_col2 = st.columns(2)

with info_col1:
    st.metric(
        "Troubleshooting tools",
        len(
            service.tool_names()
        ),
    )

with info_col2:
    st.metric(
        "Gemini model",
        service.model_name,
    )


with st.expander(
    "Available troubleshooting tools",
    expanded=False,
):
    st.caption(
        "Read-only OMC Ceph tools available during investigation."
    )

    tool_names = service.tool_names()

    columns = st.columns(3)

    for index, tool_name in enumerate(
        tool_names
    ):
        columns[index % 3].code(
            tool_name,
            language="text",
        )


# =============================================================================
# QUERY
# =============================================================================

st.divider()

st.subheader(
    "Describe the issue"
)

query = st.text_area(
    "ODF / Ceph problem",
    value=st.session_state.get(
        "odf_troubleshooting_query",
        "",
    ),
    placeholder=(
        "Example: Why is the Ceph cluster reporting Health issues? What is the root cause and how can I resolve it?"
    ),
    height=120,
)

run_troubleshooting = st.button(
    "🔎 Run Troubleshooting",
    type="primary",
    use_container_width=True,
    disabled=not (
        query or ""
    ).strip(),
)


# =============================================================================
# EXECUTION
# =============================================================================

if run_troubleshooting:
    query = (
        query or ""
    ).strip()

    if not query:
        st.warning(
            "Please describe the ODF / Ceph issue."
        )
        st.stop()

    st.session_state[
        "odf_troubleshooting_query"
    ] = query

    st.session_state[
        "odf_troubleshooting_result"
    ] = None

    progress = st.progress(
        0,
        text="Starting troubleshooting investigation...",
    )

    try:
        events = list(
            service.stream_run(
                query
            )
        )

        progress_events = [
            event
            for event in events
            if event.get(
                "type"
            ) == "progress"
        ]

        total_steps = max(
            len(progress_events),
            1,
        )

        for index, event in enumerate(
            progress_events,
            start=1,
        ):
            node_name = str(
                event.get(
                    "node",
                    "unknown",
                )
            )

            progress.progress(
                min(
                    index / total_steps,
                    1.0,
                ),
                text=(
                    f"Investigating ODF evidence: "
                    f"{node_name}"
                ),
            )

        final_result: dict[str, Any] = {}

        for event in reversed(
            events
        ):
            if event.get(
                "type"
            ) != "complete":
                continue

            result = event.get(
                "result",
                {},
            )

            if isinstance(
                result,
                Mapping,
            ):
                final_result = dict(
                    result
                )

            break

        progress.progress(
            1.0,
            text="Troubleshooting investigation complete.",
        )

        st.session_state[
            "odf_troubleshooting_result"
        ] = final_result

    except Exception as exc:
        st.error(
            "The ODF troubleshooting request failed."
        )
        st.exception(exc)


# =============================================================================
# RESULT
# =============================================================================

result = st.session_state.get(
    "odf_troubleshooting_result"
)

if not isinstance(
    result,
    dict,
):
    st.stop()


st.divider()

st.header(
    "Troubleshooting Resolution"
)


# =============================================================================
# USER ISSUE
# =============================================================================

user_query = st.session_state.get(
    "odf_troubleshooting_query",
    "",
)

if isinstance(
    user_query,
    str,
) and user_query:
    st.markdown(
        f"**Issue:** {user_query}"
    )


# =============================================================================
# ROOT CAUSE + RESOLUTION
# =============================================================================

resolution = (
    service.resolution_documentation(
        result
    )
)

if resolution:
    st.markdown(
        resolution
    )
else:
    st.warning(
        "The troubleshooting agent did not generate a resolution."
    )


# =============================================================================
# READ-ONLY NOTICE
# =============================================================================

st.info(
    "The resolution is generated from the collected ODF / Ceph evidence. "
    "This UI provides guidance only and does not execute remediation commands."
)


# =============================================================================
# OMC TOOL ACTIVITY
# =============================================================================

with st.expander(
    "OMC Tool Activity",
    expanded=False,
):
    st.caption(
        "Optional technical detail showing the read-only OMC Ceph "
        "tools used during the investigation."
    )

    tool_activity = result.get(
        "tool_activity",
        [],
    )

    if (
        isinstance(
            tool_activity,
            list,
        )
        and tool_activity
    ):
        for index, activity in enumerate(
            tool_activity,
            start=1,
        ):
            if not isinstance(
                activity,
                Mapping,
            ):
                st.code(
                    str(activity),
                    language="text",
                )
                continue

            activity_type = str(
                activity.get(
                    "type",
                    "",
                )
            )

            tool_name = str(
                activity.get(
                    "tool",
                    "unknown",
                )
            )

            content = activity.get(
                "content",
                "",
            )

            if activity_type == "call":
                st.markdown(
                    f"**{index}. Tool call:** `{tool_name}`"
                )

                if isinstance(
                    content,
                    Mapping,
                ):
                    st.json(
                        dict(content)
                    )
                else:
                    st.code(
                        str(content),
                        language="text",
                    )

            elif activity_type == "result":
                st.markdown(
                    f"**{index}. Tool result:** `{tool_name}`"
                )

                st.code(
                    str(content),
                    language="text",
                )

    else:
        st.info(
            "No tool activity was captured."
        )


# =============================================================================
# EXPORT
# =============================================================================

with st.expander(
    "Export Resolution",
    expanded=False,
):
    if resolution:
        st.download_button(
            label="Download resolution",
            data=resolution,
            file_name="odf_troubleshooting_resolution.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.download_button(
        label="Download investigation result",
        data=json.dumps(
            result,
            indent=2,
            default=str,
        ),
        file_name="odf_troubleshooting_result.json",
        mime="application/json",
        use_container_width=True,
    )

