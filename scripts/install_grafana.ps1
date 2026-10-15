$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$tempRoot = Join-Path $projectRoot '.tmp'
$runtime = Join-Path $tempRoot 'grafana-runtime'
$plugins = Join-Path $tempRoot 'grafana-data\plugins'
New-Item -ItemType Directory -Path $tempRoot,$runtime,$plugins -Force | Out-Null

$grafanaArchive = Join-Path $tempRoot 'grafana_13.2.3_36482603486_windows_amd64.tar.gz'
$grafanaHash = 'DAFE883A7C15543C6D6710B868EB8B4053353441CE7CEACF150942B8DE3960F0'
if (-not (Test-Path -LiteralPath $grafanaArchive)) {
    Invoke-WebRequest -Uri 'https://dl.grafana.com/grafana/release/13.2.3/grafana_13.2.3_36482603486_windows_amd64.tar.gz' -OutFile $grafanaArchive
}
if ((Get-FileHash -LiteralPath $grafanaArchive -Algorithm SHA256).Hash -ne $grafanaHash) {
    throw "Grafana archive checksum mismatch: $grafanaArchive"
}
$grafanaExe = Join-Path $runtime 'grafana-13.2.3\bin\grafana.exe'
if (-not (Test-Path -LiteralPath $grafanaExe)) {
    tar -xzf $grafanaArchive -C $runtime
    if ($LASTEXITCODE -ne 0) { throw 'Grafana archive extraction failed.' }
}

$pluginArchive = Join-Path $tempRoot 'frser-sqlite-datasource-4.0.6.zip'
$pluginHash = 'E5CE2354DD26BA9BEA56B37F9ED4050CC917A46B858A0A191E1CAFDA382BF18A'
if (-not (Test-Path -LiteralPath $pluginArchive)) {
    Invoke-WebRequest -Uri 'https://github.com/fr-ser/grafana-sqlite-datasource/releases/download/v4.0.6/frser-sqlite-datasource-4.0.6.zip' -OutFile $pluginArchive
}
if ((Get-FileHash -LiteralPath $pluginArchive -Algorithm SHA256).Hash -ne $pluginHash) {
    throw "SQLite plugin archive checksum mismatch: $pluginArchive"
}
$pluginExe = Join-Path $plugins 'frser-sqlite-datasource\gpx_sqlite-datasource_windows_amd64.exe'
if (-not (Test-Path -LiteralPath $pluginExe)) {
    Expand-Archive -LiteralPath $pluginArchive -DestinationPath $plugins
}
if (-not (Test-Path -LiteralPath $grafanaExe) -or -not (Test-Path -LiteralPath $pluginExe)) {
    throw 'Grafana or its SQLite plugin executable was not installed.'
}
Write-Output 'Grafana 13.2.3 and SQLite datasource 4.0.6 verified in .tmp.'
