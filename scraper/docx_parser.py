
import os
from docx import Document
from docx.shared import RGBColor
from docx.enum.text import WD_UNDERLINE


def parse_docx(file_path: str) -> list[dict]:
    """Parse a .docx file into a list of evidence cards.

    Debate documents follow Verbatim formatting conventions:
    - Heading 1 = Pocket (top-level folder)
    - Heading 2 = Hat (category)
    - Heading 3 = Block (argument block)
    - Heading 4 = Tag (card label / claim)
    - Normal text after tag = cite + card body

    Returns:
        List of card dicts with keys: tag, cite, fullcite, fulltext,
        summary, spoken, markup, pocket, hat, block
    """
    try:
        doc = Document(file_path)
    except Exception as e:
        print(f"Error opening {file_path}: {e}")
        return []

    cards = []
    current = {
        "pocket": "",
        "hat": "",
        "block": "",
    }

    # State machine to collect paragraphs between tags
    tag_text = ""
    card_paragraphs = []
    in_card = False

    for para in doc.paragraphs:
        style_name = (para.style.name or "").lower()

        # Detect heading levels
        if "heading 1" in style_name:
            current["pocket"] = para.text.strip()
            if in_card and tag_text:
                card = _build_card(tag_text, card_paragraphs, current)
                if card:
                    cards.append(card)
            in_card = False
            tag_text = ""
            card_paragraphs = []

        elif "heading 2" in style_name:
            current["hat"] = para.text.strip()
            if in_card and tag_text:
                card = _build_card(tag_text, card_paragraphs, current)
                if card:
                    cards.append(card)
            in_card = False
            tag_text = ""
            card_paragraphs = []

        elif "heading 3" in style_name:
            current["block"] = para.text.strip()
            if in_card and tag_text:
                card = _build_card(tag_text, card_paragraphs, current)
                if card:
                    cards.append(card)
            in_card = False
            tag_text = ""
            card_paragraphs = []

        elif "heading 4" in style_name:
            # New card tag - save previous card if exists
            if in_card and tag_text:
                card = _build_card(tag_text, card_paragraphs, current)
                if card:
                    cards.append(card)
            tag_text = para.text.strip()
            card_paragraphs = []
            in_card = True

        elif in_card:
            card_paragraphs.append(para)

    # Don't forget the last card
    if in_card and tag_text:
        card = _build_card(tag_text, card_paragraphs, current)
        if card:
            cards.append(card)

    return cards


def _build_card(tag: str, paragraphs: list, context: dict) -> dict | None:
    """Build a card dict from a tag and its body paragraphs."""
    if not paragraphs:
        return None

    # First paragraph is usually the cite
    cite = paragraphs[0].text.strip() if paragraphs else ""

    # Build fulltext, summary (underlined), spoken (highlighted), and markup
    fulltext_parts = []
    summary_parts = []
    spoken_parts = []
    markup_parts = [f"<h4><strong>{_escape_html(tag)}</strong></h4>"]

    for para in paragraphs:
        para_text = para.text.strip()
        if not para_text:
            continue

        fulltext_parts.append(para_text)
        para_markup = "<p>"

        for run in para.runs:
            text = run.text
            if not text:
                continue

            is_bold = run.bold
            is_underline = run.underline and run.underline != WD_UNDERLINE.NONE
            is_highlight = run.font.highlight_color is not None

            if is_underline:
                summary_parts.append(text)
            if is_highlight:
                spoken_parts.append(text)

            # Build markup
            escaped = _escape_html(text)
            if is_highlight:
                escaped = f"<mark>{escaped}</mark>"
            if is_underline:
                escaped = f"<u>{escaped}</u>"
            if is_bold:
                escaped = f"<strong>{escaped}</strong>"

            para_markup += escaped

        para_markup += "</p>"
        markup_parts.append(para_markup)

    fulltext = "\n".join(fulltext_parts)
    if not fulltext.strip():
        return None

    return {
        "tag": tag,
        "cite": cite,
        "fullcite": cite,  # Could be expanded with more parsing
        "fulltext": fulltext,
        "summary": " ".join(summary_parts),
        "spoken": " ".join(spoken_parts),
        "markup": "\n".join(markup_parts),
        "pocket": context.get("pocket", ""),
        "hat": context.get("hat", ""),
        "block": context.get("block", ""),
    }


def _escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
