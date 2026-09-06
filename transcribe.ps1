# PowerShell wrapper for speech2md.
# Examples:
#   .\transcribe.ps1 recording.mp3
#   .\transcribe.ps1 meeting.m4a -Language ru -Timestamps
#   .\transcribe.ps1 lecture.mp4 -Format md,srt -Model large-v3-turbo
param(
    [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$InputFile,

    [string]$Language,

    [string]$Model,

    [string[]]$Format,

    [ValidateSet('auto', 'cuda', 'cpu')]
    [string]$Device,

    [switch]$Timestamps,

    [string]$OutputPath
)

$ErrorActionPreference = 'Stop'

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = 'utf-8'

$exe = Join-Path $PSScriptRoot 'venv\Scripts\speech2md.exe'
if (-not (Test-Path $exe)) {
    Write-Error "speech2md is not installed. Run: .\install.ps1"
}

# Pass only parameters the user actually specified, so config-file defaults stay in effect.
$cliArgs = @($InputFile)
if ($PSBoundParameters.ContainsKey('Language')) { $cliArgs += @('--language', $Language) }
if ($PSBoundParameters.ContainsKey('Model')) { $cliArgs += @('--model', $Model) }
if ($PSBoundParameters.ContainsKey('Format')) { $cliArgs += @('--format', ($Format -join ',')) }
if ($PSBoundParameters.ContainsKey('Device')) { $cliArgs += @('--device', $Device) }
if ($Timestamps) { $cliArgs += '--timestamps' }
if ($OutputPath) { $cliArgs += @('--output', $OutputPath) }

& $exe @cliArgs
exit $LASTEXITCODE
