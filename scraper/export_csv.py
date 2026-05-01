

import os
import csv
from config.settings import SCRAPED_DIR


CSV_COLUMNS = [
    "tag", "cite", "fullcite", "fulltext", "summary", "spoken",
    "markup", "pocket", "hat", "block", "filePath", "source_file",
    "tournament", "round", "side",
]


def export_cards_to_csv(
    cards: list[dict],
    output_path: str = None,
    source_file: str = "",
):
    """Write parsed cards to a CSV file.

    Args:
        cards: List of card dicts from docx_parser.
        output_path: Path for the output CSV.
        source_file: Original filename for reference.

    Returns:
        Path to the created CSV file.
    """
    if not output_path:
        output_path = os.path.join(SCRAPED_DIR, "scraped_cards.csv")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    file_exists = os.path.exists(output_path)

    # Load existing filePaths to avoid duplicates when appending
    existing_paths = set()
    if file_exists:
        with open(output_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fp = row.get("filePath", "")
                if fp:
                    existing_paths.add(fp)

    new_cards = [c for c in cards if c.get("filePath", "") not in existing_paths]
    skipped = len(cards) - len(new_cards)

    with open(output_path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        if not file_exists:
            writer.writeheader()

        for card in new_cards:
            card["source_file"] = source_file
            writer.writerow(card)

    if skipped:
        print(f"Skipped {skipped} duplicate cards (already in CSV)")
    print(f"Exported {len(new_cards)} new cards to {output_path}")
    return output_path
