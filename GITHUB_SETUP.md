# GitHub Setup

This project is ready to publish as a GitHub repository, but publishing requires
an authenticated GitHub account on the local machine.

## Recommended Settings

- Repository name: `kegg-kgml-tools`
- Visibility: `private`
- Data: do not commit generated KEGG KGML/XML files

## Publish With GitHub CLI

From inside this folder:

```powershell
gh auth login
.\scripts\publish-to-github.ps1 -RepositoryName kegg-kgml-tools -Visibility private
```

To publish under an organization or specific owner:

```powershell
.\scripts\publish-to-github.ps1 -Owner your-github-owner -RepositoryName kegg-kgml-tools -Visibility private
```

## Manual Web Upload

1. Create a new private repository named `kegg-kgml-tools` in GitHub.
2. Upload the contents of this folder.
3. Keep the generated `data/` outputs excluded unless your KEGG license allows
   redistribution.
