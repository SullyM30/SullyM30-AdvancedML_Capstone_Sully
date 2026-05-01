"""CardIt — custom dark editorial theme for Streamlit."""

import streamlit as st

# Google Fonts imports + full CSS override
_CARDIT_CSS = """
<style>
:root {
    --ci-bg:        #0a0e17;
    --ci-surface:   #131a2b;
    --ci-surface2:  #1a2236;
    --ci-border:    #1e2d4a;
    --ci-accent:    #00e5ff;
    --ci-accent-dim:#0097a7;
    --ci-violet:    #7c5cfc;
    --ci-text:      #e2e8f0;
    --ci-muted:     #7a8ba8;
    --ci-danger:    #ff5252;
    --ci-success:   #00e676;
    --ci-warn:      #ffc107;
    --ci-glow:      0 0 20px rgba(0, 229, 255, 0.15);
    --ci-glow-strong: 0 0 30px rgba(0, 229, 255, 0.25);
}

/* ── Global ────────────────────────────────────────────── */
html, body, .stApp {
    background-color: var(--ci-bg) !important;
    font-family: inherit !important;
    color: var(--ci-text) !important;
}

/* Subtle background grain texture */
.stApp::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.03'/%3E%3C/svg%3E");
    pointer-events: none;
    z-index: 0;
}

/* ── Scrollbar ─────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--ci-bg); }
::-webkit-scrollbar-thumb { background: var(--ci-border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--ci-accent-dim); }

/* ── Header / Title area ───────────────────────────────── */
[data-testid="stAppViewBlockContainer"] > div:first-child h1,
.stMarkdown h1 {
    font-family: inherit !important;
    font-weight: 700 !important;
    font-size: 3rem !important;
    letter-spacing: -0.02em;
    background: linear-gradient(135deg, var(--ci-accent) 0%, var(--ci-violet) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    padding-bottom: 0.2em;
}

.stMarkdown h2, .stMarkdown h3 {
    font-family: inherit !important;
    font-weight: 600 !important;
    color: var(--ci-text) !important;
    letter-spacing: -0.01em;
}

/* ── Tabs ──────────────────────────────────────────────── */
[data-testid="stTabs"] {
    background: transparent;
}

[data-testid="stTabs"] button {
    font-family: inherit !important;
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em;
    color: var(--ci-muted) !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    padding: 12px 24px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stTabs"] button:hover {
    color: var(--ci-text) !important;
    border-bottom-color: var(--ci-accent-dim) !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--ci-accent) !important;
    border-bottom: 2px solid var(--ci-accent) !important;
    text-shadow: 0 0 12px rgba(0, 229, 255, 0.3);
}

/* Tab underline indicator */
[data-testid="stTabs"] [data-baseweb="tab-highlight"] {
    background-color: var(--ci-accent) !important;
    height: 2px !important;
}

[data-testid="stTabs"] [data-baseweb="tab-border"] {
    background-color: var(--ci-border) !important;
}

/* ── Search input ──────────────────────────────────────── */
[data-testid="stTextInput"] > div {
    border-radius: 8px !important;
    overflow: hidden;
}

[data-testid="stTextInput"] input {
    font-family: inherit !important;
    font-size: 1.05rem !important;
    background: var(--ci-surface) !important;
    border: 1px solid var(--ci-border) !important;
    border-radius: 8px !important;
    color: var(--ci-text) !important;
    padding: 14px 18px !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}

[data-testid="stTextInput"] input:focus {
    border-color: var(--ci-accent) !important;
    box-shadow: var(--ci-glow) !important;
}

[data-testid="stTextInput"] input::placeholder {
    color: var(--ci-muted) !important;
    font-style: italic;
}

[data-testid="stTextInput"] label {
    font-family: inherit !important;
    color: var(--ci-muted) !important;
    font-weight: 400 !important;
    font-size: 0.9rem !important;
}

/* ── Sidebar ───────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--ci-surface) !important;
    border-right: 1px solid var(--ci-border) !important;
}

[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    font-family: inherit !important;
    color: var(--ci-accent) !important;
    font-size: 1.3rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em;
    text-transform: uppercase;
    border-bottom: 1px solid var(--ci-border);
    padding-bottom: 8px;
    margin-bottom: 12px;
}

[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stSlider label,
[data-testid="stSidebar"] .stCheckbox label {
    font-family: inherit !important;
    color: var(--ci-muted) !important;
    font-size: 0.85rem !important;
}

[data-testid="stSidebar"] hr {
    border-color: var(--ci-border) !important;
    opacity: 0.5;
}

/* Sidebar subheader */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {
    font-size: 0.9rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--ci-muted) !important;
}

/* ── Selectbox & Slider ────────────────────────────────── */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
    background: var(--ci-surface2) !important;
    border-color: var(--ci-border) !important;
    border-radius: 6px !important;
}

/* Slider thumb */
[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] div[role="slider"] {
    background: var(--ci-accent) !important;
    border-color: var(--ci-accent) !important;
}

/* ── Expanders (search result cards) ───────────────────── */
[data-testid="stExpander"] {
    background: var(--ci-surface) !important;
    border: 1px solid var(--ci-border) !important;
    border-left: 3px solid var(--ci-accent) !important;
    border-radius: 6px !important;
    margin-bottom: 8px !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

[data-testid="stExpander"]:hover {
    border-color: var(--ci-accent-dim) !important;
    box-shadow: var(--ci-glow) !important;
}

[data-testid="stExpander"] summary {
    font-family: inherit !important;
    font-weight: 600 !important;
    color: var(--ci-text) !important;
    padding: 12px 16px !important;
}

[data-testid="stExpander"] summary:hover {
    color: var(--ci-accent) !important;
}

/* ── Buttons ───────────────────────────────────────────── */
.stButton > button {
    font-family: inherit !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    border-radius: 6px !important;
    border: 1px solid var(--ci-accent-dim) !important;
    background: transparent !important;
    color: var(--ci-accent) !important;
    padding: 8px 20px !important;
    transition: all 0.25s ease !important;
    letter-spacing: 0.02em;
}

.stButton > button:hover {
    background: rgba(0, 229, 255, 0.1) !important;
    border-color: var(--ci-accent) !important;
    box-shadow: var(--ci-glow) !important;
    transform: translateY(-1px);
}

.stButton > button:active {
    transform: translateY(0px);
}

/* Disabled buttons */
.stButton > button:disabled {
    border-color: var(--ci-border) !important;
    color: var(--ci-muted) !important;
    opacity: 0.5;
}

/* ── Captions & info text ──────────────────────────────── */
[data-testid="stCaptionContainer"] {
    font-family: inherit !important;
    color: var(--ci-muted) !important;
    font-size: 0.85rem !important;
}

/* ── Alert boxes ───────────────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 6px !important;
    border: 1px solid var(--ci-border) !important;
    font-family: inherit !important;
}

/* ── Metric / card metadata ────────────────────────────── */
[data-testid="stExpander"] .stMarkdown p {
    font-family: inherit !important;
    font-size: 0.9rem !important;
    color: var(--ci-muted) !important;
}

[data-testid="stExpander"] .stMarkdown strong {
    color: var(--ci-accent) !important;
    font-weight: 600 !important;
}

/* ── Pagination center text ────────────────────────────── */
[data-testid="stHorizontalBlock"] .stMarkdown div[style*="text-align:center"] {
    color: var(--ci-muted) !important;
    font-family: inherit !important;
    font-size: 0.85rem !important;
}

/* ── Divider ───────────────────────────────────────────── */
hr {
    border-color: var(--ci-border) !important;
    opacity: 0.4;
}

/* ── File uploader ─────────────────────────────────────── */
[data-testid="stFileUploader"] {
    background: var(--ci-surface) !important;
    border: 2px dashed var(--ci-border) !important;
    border-radius: 8px !important;
    padding: 16px !important;
}

[data-testid="stFileUploader"]:hover {
    border-color: var(--ci-accent-dim) !important;
}

/* ── Text area ─────────────────────────────────────────── */
[data-testid="stTextArea"] textarea {
    background: var(--ci-surface) !important;
    border: 1px solid var(--ci-border) !important;
    border-radius: 6px !important;
    color: var(--ci-text) !important;
    font-family: inherit !important;
}

[data-testid="stTextArea"] textarea:focus {
    border-color: var(--ci-accent) !important;
    box-shadow: var(--ci-glow) !important;
}

/* ── Spinner ───────────────────────────────────────────── */
[data-testid="stSpinner"] {
    color: var(--ci-accent) !important;
}

/* ── Download links ────────────────────────────────────── */
[data-testid="stExpander"] a {
    color: var(--ci-accent) !important;
    text-decoration: none !important;
    font-weight: 600;
    transition: color 0.2s ease;
}

[data-testid="stExpander"] a:hover {
    color: var(--ci-violet) !important;
    text-decoration: underline !important;
}

/* ── Checkbox ──────────────────────────────────────────── */
[data-testid="stCheckbox"] span[data-testid="stCheckbox"] {
    color: var(--ci-accent) !important;
}

/* ── Branded footer ────────────────────────────────────── */
.cardit-footer {
    text-align: center;
    padding: 24px 0 12px 0;
    color: var(--ci-muted);
    font-size: 0.85rem;
    letter-spacing: 0.05em;
    opacity: 0.6;
}

/* ── Animations ────────────────────────────────────────── */
@keyframes fadeSlideIn {
    from { opacity: 0; transform: translateY(8px); }
    to   { opacity: 1; transform: translateY(0); }
}

[data-testid="stExpander"] {
    animation: fadeSlideIn 0.3s ease forwards;
}

/* Staggered animation for result cards */
[data-testid="stExpander"]:nth-child(1) { animation-delay: 0.0s; }
[data-testid="stExpander"]:nth-child(2) { animation-delay: 0.05s; }
[data-testid="stExpander"]:nth-child(3) { animation-delay: 0.1s; }
[data-testid="stExpander"]:nth-child(4) { animation-delay: 0.15s; }
[data-testid="stExpander"]:nth-child(5) { animation-delay: 0.2s; }

/* ── Logo accent bar ───────────────────────────────────── */
.cardit-accent-bar {
    height: 3px;
    background: linear-gradient(90deg, var(--ci-accent) 0%, var(--ci-violet) 50%, transparent 100%);
    border-radius: 2px;
    margin: -8px 0 20px 0;
}
</style>
"""


def inject_theme():
    """Inject the CardIt theme CSS into the Streamlit page."""
    st.markdown(_CARDIT_CSS, unsafe_allow_html=True)


def render_accent_bar():
    """Render the gradient accent bar under the title."""
    st.markdown('<div class="cardit-accent-bar"></div>', unsafe_allow_html=True)


def render_footer():
    """Render the branded footer."""
    st.markdown(
        '<div class="cardit-footer">CardIt &mdash; Debate Evidence Search &amp; Rhetoric Engine</div>',
        unsafe_allow_html=True,
    )
