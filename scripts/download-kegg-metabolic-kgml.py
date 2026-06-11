#!/usr/bin/env python3
"""Download KEGG reference metabolic pathway maps as KGML/XML files.

The script uses the official KEGG REST API:
- br08901 JSON to identify the "Metabolism" pathway class
- /get/mapXXXXX/kgml to download each pathway as KGML/XML
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path


BRITE_URL = "https://rest.kegg.jp/get/br:br08901/json"
KGML_URL = "https://rest.kegg.jp/get/{pathway_id}/kgml"
PATH_RE = re.compile(r"(?P<name>.*?)\s+\[PATH:(?P<id>map\d{5})\]")


def fetch_text(url: str, retries: int = 3, timeout: int = 60) -> str:
    headers = {
        "User-Agent": "kegg-kgml-tools/1.0",
    }
    request = urllib.request.Request(url, headers=headers)
    last_error: Exception | None = None

    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2 * attempt)

    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def find_metabolism_node(brite: dict) -> dict:
    stack = [brite]
    while stack:
        node = stack.pop()
        name = str(node.get("name", ""))
        if name.startswith("09100 ") and "Metabolism" in name:
            return node
        stack.extend(node.get("children", []))
    raise ValueError("Could not find the '09100 Metabolism' node in br08901.")


def collect_metabolic_pathways(metabolism_node: dict) -> list[dict[str, str]]:
    pathways: list[dict[str, str]] = []

    def walk(node: dict, category: str = "", subcategory: str = "") -> None:
        name = str(node.get("name", ""))
        match = PATH_RE.match(name)
        if match:
            pathways.append(
                {
                    "pathway_id": match.group("id"),
                    "name": match.group("name").strip(),
                    "category": category,
                    "subcategory": subcategory,
                }
            )
            return

        children = node.get("children", [])
        next_category = category
        next_subcategory = subcategory

        if name.startswith("091") and name != metabolism_node.get("name"):
            next_category = name
            next_subcategory = ""
        elif category and children:
            next_subcategory = name

        for child in children:
            walk(child, next_category, next_subcategory)

    for child in metabolism_node.get("children", []):
        walk(child)

    unique: dict[str, dict[str, str]] = {}
    for pathway in pathways:
        unique[pathway["pathway_id"]] = pathway
    return sorted(unique.values(), key=lambda row: row["pathway_id"])


def write_manifest(output_dir: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "pathway_id",
        "name",
        "category",
        "subcategory",
        "kgml_file",
        "source_url",
        "downloaded",
    ]

    with (output_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    metadata = {
        "title": "KEGG reference metabolic pathway KGML/XML files",
        "source": "KEGG REST API",
        "brite_url": BRITE_URL,
        "download_date": date.today().isoformat(),
        "pathway_count": len(rows),
        "pathways": rows,
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_readme(output_dir: Path, pathway_count: int) -> None:
    readme = f"""# KEGG Metabolic Pathway KGML/XML

Downloaded from the official KEGG REST API.

- BRITE source: `{BRITE_URL}`
- KGML endpoint pattern: `https://rest.kegg.jp/get/mapXXXXX/kgml`
- Scope: reference pathway maps under `09100 Metabolism`
- Download date: `{date.today().isoformat()}`
- Pathways downloaded: `{pathway_count}`

Files are stored in `kgml/` and indexed in `manifest.csv` and `manifest.json`.
KGML is KEGG's XML representation of pathway maps.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Download all KEGG reference metabolic pathways as KGML/XML."
    )
    parser.add_argument(
        "--output",
        default="raw/data/kegg-metabolic-kgml",
        help="Output directory. Defaults to raw/data/kegg-metabolic-kgml.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download XML files that already exist.",
    )
    parser.add_argument(
        "--sleep",
        type=float,
        default=0.25,
        help="Delay between KGML requests in seconds. Defaults to 0.25.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Download only the first N pathways. Useful for testing.",
    )
    args = parser.parse_args()

    output_dir = Path(args.output)
    kgml_dir = output_dir / "kgml"
    kgml_dir.mkdir(parents=True, exist_ok=True)

    print(f"Fetching KEGG pathway hierarchy: {BRITE_URL}")
    brite_text = fetch_text(BRITE_URL)
    brite = json.loads(brite_text)
    (output_dir / "br08901.json").write_text(
        json.dumps(brite, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    metabolism_node = find_metabolism_node(brite)
    pathways = collect_metabolic_pathways(metabolism_node)
    if args.limit is not None:
        pathways = pathways[: args.limit]

    print(f"Found {len(pathways)} KEGG reference metabolic pathways.")

    manifest_rows: list[dict[str, str]] = []
    failures: list[str] = []

    for index, pathway in enumerate(pathways, start=1):
        pathway_id = pathway["pathway_id"]
        file_path = kgml_dir / f"{pathway_id}.xml"
        source_url = KGML_URL.format(pathway_id=pathway_id)

        if file_path.exists() and not args.force:
            downloaded = "already_exists"
        else:
            print(f"[{index}/{len(pathways)}] Downloading {pathway_id} - {pathway['name']}")
            try:
                xml_text = fetch_text(source_url)
                ET.fromstring(xml_text)
                file_path.write_text(xml_text, encoding="utf-8")
                downloaded = "yes"
            except Exception as exc:
                failures.append(f"{pathway_id}: {exc}")
                downloaded = "failed"
            time.sleep(args.sleep)

        manifest_rows.append(
            {
                **pathway,
                "kgml_file": str(file_path.as_posix()),
                "source_url": source_url,
                "downloaded": downloaded,
            }
        )

    write_manifest(output_dir, manifest_rows)
    write_readme(output_dir, len(manifest_rows))

    if failures:
        print("Some downloads failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        return 1

    print(f"Done. XML files: {kgml_dir}")
    print(f"Manifest: {output_dir / 'manifest.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
