# speech2md installer for Windows: creates venv, installs the package,
# adds CUDA libraries automatically when an NVIDIA GPU is present.
$ErrorActionPreference = 'Stop'

Write-Host 'Creating virtual environment...'
python -m venv "$PSScriptRoot\venv"
if (-not $?) { throw 'Python 3.10+ is required (https://python.org)' }

$pip = Join-Path $PSScriptRoot 'venv\Scripts\pip.exe'
& $pip install --upgrade pip -q

$hasNvidia = $false
try { nvidia-smi | Out-Null; $hasNvidia = $true } catch {}

if ($hasNvidia) {
    Write-Host 'NVIDIA GPU detected - installing with CUDA support...'
    & $pip install -e "$PSScriptRoot[cuda]"
} else {
    Write-Host 'No NVIDIA GPU detected - installing CPU version...'
    & $pip install -e $PSScriptRoot
}

Write-Host ''
Write-Host 'Done! Try it:'
Write-Host "  $PSScriptRoot\transcribe.ps1 your_audio.mp3"
