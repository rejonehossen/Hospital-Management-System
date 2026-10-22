
$ErrorActionPreference = "Stop"

$root = "C:\MyProjects"
$watcherTemplate = "C:\AutoGitHub\auto-github.ps1"

$name = Read-Host "Enter project name"

if ($name -notmatch '^[a-zA-Z0-9._-]+$' -or $name -in @(".", "..")) {
    throw "Use only letters, numbers, dots, underscores and hyphens."
}

$path = Join-Path $root $name

if (Test-Path $path) {
    throw "This project folder already exists."
}

New-Item -ItemType Directory -Path $path -Force | Out-Null

if (-not (Test-Path $watcherTemplate)) {
    throw "Auto-sync script not found at $watcherTemplate"
}

Copy-Item $watcherTemplate (Join-Path $path "auto-github.ps1")

code $path

Start-Process powershell.exe -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$path\auto-github.ps1`""
)

Write-Host "Project created: $path"
