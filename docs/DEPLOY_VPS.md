# Deploying to a VPS (Oracle Cloud Always Free walkthrough)

A step-by-step path from nothing to a live HTTPS instance, using Oracle Cloud's **Always Free** tier (a genuinely-free-forever VM, not a trial) since it's a real VM with root access and Docker support — this stack (Postgres, Redis, FastAPI, a worker, nginx, and a TURN server for the Devices module) needs that; it will not run on shared/PHP-only hosting.

The same steps apply to any other VPS (Hetzner, DigitalOcean, etc.) — only step 1 and the firewall specifics in step 2 are Oracle-specific. See `docs/DEPLOYMENT.md` for the underlying pre-deploy checklist this walkthrough implements.

## 1. Create the instance

In the Oracle Cloud console: **Compute → Instances → Create Instance**. Pick an *Always Free-eligible* shape (an Ampere A1 flex instance, e.g. 2 OCPU/12GB, or a VM.Standard.E2.1.Micro) and an Ubuntu 22.04 or 24.04 image. Note the public IP it's assigned.

## 2. Open the firewall — two layers, both required

Oracle Cloud blocks inbound traffic in **two independent places**. Missing either one means "nothing connects" with no useful error message, even if nginx is running correctly.

**a) VCN Security List / Network Security Group** (console-side, in front of the VM):
Under your instance's VCN → Security Lists (or the NSG if you used one), add ingress rules for:
- `80/tcp` and `443/tcp` (HTTP/HTTPS)
- `3478/tcp` and `3478/udp` (TURN control)
- `49152-49252/udp` (TURN relay range) — only needed if you'll turn `ENABLE_DEVICE_CONTROL` on

**b) The VM's own firewall.** Oracle's Ubuntu images ship with restrictive `iptables` rules by default — `ufw` alone is not enough here, since Oracle's default iptables rules run independently of ufw's. On the VM:

```bash
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 3478 -j ACCEPT
sudo iptables -I INPUT -p udp --dport 3478 -j ACCEPT
sudo iptables -I INPUT -p udp --dport 49152:49252 -j ACCEPT
sudo netfilter-persistent save   # or: sudo iptables-save > /etc/iptables/rules.v4
```

## 3. Point DNS at the instance

Add an `A` record for your domain (and `www` if you want it) pointing at the instance's public IP. Wait for it to propagate (`dig +short yourdomain.com` should return the IP) before continuing — Let's Encrypt's challenge in step 7 needs this to already resolve correctly.

## 4. Install Docker

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# log out and back in for the group change to take effect
```

(This installs the Compose plugin too — `docker compose` works out of the box.)

## 5. Clone the repo and configure

```bash
git clone <your-repo-url> furoftheweak
cd furoftheweak
cp .env.production.example .env.production
nano .env.production   # fill in APP_SECRET_KEY, JWT_SECRET_KEY, POSTGRES_PASSWORD,
                        # APP_BASE_URL/FRONTEND_BASE_URL/TRACKING_BASE_URL/CORS_ORIGINS
                        # (all https://yourdomain.com), and TURN_* if you'll use Devices
```

Generate real secrets rather than editing them by hand:

```bash
openssl rand -hex 32   # run 3 times: APP_SECRET_KEY, JWT_SECRET_KEY, TURN_SHARED_SECRET
openssl rand -hex 24   # POSTGRES_PASSWORD — also update it inside DATABASE_URL to match
```

## 6. Issue the TLS certificate

```bash
bash scripts/init-letsencrypt.sh yourdomain.com you@example.com
```

This writes your domain into `nginx/nginx.prod.conf` (replacing the `YOUR_DOMAIN_HERE` placeholder) and runs the Let's Encrypt bootstrap dance (dummy cert → start nginx → real cert → reload). See the script's comments for what each step does; it's meant to be read, not just trusted blindly.

## 7. Bring the whole stack up

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

First boot runs migrations automatically (`alembic upgrade head`); the dev-only admin auto-seed is a no-op in production (`APP_ENV=production` — see `backend/scripts/seed.py`).

## 8. Verify

```bash
curl -I https://yourdomain.com/health          # expect 200, Strict-Transport-Security header present
curl -I http://yourdomain.com/                  # expect a 301 redirect to https
curl -I https://yourdomain.com/api/docs         # expect 404 — Swagger UI is disabled in production
```

Create your first account by registering normally in the browser, then promote it to admin directly in the database:

```bash
docker compose --env-file .env.production -f docker-compose.prod.yml exec postgres \
  psql -U furoftheweak -d furoftheweak \
  -c "UPDATE users SET role='SUPER_ADMIN' WHERE email='you@example.com';"
```

If you enabled `ENABLE_DEVICE_CONTROL`, confirm pairing works end-to-end (`/devices` in the app) before relying on it — TURN misconfiguration (wrong `TURN_SERVER_URL`, or the firewall rules from step 2 not actually applied) is the most likely failure point, and it fails silently as "connection never establishes" rather than a clear error.

## 9. Schedule backups

```bash
crontab -e
# add:
0 3 * * * cd /home/ubuntu/furoftheweak && bash scripts/backup-db.sh >> /var/log/furoftheweak-backup.log 2>&1
```

Dumps land in `backups/` (gitignored), 14 days retained automatically by the script. Test a restore at least once — an untested backup isn't a backup (see `docs/DEPLOYMENT.md`).

## Redeploying after a code change

```bash
git pull
docker compose --env-file .env.production -f docker-compose.prod.yml up -d --build
```

Certificates renew automatically via the `certbot` service already running in the stack — no action needed unless renewal fails (check `docker compose --env-file .env.production -f docker-compose.prod.yml logs certbot`).

## Out of scope here

Monitoring/alerting, log shipping, the data-retention cleanup job noted in `docs/DATABASE.md`, and scaling beyond one host are all separate follow-up work, not covered by this walkthrough.
