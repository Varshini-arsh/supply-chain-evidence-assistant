param([int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) { $projectPython = (Get-Command python -ErrorAction Stop).Source }
$localReady = $false
try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2; $localReady = $true } catch {}
if (-not $localReady) {
    $ollamaCommand = Get-Command ollama -ErrorAction SilentlyContinue
    if ($ollamaCommand) {
        $env:OLLAMA_MODELS = Join-Path $PSScriptRoot 'models'
        Start-Process -FilePath $ollamaCommand.Source -ArgumentList 'serve' -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'ollama.start.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'ollama.start.stderr.log')
    } else { Write-Host 'Ollama is unavailable. The offline evidence workflow still works.' }
}
Write-Host "Open http://127.0.0.1:$Port"
& $projectPython app.py --port $Port

