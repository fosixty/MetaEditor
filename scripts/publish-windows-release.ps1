# Publish Windows installer to GitHub Releases (requires: gh auth login, or set GH_TOKEN).
# Default asset path matches local installer output; override with $env:QUARTZ_ASSET, $env:QUARTZ_EXE, or $env:META_EDITOR_EXE.

$ErrorActionPreference = "Stop"
$Repo = "fosixty/quartz"
$Tag = if ($env:META_EDITOR_TAG) { $env:META_EDITOR_TAG } else { "v1.0.0" }
$Asset = if ($env:QUARTZ_ASSET) {
    $env:QUARTZ_ASSET
} elseif ($env:QUARTZ_EXE) {
    $env:QUARTZ_EXE
} elseif ($env:META_EDITOR_EXE) {
    $env:META_EDITOR_EXE
} else {
    Join-Path $env:USERPROFILE "Documents\App_Projects\MetaEditor_Repo\dist\installer\Quartz-Setup-v1.0.0.exe"
}

$gh = "C:\Program Files\GitHub CLI\gh.exe"
if (-not (Test-Path $gh)) { $gh = "gh" }

& $gh auth status 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Run once: gh auth login`nOr set GH_TOKEN to a classic PAT with repo scope." -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path -LiteralPath $Asset)) {
    Write-Host "Release asset not found: $Asset" -ForegroundColor Red
    exit 1
}

& $gh release create $Tag $Asset `
    --repo $Repo `
    --title "Quartz $Tag (Windows)" `
    --notes "Windows installer build. Add macOS .dmg from your Mac as another release asset if you like."
