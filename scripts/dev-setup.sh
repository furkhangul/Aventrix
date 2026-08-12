#!/usr/bin/env bash
# One-time local dev bootstrap for FurOfTheWeak (macOS/Linux).
#
# Creates .env from .env.example if it doesn't exist yet, checks for
# Docker, and prints the next command to run. Safe to re-run — never
# overwrites an existing .env.
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
env_path="$repo_root/.env"
env_example_path="$repo_root/.env.example"

if [ -f "$env_path" ]; then
    echo "[dev-setup] .env already exists — leaving it untouched."
else
    cp "$env_example_path" "$env_path"
    echo "[dev-setup] Created .env from .env.example. Review it before running in anything but local dev."
fi

echo ""
if command -v docker >/dev/null 2>&1; then
    echo "[dev-setup] Docker found. Next step:"
    echo "    docker compose up"
else
    echo "[dev-setup] Docker not found on PATH. Follow the manual setup instead:"
    echo "    docs/SETUP.md -> 'Option B - Manual local setup'"
fi
