
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

if (-not (Test-Path ".git")) {
    throw "This folder is not a Git repository."
}

if (-not (git remote get-url origin)) {
    throw "GitHub remote origin is missing."
}

Write-Host "Auto-sync started for $PSScriptRoot"
Write-Host "Press Ctrl+C to stop."

while ($true) {
    Start-Sleep -Seconds 3

    git add -A
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "Could not stage files."
        continue
    }

    git diff --cached --quiet
    $result = $LASTEXITCODE

    if ($result -eq 1) {
        $message = "Auto-sync: " + (Get-Date -Format "yyyy-MM-dd HH:mm:ss")
        git commit -m $message

        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Commit failed; check the files."
            continue
        }

        git push
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Push failed; check connection and retry."
        }
    }
    elseif ($result -gt 1) {
        Write-Warning "Could not check staged changes."
    }
}

