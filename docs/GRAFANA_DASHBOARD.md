# Grafana benchmark dashboard

The local Grafana dashboard is a single scrollable page at
`http://127.0.0.1:3000/d/securellmbench/securellmbench-benchmark-evidence`.
It reads `securellmbench.db` through the SQLite datasource in read-only mode.
Grafana binds to `127.0.0.1` and permits anonymous **Viewer** access on that
local interface. Basic login is disabled for this local viewing service.

From `F:\SecureLLM` in PowerShell:

```powershell
$env:TEMP = 'F:\SecureLLM.tmp'
$env:TMP = 'F:\SecureLLM.tmp'
.\scripts\install_grafana.ps1
.\scripts\start_grafana.ps1
.\scripts\start_local.ps1
```

After installation, `start_local.ps1` also starts Grafana automatically when
its local runtime is present.

The installer uses the official Grafana 13.2.3 Windows archive and the
[SQLite datasource 4.0.6 release](https://github.com/fr-ser/grafana-sqlite-datasource/releases/tag/v4.0.6).
It checks pinned SHA-256 hashes before extracting into the ignored `.tmp`
directory. Provisioned dashboard and datasource definitions are in `grafana/`.

The line chart reads persisted `scientific_records` with
`family = model_score`, `status = computed`, `dataset_kind = repository_example`,
`scientifically_validated = false`, and formula version
`engineering-detector-score-v1`. Its markers are completed runs. The plotted
number is the existing engineering detector summary, plotted by chronological
run number so closely timed runs remain distinguishable. Exact completion
times are in the table. It is not validated attack
success, semantic drift, a safety rating, or a model recommendation. Other
formula versions are excluded from this line. The table lists the run IDs and
exact plotted values; full source hashes remain in the saved run reports.

No matched, validated before/after attack behavioral measurement is persisted.
The drift panel therefore reports **Unavailable** and does not draw a value.
The Phase 4 condition labels alone do not define a numerical behavioral state.

The Grafana `/api/health` endpoint, provisioned dashboard API, datasource API,
and `/api/ds/query` can be used to verify the live service and exact SQL
results. The React dashboard at `http://127.0.0.1:5173/` links to Grafana and
also shows the marked engineering trend.
