"""Main Streamlit application for CardIt — Debate Evidence Search & Rhetoric Engine."""

import os
import sys
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import hashlib
import streamlit as st
from ui.card_renderer import render_card_markup, estimate_card_height
from ui.filters import render_filters
from ui.download_helper import get_download_info
from ui.theme import inject_theme, render_accent_bar, render_footer
from rhetorifier.page import render_rhetorifier


def _dedup_key(card: dict) -> str:
    """Generate a dedup key from tag and full text of each card."""
    tag = " ".join((card.get("tag") or "").split()).lower()
    fulltext = " ".join((card.get("fulltext") or "").split()).lower()[:500]
    return hashlib.md5(f"{tag}|{fulltext}".encode()).hexdigest()


def _dedup_and_filter(results: list[dict], require_cite: bool) -> tuple[list[dict], dict]:
    """Deduplicate and optionally filter uncited cards. Returns ALL unique results."""
    seen = set()
    unique = []
    removed_no_cite = 0
    removed_dup = 0

    for card in results:
        if require_cite:
            cite = card.get("cite")
            if not cite or cite in ("", "None", "nan"):
                removed_no_cite += 1
                continue

        key = _dedup_key(card)
        if key not in seen:
            seen.add(key)
            unique.append(card)
        else:
            removed_dup += 1

    stats = {
        "total_before": len(results),
        "removed_no_cite": removed_no_cite,
        "removed_dup": removed_dup,
    }
    return unique, stats


st.set_page_config(
    page_title="CardIt",
    page_icon="C",
    layout="wide",
)

# Inject the full custom theme
inject_theme()


@st.cache_resource
def load_search_engine(dataset_name: str, use_reranker: bool = True):
    """Load the search engine (cached per dataset + reranker combo)."""
    from search.search_engine import SearchEngine
    return SearchEngine(dataset_name=dataset_name, use_reranker=use_reranker)


def _search_key(query, filters, use_reranker, require_cite, dataset_name):
    """A hashable key representing the current search parameters."""
    return (query, str(sorted(filters.items())), use_reranker, require_cite, dataset_name)


def main():
    st.title("CardIt")
    render_accent_bar()

    tab_search, tab_rhetorifier = st.tabs(["Search", "Rhetorifier"])

    with tab_rhetorifier:
        render_rhetorifier()

    with tab_search:
        st.caption("Hybrid ML retrieval across millions of debate evidence cards")

        # Sidebar filters
        filters, use_reranker, require_cite, dataset_name = render_filters()

        # Search bar + results per page on the same row
        col1, col2 = st.columns([4, 1])
        with col1:
            query = st.text_input(
                "Search for debate evidence",
                placeholder="e.g., nuclear proliferation increases conflict",
            )
        with col2:
            results_per_page = st.selectbox("Results per page", [10, 20, 50], index=1)

        if not query:
            st.info("Enter a search query above to find debate cards.")
        else:
            # Load engine
            with st.spinner("Loading search engine..."):
                engine = load_search_engine(dataset_name=dataset_name, use_reranker=use_reranker)

            # Only re-run the search when query/filters/dataset change, not on page turns
            key = _search_key(query, filters, use_reranker, require_cite, dataset_name)
            if st.session_state.get("search_key") != key:
                with st.spinner("Searching..."):
                    response = engine.search(
                        query=query,
                        top_k=1000,
                        use_reranker=use_reranker,
                        filters=filters if filters else None,
                    )
                all_results, filter_stats = _dedup_and_filter(response["results"], require_cite)
                st.session_state.search_key = key
                st.session_state.all_results = all_results
                st.session_state.filter_stats = filter_stats
                st.session_state.timings = response["timings"]
                st.session_state.page = 1

            all_results = st.session_state.get("all_results", [])
            filter_stats = st.session_state.get("filter_stats", {})
            timings = st.session_state.get("timings", {})

            # Timing + result count
            timing_parts = [f"{k}: {v*1000:.0f}ms" for k, v in timings.items() if k != "total"]
            timing_str = " | ".join(timing_parts)
            total_unique = len(all_results)
            total_pages = max(1, math.ceil(total_unique / results_per_page))
            st.caption(
                f"{total_unique} unique results in {timings.get('total', 0)*1000:.0f}ms"
                f"  ({timing_str})"
            )

            # Warn when cite filter hides most results
            if require_cite and filter_stats.get("removed_no_cite", 0) > 0:
                pct = filter_stats["removed_no_cite"] / max(filter_stats["total_before"], 1) * 100
                if total_unique < results_per_page:
                    st.info(
                        f"{filter_stats['removed_no_cite']} uncited results hidden "
                        f"({pct:.0f}% of candidates were analytics without author citations). "
                        f'Uncheck **"Cited cards only"** in the sidebar to see all results.'
                    )

            if not all_results:
                st.warning("No results found. Try a different query or adjust filters.")
            else:
                # --- Pagination controls ---
                page = st.session_state.get("page", 1)
                page = min(page, total_pages)
                st.session_state.page = page

                start = (page - 1) * results_per_page
                end = min(start + results_per_page, total_unique)
                page_results = all_results[start:end]

                # Page navigation row
                nav_left, nav_mid, nav_right = st.columns([1, 3, 1])
                with nav_left:
                    if st.button("← Prev", disabled=(page <= 1)):
                        st.session_state.page = page - 1
                        st.rerun()
                with nav_mid:
                    st.markdown(
                        f"<div style='text-align:center; padding-top:6px;'>"
                        f"Page {page} of {total_pages} &nbsp;·&nbsp; results {start+1}–{end} of {total_unique}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with nav_right:
                    if st.button("Next →", disabled=(page >= total_pages)):
                        st.session_state.page = page + 1
                        st.rerun()

                # --- Display current page ---
                for i, card in enumerate(page_results):
                    global_i = start + i
                    with st.expander(
                        f"**{global_i + 1}.** {card.get('tag', 'No tag')[:120]}",
                        expanded=(i < 3),
                    ):
                        meta_cols = st.columns(5)
                        with meta_cols[0]:
                            st.markdown(f"**Cite:** {card.get('cite', 'N/A')}")
                        with meta_cols[1]:
                            st.markdown(f"**Year:** {card.get('year', 'N/A')}")
                        with meta_cols[2]:
                            st.markdown(f"**Tournament:** {card.get('tournament', 'N/A')}")
                        with meta_cols[3]:
                            side = card.get("side", "")
                            side_label = "Aff" if side == "A" else "Neg" if side == "N" else side
                            st.markdown(f"**Side:** {side_label}")
                        with meta_cols[4]:
                            st.markdown(f"**School:** {card.get('schoolDisplayName', 'N/A')}")

                        markup = card.get("markup", "")
                        if markup:
                            height = estimate_card_height(markup)
                            render_card_markup(markup, height=height)
                        else:
                            fulltext = card.get("fulltext", "")
                            if fulltext:
                                st.text(fulltext[:2000])
                            else:
                                st.text("No content available.")

                        download_info = get_download_info(card)
                        if download_info["url"]:
                            st.markdown(
                                f"[⬇ Download {download_info['filename']}]({download_info['url']})"
                            )
                        elif download_info["filepath"]:
                            st.caption(f"Source: {download_info['filepath']}")

                # Bottom page navigation (mirrors the top)
                st.markdown("---")
                bot_left, bot_mid, bot_right = st.columns([1, 3, 1])
                with bot_left:
                    if st.button("← Prev ", disabled=(page <= 1)):
                        st.session_state.page = page - 1
                        st.rerun()
                with bot_mid:
                    st.markdown(
                        f"<div style='text-align:center; padding-top:6px;'>"
                        f"Page {page} of {total_pages}"
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with bot_right:
                    if st.button("Next → ", disabled=(page >= total_pages)):
                        st.session_state.page = page + 1
                        st.rerun()

    render_footer()


if __name__ == "__main__":
    main()
