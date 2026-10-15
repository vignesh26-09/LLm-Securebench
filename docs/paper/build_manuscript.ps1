param(
    [string]$Python = 'C:\Users\tirishaanth\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
)

$ErrorActionPreference = 'Stop'
$paperDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:TEMP = 'F:\SecureLLM.tmp'
$env:TMP = 'F:\SecureLLM.tmp'
& $Python (Join-Path $paperDir 'build_manuscript_docx.py')
if ($LASTEXITCODE -ne 0) { throw 'DOCX build failed.' }

$source = Join-Path $paperDir 'SecureLLMBench_IEEE_Manuscript.docx'
$output = Join-Path $paperDir 'SecureLLMBench_IEEE_Manuscript.pdf'
$word = New-Object -ComObject Word.Application
try {
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open($source, $false, $true)
    try {
        $document.ExportAsFixedFormat($output, 17)
    }
    finally {
        $document.Close($false) | Out-Null
    }
}
finally {
    $word.Quit() | Out-Null
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null
}
Write-Output "Rendered $output"
