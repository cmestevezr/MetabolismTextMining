#!/usr/bin/env python3
"""Import KEGG KGML/XML files from local licensed archives.

Use this when KEGG REST API access is unavailable but you have KGML files from an
authorized KEGG FTP/subscription export, for example ko.tar.gz, ec.tar.gz,
rn.tar.gz, organism tarballs, or a folder/zip containing .xml/.kgml files.
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import tarfile
import tempfile
import zipfile
from datetime import date
from pathlib import Path
import xml.etree.ElementTree as ET


def iter_xml_files(input_path: Path):
    if input_path.is_dir():
        yield from input_path.rglob("*.xml")
        yield from input_path.rglob("*.kgml")
        return

    suffixes = "".join(input_path.suffixes).lower()
    if suffixes.endswith((".tar.gz", ".tgz", ".tar")):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with tarfile.open(input_path) as archive:
                archive.extractall(tmp_path, filter="data")
            yield from tmp_path.rglob("*.xml")
            yield from tmp_path.rglob("*.kgml")
        return

    if input_path.suffix.lower() == ".zip":
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            with zipfile.ZipFile(input_path) as archive:
                archive.extractall(tmp_path)
            yield from tmp_path.rglob("*.xml")
            yield from tmp_path.rglob("*.kgml")
        return

    if input_path.suffix.lower() in {".xml", ".kgml"}:
        yield input_path
        return

    raise ValueError(f"Unsupported input: {input_path}")


def parse_kgml(xml_path: Path) -> dict[str, str]:
    tree = ET.parse(xml_path)
    root = tree.getroot()
    if root.tag != "pathway":
        raise ValueError(f"{xml_path} is not a KGML pathway file")

    raw_name = root.attrib.get("name", "")
    pathway_id = raw_name.split(":")[-1] if ":" in raw_name else raw_name
    if not pathway_id:
        pathway_id = xml_path.stem

    return {
        "pathway_id": pathway_id,
        "title": root.attrib.get("title", ""),
        "org": root.attrib.get("org", ""),
        "number": root.attrib.get("number", ""),
        "image": root.attrib.get("image", ""),
        "link": root.attrib.get("link", ""),
    }


def import_archives(inputs: list[Path], output_dir: Path, force: bool) -> list[dict[str, str]]:
    kgml_dir = output_dir / "kgml"
    kgml_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, str]] = []
    seen_sources: set[Path] = set()

    for input_path in inputs:
        for xml_path in iter_xml_files(input_path):
            resolved = xml_path.resolve()
            if resolved in seen_sources:
                continue
            seen_sources.add(resolved)

            metadata = parse_kgml(xml_path)
            pathway_id = metadata["pathway_id"].replace("path:", "")
            destination = kgml_dir / f"{pathway_id}.xml"

            status = "copied"
            if destination.exists() and not force:
                status = "already_exists"
            else:
                shutil.copyfile(xml_path, destination)

            rows.append(
                {
                    **metadata,
                    "source_file": str(input_path),
                    "kgml_file": str(destination.as_posix()),
                    "status": status,
                }
            )

    rows.sort(key=lambda row: row["pathway_id"])
    return rows


def write_outputs(output_dir: Path, rows: list[dict[str, str]]) -> None:
    fieldnames = [
        "pathway_id",
        "title",
        "org",
        "number",
        "image",
        "link",
        "source_file",
        "kgml_file",
        "status",
    ]

    with (output_dir / "manifest.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    (output_dir / "manifest.json").write_text(
        json.dumps(
            {
                "title": "KEGG KGML/XML files imported from local archives",
                "import_date": date.today().isoformat(),
                "pathway_count": len(rows),
                "pathways": rows,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    readme = f"""# KEGG KGML/XML Import

Imported from local KEGG KGML archives on `{date.today().isoformat()}`.

Files are stored in `kgml/` and indexed in `manifest.csv` and `manifest.json`.
Only use this with KGML files you are authorized to access.

Pathways imported: `{len(rows)}`
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Import KEGG KGML/XML files from local tar.gz, zip, folder, or XML files."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Input archives/folders/files, e.g. ko.tar.gz ec.tar.gz rn.tar.gz.",
    )
    parser.add_argument(
        "--output",
        default="raw/data/kegg-kgml",
        help="Output directory. Defaults to raw/data/kegg-kgml.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing imported XML files.",
    )
    args = parser.parse_args()

    inputs = [Path(value) for value in args.inputs]
    missing = [str(path) for path in inputs if not path.exists()]
    if missing:
        raise SystemExit(f"Missing input path(s): {', '.join(missing)}")

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = import_archives(inputs, output_dir, args.force)
    write_outputs(output_dir, rows)

    print(f"Imported {len(rows)} KGML/XML files into {output_dir / 'kgml'}")
    print(f"Manifest: {output_dir / 'manifest.csv'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
