# Publish Windows build to GitHub Releases (requires: gh auth login, or set GH_TOKEN).
# Default exe path matches MetaEditor1.0_builds layout; override with $env:META_EDITOR_EXE.

$ErrorActionPreference = "Stop"
$Repo = "fosixty/MetaEditor"
$Tag = if ($env:META_EDITOR_TAG) { $env:META_EDITOR_TAG } else { "v1.0.0" }
$Exe = if ($env:META_EDITOR_EXE) {
    $env:META_EDITOR_EXE
} else {
    Join-Path $env:USERPROFILE "Documents\App_Projects\MetaEditor1.0_builds\dist_new\MetaEditor.exe"
}

$gh = "C:\Program Files\GitHub CLI\gh.exe"
if (-not (Test-Path $gh)) { $gh = "gh" }

& $gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run once: gh auth login`nOr set GH_TOKEN to a classic PAT with repo scope." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -LiteralPath $Exe)) {
    Write-Host "Exe not found: $Exe" -ForegroundColor Red
    exit 1
}

& $gh release create $Tag $Exe `
    --repo $Repo `
    --title "MetaEditor $Tag (Windows)" `
    --notes "Windows build from dist_new. Add macOS .dmg from your Mac as another release asset if you like."
