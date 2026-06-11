# KEGG Data Handling Notes

This project is designed to work with KEGG KGML/XML files that the user has
already obtained through an authorized channel.

## Principles

- Do not redistribute KEGG KGML/XML data unless your license allows it.
- Keep generated `data/` outputs out of public repositories by default.
- Treat manifests as potentially sensitive if they reveal the contents of a
  licensed data package.
- Prefer private GitHub repositories for internal or exploratory work.

## Supported Inputs

The local importer accepts:

- `.tar.gz`, `.tgz`, and `.tar` archives
- `.zip` archives
- folders containing `.xml` or `.kgml` files
- individual `.xml` or `.kgml` files

## Expected Output

The importer creates:

- `kgml/` - normalized XML files named by pathway ID
- `manifest.csv` - tabular metadata
- `manifest.json` - structured metadata
- `README.md` - generated local dataset note
