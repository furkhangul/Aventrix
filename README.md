# FurOfTheWeak

A URL intelligence & campaign management platform: create tracked links, organize them into campaigns, and see privacy-respecting analytics about who's clicking — with explicit visitor consent built into the core flow, not bolted on.

```text
Dashboard → Campaign → Tracking Link → /t/CODE → Consent/Password gate → Redirect
                                                        ↓
                                                  Visit recorded → IP intelligence (async) → Dashboard
```

## Status

This build covers the **core platform** end-to-end, production-shaped and tested:

- Authentication: register/login/logout, refresh-token rotation, email verification, password reset, 2FA (TOTP + backup codes), active sessions, login history, account deletion — all RBAC-enforced server-side (`SUPER_ADMIN → ADMIN → MANAGER → USER → VIEWER`)
- Campaigns & tracking links: custom aliases, reserved-word/collision checks, expiration, password protection, optional consent gate, UTM builder
- Redirect system with no open-redirect surface — targets are only ever read from the database, never from the request
- Per-visit analytics: IP intelligence (mock provider by default, real-provider adapter ready), UA parsing, bot-confidence signal; the raw client IP is recorded on every visit, while the richer device/browser/UTM fingerprint is gated on explicit consent (see `docs/SECURITY.md#privacy`)
- Dashboard + a filterable/exportable Analytics page: stat cards, visit trends, top countries/devices/browsers/OS/referrers, date-range and link/campaign filters, CSV/JSON export
- QR Codes: server-generated PNG/SVG for any link or URL, customizable size/colors/error-correction, optional embedded logo
- URL Tools: encoder/decoder, UTM builder, an SSRF-hardened URL analyzer (title/description/favicon), and a redirect-chain checker
- Security Center: DNS, WHOIS, and SSL certificate checks (all real, no API key needed), a security-headers analyzer, and a reputation check (mock by default, real adapter ready) — combined into a 0–100 score with scan history
- API keys: tiered (Free/Pro/Business) alternate credentials for the whole API, shown once, hashed at rest, rate-limited per tier
- Webhooks: HMAC-signed, event-driven (`link.created/clicked`, `campaign.created/completed`, `security.alert`), delivered async with retry backoff and a delivery log
- Notifications: in-app center + email, triggered by a link's first visit, link expiry, a webhook's final failure, and a low security score, with per-type email preferences
- Security baseline: rate limiting, security headers, CORS, standard error envelope, structured JSON logs, audit log, IDOR-safe ownership checks throughout, SSRF-hardened outbound fetching everywhere a user-supplied URL is fetched server-side

See [Proje.md](./Proje.md) for the full original specification and `docs/ARCHITECTURE.md` for what's still deferred (PDF export, real-time SSE/WebSocket dashboard, AI assistant, admin panel, workspaces, billing, CI/CD).

## Quick start

**With Docker (recommended):**

```bash
cp .env.example .env      # edit secrets/URLs as needed
docker compose up
```

(Or run `scripts/dev-setup.ps1` on Windows / `scripts/dev-setup.sh` on macOS/Linux — creates `.env` for you and checks whether Docker is on your PATH.)

This brings up Postgres, Redis, the API, the background worker, the frontend dev server, and nginx. Migrations and a development admin seed run automatically on backend startup — watch the logs for a one-time printed admin password.

- App (via nginx): http://localhost:8080
- Frontend directly: http://localhost:5173
- API docs (Swagger): http://localhost:8000/api/docs

**Without Docker:** see [docs/SETUP.md](./docs/SETUP.md) for running the backend and frontend locally against your own Postgres/Redis.

## Documentation

| Doc | Purpose |
| --- | --- |
| [SETUP.md](./docs/SETUP.md) | Docker and manual local setup |
| [ARCHITECTURE.md](./docs/ARCHITECTURE.md) | System design, module layout, what's built vs. deferred |
| [DATABASE.md](./docs/DATABASE.md) | Schema, indexes, retention |
| [API.md](./docs/API.md) | Endpoint reference |
| [SECURITY.md](./docs/SECURITY.md) | Threat model, protections, known advisories |
| [ENVIRONMENT.md](./docs/ENVIRONMENT.md) | Every environment variable explained |
| [DEPLOYMENT.md](./docs/DEPLOYMENT.md) | Production deployment notes and checklist |
| [CONTRIBUTING.md](./docs/CONTRIBUTING.md) | Code style, testing, PR expectations |

## Tech stack

React 18 + TypeScript + Vite + Tailwind + Radix primitives + TanStack Query · FastAPI + SQLAlchemy (async) + Alembic · PostgreSQL · Redis · Docker Compose + nginx.
