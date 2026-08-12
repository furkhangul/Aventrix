#!/usr/bin/env bash
# Dumps the production Postgres database to a timestamped, gzipped file
# under backups/ (gitignored). Wire this into a cron job on the VPS —
# see docs/DEPLOY_VPS.md — this script does not schedule itself.
#
# Usage: scripts/backup-db.sh
#
# Restore with:
#   gunzip -c backups/furoftheweak_YYYYMMDD_HHMMSS.sql.gz | \
#     docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres \
#       psql -U furoftheweak -d furoftheweak
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

backup_dir="$repo_root/backups"
mkdir -p "$backup_dir"

timestamp="$(date +%Y%m%d_%H%M%S)"
out_file="$backup_dir/furoftheweak_${timestamp}.sql.gz"

pg_user="${POSTGRES_USER:-furoftheweak}"
pg_db="${POSTGRES_DB:-furoftheweak}"

echo "[backup-db] Dumping $pg_db to $out_file..."
docker compose --env-file .env.production -f docker-compose.prod.yml exec -T postgres \
    pg_dump -U "$pg_user" "$pg_db" | gzip > "$out_file"

echo "[backup-db] Done: $out_file ($(du -h "$out_file" | cut -f1))"

# Keep the last 14 daily backups, discard older ones — untested retention
# forever is just a slowly filling disk, not a backup policy.
find "$backup_dir" -name 'furoftheweak_*.sql.gz' -mtime +14 -delete
