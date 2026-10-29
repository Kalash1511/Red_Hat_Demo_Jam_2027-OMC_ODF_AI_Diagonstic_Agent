from __future__ import annotations

import streamlit as st


def inject_theme() -> None:
    st.markdown(
        """
        <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2rem;
            max-width: 1500px;
        }
        .metric-card {
            border: 1px solid rgba(128,128,128,0.25);
            border-radius: 12px;
            padding: 12px 16px;
            background: rgba(128,128,128,0.05);
        }
        .status-ok {
            border-left: 5px solid #2e7d32;
            padding: 10px 14px;
            border-radius: 6px;
            background: rgba(46,125,50,0.08);
        }
        .status-err {
            border-left: 5px solid #c62828;
            padding: 10px 14px;
            border-radius: 6px;
            background: rgba(198,40,40,0.08);
        }
        .status-warn {
            border-left: 5px solid #ef6c00;
            padding: 10px 14px;
            border-radius: 6px;
            background: rgba(239,108,0,0.08);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
