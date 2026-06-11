# KEGG KGML Tools

Utilities for organizing KEGG pathway KGML/XML files in a reproducible local
folder structure.

## What This Project Does

- Imports local KEGG KGML/XML files from authorized archives, ZIP files,
  folders, or individual XML/KGML files.
- Produces a normalized `kgml/` output directory.
- Creates `manifest.csv` and `manifest.json` indexes with pathway metadata.
- Includes an optional KEGG REST downloader for environments that have API
  access.

## Important Data Note

This repository does not include KEGG KGML/XML data.

KEGG pathway KGML files may require an authorized KEGG FTP/subscription or other
valid access rights. Use these tools only with data you are allowed to access and
process.

## Main Workflow Without KEGG API Access

If you have local KGML archives from an authorized source, run:

```powershell
python scripts/import-kegg-kgml-archive.py "C:\path\to\ko.tar.gz" "C:\path\to\ec.tar.gz" "C:\path\to\rn.tar.gz" --output data\kegg-kgml
```

You can also import a folder, ZIP, single `.xml`, or single `.kgml` file:

```powershell
python scripts/import-kegg-kgml-archive.py "C:\path\to\kgml-folder" --output data\kegg-kgml
```

Output:

```text
data/kegg-kgml/
|-- README.md
|-- manifest.csv
|-- manifest.json
`-- kgml/
    |-- map00010.xml
    |-- map00020.xml
    `-- ...
```

## Optional KEGG REST API Workflow

If you do have KEGG REST access and want the reference metabolic pathway maps:

```powershell
python scripts/download-kegg-metabolic-kgml.py --output data\kegg-metabolic-kgml
```

This script:

- Reads KEGG BRITE `br08901`.
- Selects pathways under `09100 Metabolism`.
- Downloads each pathway from `/get/mapXXXXX/kgml`.

## Requirements

- Python 3.10+
- No third-party Python packages

## Repository Contents

- `scripts/import-kegg-kgml-archive.py` - import local licensed KGML/XML archives.
- `scripts/download-kegg-metabolic-kgml.py` - optional API-based downloader.
- `docs/kegg-data-policy.md` - notes on KEGG data handling.

## Suggested GitHub Repository Settings

- Visibility: private, unless you are only publishing code and no KEGG data.
- Do not commit generated `data/` contents unless you have explicit permission
  to redistribute them.
- Keep generated manifests out of public repositories if they expose licensed
  data details you do not intend to share.
