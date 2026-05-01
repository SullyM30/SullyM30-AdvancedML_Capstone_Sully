"""Render debate cards with original formatting in Streamlit."""

import streamlit.components.v1 as components


CARD_CSS = """
body {
    font-family: 'Times New Roman', Times, serif;
    font-size: 14px;
    padding: 12px;
    margin: 0;
    line-height: 1.5;
    color: #000000;
    background-color: #ffffff;
}
h1, h2, h3, h4 {
    font-family: 'Times New Roman', Times, serif;
    margin: 8px 0 4px 0;
    color: #000000;
}
h4 { font-size: 15px; font-weight: bold; }
mark { background-color: #00ffff; color: #000000; padding: 0 1px; }
u { text-decoration: underline; }
strong { font-weight: bold; color: #000000; }
p { margin: 4px 0; }
.cite { color: #333333; font-size: 13px; margin-bottom: 8px; }
"""


def render_card_markup(markup_html: str, height: int = 400):
    """Render a debate card's markup HTML in a Streamlit component."""
    if not markup_html:
        return

    full_html = f"""
    <html>
    <head><style>{CARD_CSS}</style></head>
    <body>{markup_html}</body>
    </html>
    """
    components.html(full_html, height=height, scrolling=True)


def estimate_card_height(markup_html: str) -> int:
    """Estimate a reasonable height for the card iframe based on content length."""
    if not markup_html:
        return 100
    char_count = len(markup_html)
    if char_count < 500:
        return 150
    elif char_count < 2000:
        return 300
    elif char_count < 5000:
        return 450
    else:
        return 600
