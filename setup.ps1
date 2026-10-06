param([switch]$SkipModels, [switch]$Dev)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
python -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python virtual environment creation failed.' }
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
& $projectPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Runtime dependency installation failed.' }
if ($Dev) {
    & $projectPython -m pip install -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw 'Development dependency installation failed.' }
}
& $projectPython create_sample_pdf.py
if (-not $SkipModels) {
    $ollamaCommand = Get-Command ollama -ErrorAction Stop
    $modelServiceReady = $false
    try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2; $modelServiceReady = $true } catch {}
    if (-not $modelServiceReady) {
        $env:OLLAMA_MODELS = Join-Path $PSScriptRoot 'models'
        Start-Process -FilePath $ollamaCommand.Source -ArgumentList 'serve' -WindowStyle Hidden -RedirectStandardOutput (Join-Path $PSScriptRoot 'ollama.setup.stdout.log') -RedirectStandardError (Join-Path $PSScriptRoot 'ollama.setup.stderr.log')
        for ($attempt = 0; $attempt -lt 15; $attempt++) {
            Start-Sleep -Milliseconds 1000
            try { $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2; $modelServiceReady = $true; break } catch {}
        }
    }
    if (-not $modelServiceReady) { throw 'Could not start the local Ollama service.' }
    foreach ($modelName in @('qwen2.5:0.5b','all-minilm')) {
        Write-Host "Downloading local model $modelName"
        $modelPayload = @{ model = $modelName; stream = $false } | ConvertTo-Json
        $null = Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/pull' -Method Post -ContentType 'application/json' -Body $modelPayload -TimeoutSec 1800
    }
}
Write-Host 'Setup complete. Run .\start.ps1'

