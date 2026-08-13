$ErrorActionPreference = "Stop"
$Candidates = @(
    (Get-Command py -ErrorAction SilentlyContinue).Source,
    (Get-Command python -ErrorAction SilentlyContinue).Source,
    (Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe")
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }
$Python = $null
foreach ($Candidate in $Candidates) {
    try {
        & $Candidate --version *> $null
        if ($LASTEXITCODE -eq 0) { $Python = $Candidate; break }
    } catch {
        continue
    }
}
if (-not $Python) { throw "Python 3.11+ was not found. Install Python and run this script again." }
if (-not (Test-Path -LiteralPath ".venv\Scripts\python.exe")) { & $Python -m venv .venv }
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& .\.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
