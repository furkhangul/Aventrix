#!/usr/bin/env bash
# One-time TLS bootstrap for a fresh Aventrix production deploy.
#
# nginx's production config (nginx/nginx.prod.conf) has a TLS server block
# that points at a Let's Encrypt certificate — but nginx won't even start
# with that config if the certificate doesn't exist yet, and Let's Encrypt's
# webroot challenge needs nginx to already be serving HTTP. This script
# breaks that chicken-and-egg loop the standard way: issue a throwaway
# self-signed cert so nginx can start, then swap it for a real one.
#
# Usage: scripts/init-letsencrypt.sh yourdomain.com you@example.com
#
# Run this ONCE, from the repo root on the VPS, after:
#   - DNS for the domain points at this server's public IP
#   - .env.production exists and is filled in (cp .env.production.example .env.production)
# See docs/DEPLOY_VPS.md for the full walkthrough.
set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <domain> <email-for-letsencrypt-renewal-notices>"
    exit 1
fi

DOMAIN="$1"
EMAIL="$2"

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

compose() {
    docker compose --env-file .env.production -f docker-compose.prod.yml "$@"
}

certbot_conf="nginx/certbot/conf"
certbot_www="nginx/certbot/www"
live_path="$certbot_conf/live/$DOMAIN"

if [ ! -f ".env.production" ]; then
    echo "[init-letsencrypt] .env.production not found. Copy .env.production.example to .env.production and fill it in first."
    exit 1
fi

echo "[init-letsencrypt] Writing $DOMAIN into nginx/nginx.prod.conf (replacing the YOUR_DOMAIN_HERE placeholder)..."
sed -i.bak "s/YOUR_DOMAIN_HERE/$DOMAIN/g" nginx/nginx.prod.conf
rm -f nginx/nginx.prod.conf.bak

mkdir -p "$live_path" "$certbot_www"

echo "[init-letsencrypt] Creating a throwaway self-signed cert so nginx can start..."
openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout "$live_path/privkey.pem" \
    -out "$live_path/fullchain.pem" \
    -subj "/CN=$DOMAIN"

echo "[init-letsencrypt] Starting nginx with the dummy cert..."
compose up -d --build nginx

echo "[init-letsencrypt] Deleting the dummy cert and requesting a real one from Let's Encrypt..."
rm -rf "$certbot_conf/live/$DOMAIN" "$certbot_conf/archive/$DOMAIN" "$certbot_conf/renewal/$DOMAIN.conf"

compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    -d $DOMAIN \
    --email $EMAIL --agree-tos --no-eff-email" certbot

echo "[init-letsencrypt] Reloading nginx with the real certificate..."
compose exec nginx nginx -s reload

echo "[init-letsencrypt] Done. https://$DOMAIN should now serve a valid certificate."
echo "[init-letsencrypt] The 'certbot' service in docker-compose.prod.yml handles renewal automatically from now on."
