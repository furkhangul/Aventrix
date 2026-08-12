# Environment variables

Copy `.env.example` to `.env` at the repo root and fill in as needed. Nothing here is required to have a real value to run locally — every external integration defaults to a mock provider (`USE_MOCK_PROVIDERS=true`), and the app never crashes on a missing key; the affected feature just reports itself unavailable.

## App

| Variable | Default | Notes |
| --- | --- | --- |
| `APP_ENV` | `development` | `production` disables the auto-seeded admin account and enables HSTS |
| `APP_SECRET_KEY` | — | Used to pepper hashed tokens (`hash_token`). **Set a real random value before any shared/deployed use.** |
| `APP_BASE_URL` / `FRONTEND_BASE_URL` / `TRACKING_BASE_URL` | localhost ports | Used to build email links and `short_url` values |
| `USE_MOCK_PROVIDERS` | `true` | Forces every integration below to its mock, regardless of key presence |

## Database / Redis

`DATABASE_URL` (asyncpg DSN), `REDIS_URL`. Both are also decomposed into `POSTGRES_*` vars for docker-compose's Postgres image init.

## Auth

`JWT_SECRET_KEY`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_DAYS`, `COOKIE_SECURE` (set `true` behind HTTPS), `COOKIE_DOMAIN`.

## Rate limiting

`RATE_LIMIT_LOGIN_PER_MINUTE`, `RATE_LIMIT_REGISTER_PER_MINUTE`, `RATE_LIMIT_PASSWORD_RESET_PER_MINUTE`, `RATE_LIMIT_REDIRECT_PER_MINUTE`, `RATE_LIMIT_API_PER_MINUTE` — all per-IP, per-minute.

`RATE_LIMIT_API_KEY_FREE_PER_DAY`, `RATE_LIMIT_API_KEY_PRO_PER_DAY`, `RATE_LIMIT_API_KEY_BUSINESS_PER_DAY` — per-API-key, rolling 24h window (spec section 21's Free/Pro/Business tiers).

## Webhooks

`WEBHOOK_MAX_RETRY_ATTEMPTS` (default 5) — delivery attempts before giving up and notifying the owner. `WEBHOOK_DELIVERY_TIMEOUT_SECONDS` (default 8) — per-attempt HTTP timeout.

## Background worker

`WORKER_SWEEP_INTERVAL_SECONDS` (default 60) — how often the worker checks for due webhook retries and newly expired links.

## Security Center

`SECURITY_SCAN_ALERT_THRESHOLD` (default 60) — a scan scoring below this fires a `security.alert` webhook event and a notification.

## Seed

`SEED_ADMIN_EMAIL` — the account `python -m scripts.seed` creates (dev only; skipped in production). The password is always randomly generated and printed once, never configured here.

## Integrations (all adapter-pattern, all optional)

| Prefix | Provider values | What it's for |
| --- | --- | --- |
| `IP_PROVIDER`, `IP_INTELLIGENCE_*` | `mock`, `ipinfo`, `ipapi` | Visit geo/ISP/VPN enrichment. `ipapi` uses ip-api.com's free JSON endpoint — no key needed, but only resolves real public IPs (private/reserved-range IPs, e.g. local dev traffic, fall back to the mock provider) and doesn't distinguish VPN from proxy/Tor (reported as `is_proxy`, leaving `is_vpn`/`is_tor` `UNKNOWN`) |
| `REPUTATION_PROVIDER`, `REPUTATION_API_KEY` | `mock`, `safe_browsing` | Security Center domain reputation. DNS/WHOIS/SSL checks in the same module are always real (no key needed — open protocols) |
| `EMAIL_PROVIDER`, `EMAIL_*`, `SMTP_*` | `mock`, `smtp` | Verification/reset/notification emails |
| `MAP_PROVIDER`, `MAP_API_KEY` | — | Reserved for a future approximate-location map in the visit-detail UI — not consumed by any code yet |

## Feature flags

`ENABLE_QR` (default `true`), `ENABLE_WEBHOOK` (default `true`), `ENABLE_DOMAIN_ANALYZER` (default `true`) gate their respective routers — a disabled feature 404s instead of executing (`app/api/deps.py:require_feature`). `ENABLE_REALTIME` and `ENABLE_AI` remain declared but unread — those features (live dashboard push, AI assistant) are still deferred.
