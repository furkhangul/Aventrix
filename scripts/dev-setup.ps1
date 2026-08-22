<#
.SYNOPSIS
    One-time local dev bootstrap for Aventrix (Windows/PowerShell).

.DESCRIPTION
    Creates .env from .env.example if it doesn't exist yet, checks for
    Docker, and prints the next command to run. Safe to re-run - never
    overwrites an existing .env.
#>

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

$envPath = Join-Path $repoRoot ".env"
$envExamplePath = Join-Path $repoRoot ".env.example"

if (Test-Path $envPath) {
    Write-Host "[dev-setup] .env already exists - leaving it untouched." -ForegroundColor Yellow
} else {
    Copy-Item $envExamplePath $envPath
    Write-Host "[dev-setup] Created .env from .env.example. Review it before running in anything but local dev." -ForegroundColor Green
}

$dockerAvailable = $null -ne (Get-Command docker -ErrorAction SilentlyContinue)

Write-Host ""
if ($dockerAvailable) {
    Write-Host "[dev-setup] Docker found. Next step:" -ForegroundColor Cyan
    Write-Host "    docker compose up"
} else {
    Write-Host "[dev-setup] Docker not found on PATH. Follow the manual setup instead:" -ForegroundColor Cyan
    Write-Host "    docs/SETUP.md -> 'Option B - Manual local setup'"
}
