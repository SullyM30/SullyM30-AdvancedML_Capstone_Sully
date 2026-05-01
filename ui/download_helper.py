"""Construct download URLs for original Word documents."""

from config.settings import OPENCASELIST_API_BASE


def get_download_url(opensource_path: str) -> str | None:
    """Construct the download URL for a card's source document."""
    if not opensource_path:
        return None
    return f"{OPENCASELIST_API_BASE}/download?path={opensource_path}"


def get_download_info(card: dict) -> dict:
    """Get download information for a card.

    Returns a dict with 'url', 'filename', and 'filepath'.
    """
    opensource_path = card.get("opensourcePath") or ""
    file_path = card.get("filePath") or ""

    # Use opensourcePath if available, fall back to filePath for scraped cards
    download_path = opensource_path or file_path
    url = get_download_url(download_path) if download_path else None

    # Extract filename from path
    filename = ""
    if download_path:
        filename = download_path.split("/")[-1] if "/" in download_path else download_path

    return {
        "url": url,
        "filename": filename,
        "filepath": file_path,
    }
