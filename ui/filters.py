"""Sidebar filter controls for CardIt."""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
from config.settings import list_available_datasets


def render_filters():
    """Render sidebar filter controls.

    Returns:
        (filters, use_reranker, require_cite, dataset_name)
    """
    st.sidebar.markdown(
        "<h2 style='"
        "background: linear-gradient(135deg, #00e5ff, #7c5cfc); "
        "-webkit-background-clip: text; -webkit-text-fill-color: transparent; "
        "font-size: 1.8rem; margin-bottom: 4px;'>CardIt</h2>",
        unsafe_allow_html=True,
    )
    st.sidebar.caption("Debate Evidence Search")
    st.sidebar.markdown("---")

    st.sidebar.header("Dataset")

    available = list_available_datasets()
    if not available:
        st.sidebar.error("No datasets found. Run the pipeline first.")
        dataset_name = "opencaselist-2020-2022"
    elif len(available) == 1:
        dataset_name = available[0][0]
        st.sidebar.caption(f"Using: **{available[0][1]}**")
    else:
        names = [name for name, _ in available]
        labels = [label for _, label in available]
        idx = st.sidebar.selectbox(
            "Select dataset",
            options=range(len(names)),
            format_func=lambda i: labels[i],
        )
        dataset_name = names[idx]

    st.sidebar.header("Filters")

    filters = {}

    # Year range
    year_range = st.sidebar.slider(
        "Year Range",
        min_value=2010,
        max_value=2026,
        value=(2010, 2026),
    )
    if year_range != (2010, 2026):
        filters["year"] = year_range

    # Event type
    event = st.sidebar.selectbox(
        "Event",
        options=["All", "cx", "ld"],
        format_func=lambda x: {"All": "All Events", "cx": "Policy (CX)", "ld": "LD"}[x],
    )
    if event != "All":
        filters["event"] = event

    # Level
    level = st.sidebar.selectbox(
        "Level",
        options=["All", "college", "hs"],
        format_func=lambda x: {
            "All": "All Levels",
            "college": "College",
            "hs": "High School",
        }[x],
    )
    if level != "All":
        filters["level"] = level

    # Side
    side = st.sidebar.selectbox(
        "Side",
        options=["All", "A", "N"],
        format_func=lambda x: {"All": "Both Sides", "A": "Affirmative", "N": "Negative"}[x],
    )
    if side != "All":
        filters["side"] = side

    # Content filters
    st.sidebar.markdown("---")
    st.sidebar.subheader("Content")
    require_cite = st.sidebar.checkbox("Cited cards only", value=True,
        help="Hide analytics and uncited entries (cards without an author citation)")

    # Re-ranker toggle
    st.sidebar.markdown("---")
    st.sidebar.subheader("Search Settings")
    use_reranker = st.sidebar.checkbox("Use Cross-Encoder Re-ranker", value=True)

    return filters, use_reranker, require_cite, dataset_name
