param(
    [Parameter(Mandatory = $false)]
    [string]$RepositoryName = "kegg-kgml-tools",

    [Parameter(Mandatory = $false)]
    [ValidateSet("private", "public", "internal")]
    [string]$Visibility = "private",

    [Parameter(Mandatory = $false)]
    [string]$Owner = ""
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "Git is required but was not found in PATH."
}

if (-not (Get-Command gh -ErrorAction SilentlyContinue)) {
    throw "GitHub CLI is required but was not found in PATH. Install it and run: gh auth login"
}

$repoArg = $RepositoryName
if ($Owner.Trim()) {
    $repoArg = "$Owner/$RepositoryName"
}

if (-not (Test-Path ".git")) {
    git init
    git branch -M main
}

git add .
git commit -m "Initial KEGG KGML tools project"

$visibilityFlag = "--private"
if ($Visibility -eq "public") {
    $visibilityFlag = "--public"
}
elseif ($Visibility -eq "internal") {
    $visibilityFlag = "--internal"
}

gh repo create $repoArg $visibilityFlag --source . --remote origin --push
