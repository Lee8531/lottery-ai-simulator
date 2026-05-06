[CmdletBinding()]
param(
    [switch]$SkipInstall
)

$ErrorActionPreference = "Stop"

$RepoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $RepoRoot

$env:PYTHONPATH = "src"
$AppName = "lottery-ai-simulator"
$DistDir = Join-Path $RepoRoot "dist\$AppName"
$BuildDir = Join-Path $RepoRoot "build\$AppName"

function Test-PyInstaller {
    & python -m PyInstaller --version *> $null
    return ($LASTEXITCODE -eq 0)
}

if (-not (Test-PyInstaller)) {
    if ($SkipInstall) {
        throw "PyInstaller is not installed. Run without -SkipInstall or install it manually."
    }
    Write-Host "Installing PyInstaller..."
    & python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install PyInstaller."
    }
}

foreach ($path in @($DistDir, $BuildDir)) {
    if (Test-Path -LiteralPath $path) {
        Remove-Item -LiteralPath $path -Recurse -Force
    }
}

$pyinstallerArgs = @(
    "--noconfirm",
    "--clean",
    "--onedir",
    "--name",
    $AppName,
    "--paths",
    "src",
    "--collect-submodules",
    "fastapi",
    "--collect-submodules",
    "starlette",
    "--collect-submodules",
    "uvicorn",
    "--collect-submodules",
    "pydantic",
    "--exclude-module",
    "tests",
    "launcher.py"
)

& python -m PyInstaller @pyinstallerArgs
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller build failed."
}

Copy-Item -Path "scripts" -Destination (Join-Path $DistDir "scripts") -Recurse -Force
New-Item -ItemType Directory -Force -Path (Join-Path $DistDir "data\normalized") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DistDir "data\users") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DistDir "reports\latest") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $DistDir "reports\users") | Out-Null

Write-Host "EXE build finished:"
Write-Host (Join-Path $DistDir "$AppName.exe")
