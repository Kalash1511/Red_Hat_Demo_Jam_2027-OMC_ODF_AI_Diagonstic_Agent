from __future__ import annotations

import uuid

import streamlit as st

from src.streamlit_ui.components.sidebar import render_sidebar
from src.streamlit_ui.components.theme import inject_theme
from src.streamlit_ui.services.odf_chat_service import ODFChatService


st.set_page_config(
    page_title="CEPH Cluster Chat AI Agent",
    page_icon="💬",
    layout="wide",
)

inject_theme()
render_sidebar()

st.title("💬 ODF Cluster Chat")

st.caption(
    "Conversational LangGraph agent for read-only OMC Ceph / ODF analysis"
)


# ---------------------------------------------------------------------------
# Session initialization
# ---------------------------------------------------------------------------

if "odf_chat_thread_id" not in st.session_state:
    st.session_state["odf_chat_thread_id"] = str(
        uuid.uuid4()
    )

if "odf_chat_service" not in st.session_state:
    st.session_state["odf_chat_service"] = None

if "odf_chat_state" not in st.session_state:
    st.session_state["odf_chat_state"] = None


# ---------------------------------------------------------------------------
# Sidebar configuration
# ---------------------------------------------------------------------------

with st.sidebar:
    st.subheader("Cluster Chat")

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
            "Windows path to the OMC Ceph/ODF must-gather. "
            "The chat agent uses the read-only OMC Ceph command registry."
        ),
    )

    must_gather_path = (
        must_gather_path_input or ""
    ).strip()

    st.session_state["must_gather_path"] = must_gather_path

    configure_chat = st.button(
        "Load ODF Chat",
        type="primary",
        use_container_width=True,
        disabled=not must_gather_path,
    )

    clear_chat = st.button(
        "New Chat Session",
        use_container_width=True,
        disabled=(
            st.session_state.get(
                "odf_chat_service"
            )
            is None
        ),
    )


# ---------------------------------------------------------------------------
# Clear / configure
# ---------------------------------------------------------------------------

if clear_chat:
    st.session_state["odf_chat_thread_id"] = str(
        uuid.uuid4()
    )
    st.session_state["odf_chat_state"] = None
    st.rerun()


if configure_chat:
    try:
        with st.spinner(
            "Loading must-gather and initializing ODF LangGraph..."
        ):
            service = ODFChatService(
                must_gather_path
            )

        st.session_state["odf_chat_service"] = service

        st.session_state["odf_chat_thread_id"] = str(
            uuid.uuid4()
        )

        st.session_state["odf_chat_state"] = None

        st.success(
            "ODF Cluster Chat is ready."
        )

    except Exception as exc:
        st.error(
            "Failed to initialize ODF Cluster Chat."
        )
        st.exception(exc)
        st.stop()


# ---------------------------------------------------------------------------
# Retrieve configured service
# ---------------------------------------------------------------------------

service = st.session_state.get(
    "odf_chat_service"
)

if not isinstance(
    service,
    ODFChatService,
):
    st.info(
        "Enter a must-gather path in the sidebar and click "
        "**Load ODF Chat**."
    )

    st.markdown(
        """
        ### What this chat can answer

        The agent can query the registered read-only OMC Ceph tools for:

        - cluster health details
        - OSD topology, and individual OSD details
        - OSD capacity, utilization and performance information
        - Ceph Manager state, modules, and services
        - CRUSH classes, rules, tunables, and weight configuration

        ### Example questions

        - What is the Ceph cluster health?
        - How many OSDs are present in the cluster?
        """
    )

    st.stop()


# ---------------------------------------------------------------------------
# Restore current LangGraph state after Streamlit reruns
# ---------------------------------------------------------------------------

thread_id = st.session_state[
    "odf_chat_thread_id"
]

current_state = service.get_state(
    thread_id
)

if current_state is not None:
    st.session_state["odf_chat_state"] = current_state
else:
    stored_state = st.session_state.get(
        "odf_chat_state"
    )

    if stored_state is not None:
        current_state = stored_state


# ---------------------------------------------------------------------------
# Header / status
# ---------------------------------------------------------------------------

st.success(
    f"Connected to must-gather: `{must_gather_path}`"
)

st.caption(
    f"LangGraph session: `{thread_id}` · "
    f"{len(service.tool_names())} read-only Ceph tools registered"
)


with st.expander(
    "Registered OMC Ceph tools",
    expanded=False,
):
    tool_names = service.tool_names()

    columns = st.columns(3)

    for index, tool_name in enumerate(
        tool_names
    ):
        columns[index % 3].code(
            tool_name,
            language="text",
        )


# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------

if current_state is not None:
    for message in service.display_messages(
        current_state
    ):
        with st.chat_message(
            message["role"]
        ):
            st.markdown(
                message["content"]
            )


# ---------------------------------------------------------------------------
# Tool activity
# ---------------------------------------------------------------------------

if current_state is not None:
    activity = service.tool_activity(
        current_state
    )

    if activity:
        with st.expander(
            "OMC tool activity",
            expanded=False,
        ):
            for item in activity:
                if item["type"] == "call":
                    st.markdown(
                        f"**Tool call:** `{item['tool']}`"
                    )

                    st.code(
                        item["content"],
                        language="json",
                    )

                else:
                    st.markdown(
                        f"**Tool result:** `{item['tool']}`"
                    )

                    st.code(
                        item["content"],
                        language="text",
                    )


# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------

query = st.chat_input(
    "Ask about the ODF / Ceph cluster..."
)


if query:
    with st.chat_message("user"):
        st.markdown(query)

    try:
        with st.chat_message("assistant"):
            with st.spinner(
                "Analyzing the ODF cluster..."
            ):
                result = service.ask(
                    query=query,
                    thread_id=thread_id,
                )

            st.session_state["odf_chat_state"] = result

            messages = result.get(
                "messages",
                [],
            )

            response_content = ""

            for message in reversed(
                messages
            ):
                message_type = getattr(
                    message,
                    "type",
                    "",
                )

                content = getattr(
                    message,
                    "content",
                    "",
                )

                if (
                    message_type == "ai"
                    and content
                ):
                    response_content = str(
                        content
                    )
                    break

            if response_content:
                st.markdown(
                    response_content
                )
            else:
                st.warning(
                    "The agent completed without a textual response."
                )

    except Exception as exc:
        st.error(
            "The ODF chat request failed."
        )
        st.exception(exc)

