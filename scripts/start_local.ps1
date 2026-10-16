$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$env:TEMP = 'F:\SecureLLM.tmp'
$env:TMP = 'F:\SecureLLM.tmp'
$env:SECURELLM_ENABLE_LOCAL_RUNS = '1'
New-Item -ItemType Directory -Path $env:TEMP -Force | Out-Null
$logDirectory = Join-Path $projectRoot '.tmp'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
$nodePath = (Get-Command node -ErrorAction Stop).Source
if (-not (Test-Path -LiteralPath $pythonPath)) { throw "Missing interpreter: $pythonPath" }
if (-not (Get-NetTCPConnection -State Listen -LocalPort 8000 -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $pythonPath -ArgumentList '-m','uvicorn','apps.api.main:app','--host','127.0.0.1','--port','8000' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'backend.stdout.log') -RedirectStandardError (Join-Path $logDirectory 'backend.stderr.log') | Out-Null
}
if (-not (Get-NetTCPConnection -State Listen -LocalPort 5173 -ErrorAction SilentlyContinue)) {
    $vitePath = Join-Path $projectRoot 'frontend\node_modules\vite\bin\vite.js'
    Start-Process -FilePath $nodePath -ArgumentList ('"' + $vitePath + '"'),'--configLoader','runner','--host','127.0.0.1','--port','5173','--strictPort' -WorkingDirectory (Join-Path $projectRoot 'frontend') -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'frontend.stdout.log') -RedirectStandardError (Join-Path $logDirectory 'frontend.stderr.log') | Out-Null
}
$verified = $false
for ($attempt = 0; $attempt -lt 15; $attempt++) {
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:8000/health'
        $ready = Invoke-RestMethod 'http://127.0.0.1:8000/ready'
        $proxy = Invoke-RestMethod 'http://127.0.0.1:5173/benchmark-datasets' -Headers @{Accept='application/json'}
        $page = Invoke-WebRequest 'http://127.0.0.1:5173/' -Headers @{Accept='text/html'}
        if ($health.service -eq 'securellmbench' -and $ready.status -eq 'ready' -and $null -ne $proxy.items -and $page.Content.Contains('<div id="root"></div>')) { $verified = $true; break }
    } catch { }
    Start-Sleep -Seconds 1
}
if (-not $verified) { throw "Local services failed verification. Inspect $logDirectory service logs and check for port conflicts." }
Write-Output 'Verified backend http://127.0.0.1:8000 and dashboard http://127.0.0.1:5173'
if (Test-Path -LiteralPath (Join-Path $projectRoot '.tmp\grafana-runtime\grafana-13.2.3\bin\grafana.exe')) {
    & (Join-Path $PSScriptRoot 'start_grafana.ps1')
}
