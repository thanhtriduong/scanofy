$ErrorActionPreference = "Stop"

$workspaceRoot = Split-Path -Parent $PSScriptRoot

Push-Location (Join-Path $workspaceRoot "be")
try {
    .\.venv\Scripts\python.exe -m pytest
}
finally {
    Pop-Location
}
Push-Location (Join-Path $workspaceRoot "fe")
try {
    npm run lint
    npm run build
}
finally {
    Pop-Location
}
