
import os
import time
import zipfile
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from scraper.api_client import CaselistAPIClient
from config.settings import SCRAPED_DIR

# Number of parallel download threads.
DOWNLOAD_WORKERS = 1


def _download_one(client: CaselistAPIClient, file_path: str, local_path: str):
    """Download a single document via the API proxy. Returns (file_path, local_path) or raises."""
    content = client.download_document(file_path)
    with open(local_path, "wb") as f:
        f.write(content)
    return (file_path, local_path)


def _download_direct(url: str, local_path: str, session: requests.Session):
    """Download a file from a direct URL (no API rate limiting). Returns local_path or raises."""
    response = session.get(url, timeout=30)
    response.raise_for_status()
    with open(local_path, "wb") as f:
        f.write(response.content)
    return local_path


def download_bulk(
    client: CaselistAPIClient,
    caselist: str,
    output_dir: str = None,
):
    """Download the latest weekly ZIP for a caselist and extract documents.
    Args:
        client: Authenticated API client.
        caselist: Caselist name (e.g., 'hspf25').
        output_dir: Directory to extract documents into.

    Returns:
        List of (file_name, local_path) tuples for all extracted document files.
    """
    output_dir = output_dir or os.path.join(SCRAPED_DIR, "documents")
    zip_dir = os.path.join(SCRAPED_DIR, "zips")
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(zip_dir, exist_ok=True)

    print(f"Fetching bulk download URLs for {caselist}...")
    entries = client.get_bulk_downloads(caselist)
    print(f"Got {len(entries)} weekly archives.")

    if not entries:
        print("No archives available.")
        return []

    # Pick the most recent ZIP
    latest = entries[-1]
    name = latest.get("name", "")
    url = latest.get("url", "")
    print(f"Latest archive: {name}")

    local_zip = os.path.join(zip_dir, name)

    # Download if not cached
    if os.path.exists(local_zip):
        print(f"  Already cached, skipping download.")
    else:
        print(f"  Downloading {name}...")
        session = requests.Session()
        if client.session.cookies:
            session.cookies.update(client.session.cookies)
        _download_direct(url, local_zip, session)
        print(f"  Done.")

    # Extract into documents directory
    print(f"Extracting into {output_dir}...")
    extracted = []
    new_files = 0
    try:
        with zipfile.ZipFile(local_zip, "r") as zf:
            for member in zf.namelist():
                if member.endswith("/"):
                    continue
                base_name = os.path.basename(member)
                if not base_name:
                    continue
                local_path = os.path.join(output_dir, base_name)
                extracted.append((base_name, local_path))
                if not os.path.exists(local_path):
                    data = zf.read(member)
                    with open(local_path, "wb") as f:
                        f.write(data)
                    new_files += 1
    except zipfile.BadZipFile:
        print(f"  Error: corrupt ZIP file: {name}")
        return []

    print(f"  {new_files} new files extracted, {len(extracted)} total documents.")
    return extracted


def download_documents(
    client: CaselistAPIClient,
    file_paths: list[str],
    output_dir: str = None,
    workers: int = DOWNLOAD_WORKERS,
):
    """Download a list of documents in parallel.

    Args:
        client: Authenticated API client.
        file_paths: List of file paths to download.
        output_dir: Directory to save files to.
        workers: Number of parallel download threads.

    Returns:
        List of (file_path, local_path) tuples for successfully downloaded files.
    """
    output_dir = output_dir or os.path.join(SCRAPED_DIR, "documents")
    os.makedirs(output_dir, exist_ok=True)

    # Separate already-downloaded from pending
    downloaded = []
    pending = []
    for file_path in file_paths:
        safe_name = file_path.replace("/", "_").replace("\\", "_")
        local_path = os.path.join(output_dir, safe_name)
        if os.path.exists(local_path):
            downloaded.append((file_path, local_path))
        else:
            pending.append((file_path, local_path))

    if downloaded:
        print(f"  {len(downloaded)} already downloaded, skipping.")

    if pending:
        print(f"  Downloading {len(pending)} documents with {workers} threads...")
        failed = 0
        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {
                executor.submit(_download_one, client, fp, lp): (fp, lp)
                for fp, lp in pending
            }
            with tqdm(total=len(pending), desc="Downloading") as bar:
                for future in as_completed(futures):
                    fp, lp = futures[future]
                    try:
                        result = future.result()
                        downloaded.append(result)
                    except Exception as e:
                        print(f"\n  Failed: {fp}: {e}")
                        failed += 1
                    bar.update(1)

        if failed:
            print(f"  {failed} downloads failed.")

    print(f"Downloaded {len(downloaded)} / {len(file_paths)} documents.")
    return downloaded
