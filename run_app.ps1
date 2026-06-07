$ErrorActionPreference = "Stop"

$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    python -m venv (Join-Path $PSScriptRoot ".venv")
}

& $venvPython -m pip install -r (Join-Path $PSScriptRoot "requirements.txt")
& $venvPython -m streamlit run (Join-Path $PSScriptRoot "app.py")
