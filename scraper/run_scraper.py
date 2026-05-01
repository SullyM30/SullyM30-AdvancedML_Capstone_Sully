import os
import sys
import argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from scraper.api_client import CaselistAPIClient
from scraper.docx_downloader import download_bulk
from scraper.docx_parser import parse_docx
from scraper.export_csv import export_cards_to_csv
from config.settings import SCRAPED_DIR


def run_bulk_scraper(
    caselist_name: str,
    cookie: str,
    output_csv: str = None,
    tournaments: list[str] = None,
):
    """Download the latest weekly ZIP for a caselist and export cards to CSV.

    Args:
        caselist_name: e.g., "ndtceda24" or "hspolicy25"
        cookie: Tabroom caselist_token cookie value.
        output_csv: Path for output CSV.
    """
    client = CaselistAPIClient(cookie=cookie)
    docs_dir = os.path.join(SCRAPED_DIR, "documents")

    # Step 1: Download latest ZIP and extract
    print(f"\n=== Bulk download: {caselist_name} ===")
    downloaded = download_bulk(client, caselist_name, output_dir=docs_dir)

    # Step 2: Filter by tournament name in filename if specified
    if tournaments:
        tourn_lower = [t.lower() for t in tournaments]
        before = len(downloaded)
        downloaded = [
            (name, path) for name, path in downloaded
            if any(t in name.lower() for t in tourn_lower)
        ]
        print(f"\nFiltered to {tournaments}: {len(downloaded)}/{before} files match")

    # Step 3: Parse .docx files into cards
    print(f"\n=== Parsing {len(downloaded)} documents ===")
    all_cards = []
    for name, local_path in downloaded:
        if not local_path.endswith(".docx"):
            continue
        try:
            cards = parse_docx(local_path)
            file_base = os.path.basename(name)
            for card in cards:
                card["filePath"] = name
                # Extract tournament from filename pattern: ...---Tournament-Round.docx
                if not card.get("tournament") and "---" in file_base:
                    tourn_part = file_base.split("---", 1)[-1]
                    tourn_name = tourn_part.rsplit("-Round-", 1)[0] if "-Round-" in tourn_part else tourn_part
                    card["tournament"] = tourn_name.replace("-", " ").replace(".docx", "").strip()
                # Extract side from filename
                if not card.get("side"):
                    name_lower = file_base.lower()
                    if "-aff-" in name_lower:
                        card["side"] = "Aff"
                    elif "-neg-" in name_lower:
                        card["side"] = "Neg"
            all_cards.extend(cards)
        except Exception as e:
            print(f"  Failed to parse {os.path.basename(local_path)}: {e}")

    print(f"\nTotal cards extracted: {len(all_cards)}")

    # Step 4: Export to CSV
    if all_cards:
        if tournaments:
            default_name = f"{caselist_name}_{'_'.join(tournaments)}.csv"
        else:
            default_name = f"{caselist_name}_cards.csv"
        output_path = output_csv or os.path.join(SCRAPED_DIR, default_name)
        export_cards_to_csv(all_cards, output_path=output_path)

    return all_cards


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bulk download debate cards from OpenCaselist")
    parser.add_argument("caselist", help="Caselist name (e.g., hspf25)")
    parser.add_argument("--cookie", required=True, help="Tabroom caselist_token cookie value")
    parser.add_argument("--output", help="Output CSV path")
    parser.add_argument(
        "--tournaments", nargs="+", metavar="NAME",
        help="Only parse files matching these tournament names (case-insensitive substring). "
             "e.g., --tournaments TOC Kentucky"
    )

    args = parser.parse_args()
    run_bulk_scraper(
        caselist_name=args.caselist,
        cookie=args.cookie,
        output_csv=args.output,
        tournaments=args.tournaments,
    )
