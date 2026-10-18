$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$grafanaHome = Join-Path $projectRoot '.tmp\grafana-runtime\grafana-13.2.3'
$grafanaExe = Join-Path $grafanaHome 'bin\grafana.exe'
$pluginExe = Join-Path $projectRoot '.tmp\grafana-data\plugins\frser-sqlite-datasource\gpx_sqlite-datasource_windows_amd64.exe'
if (-not (Test-Path -LiteralPath $grafanaExe)) { throw "Grafana executable missing: $grafanaExe" }
if (-not (Test-Path -LiteralPath $pluginExe)) { throw "SQLite plugin missing: $pluginExe" }

$env:GF_PATHS_PROVISIONING = Join-Path $projectRoot 'grafana\provisioning'
$env:GF_PATHS_DATA = Join-Path $projectRoot '.tmp\grafana-data'
$env:GF_PATHS_PLUGINS = Join-Path $env:GF_PATHS_DATA 'plugins'
$env:GF_SERVER_HTTP_ADDR = '127.0.0.1'
$env:GF_SERVER_HTTP_PORT = '3000'
$env:GF_AUTH_ANONYMOUS_ENABLED = 'true'
$env:GF_AUTH_ANONYMOUS_ORG_ROLE = 'Viewer'
$env:GF_AUTH_BASIC_ENABLED = 'false'
$env:GF_AUTH_DISABLE_LOGIN_FORM = 'true'
$env:GF_USERS_DEFAULT_THEME = 'dark'

if (-not (Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue)) {
    Start-Process -FilePath $grafanaExe -ArgumentList 'server','--homepath',$grafanaHome -WorkingDirectory $grafanaHome -WindowStyle Hidden -RedirectStandardOutput (Join-Path $projectRoot '.tmp\grafana.stdout.log') -RedirectStandardError (Join-Path $projectRoot '.tmp\grafana.stderr.log') | Out-Null
}
for ($attempt = 0; $attempt -lt 30; $attempt++) {
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:3000/api/health' -TimeoutSec 2
        if ($health.database -eq 'ok') {
            Write-Output 'Grafana healthy at http://127.0.0.1:3000'
            exit 0
        }
    } catch { }
    Start-Sleep -Seconds 1
}
throw 'Grafana did not become healthy. Inspect .tmp/grafana.stderr.log.'
