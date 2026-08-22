# Aventrix

**A URL intelligence & campaign management platform**, done responsibly: create tracked links, organize them into campaigns, generate QR codes, run domain/security reconnaissance, and see privacy-respecting analytics about who's clicking — with explicit visitor consent built into the core flow, not bolted on afterwards.

Built as a full production-shaped SaaS: FastAPI + async SQLAlchemy backend, React + TypeScript frontend, Postgres, Redis, a background worker, and an optional companion Android app for remote device control — all containerized behind nginx.

```mermaid
flowchart LR
    A[Dashboard] --> B[Campaign]
    B --> C[Tracking link<br/>/t/CODE]
    C --> D{Consent /<br/>password gate}
    D --> E[Redirect]
    D --> F[Visit recorded]
    F --> G[IP intelligence<br/>async]
    G --> A
```

<p align="center">
  <img src="docs/screenshots/04-dashboard.png" alt="Aventrix dashboard" width="860">
</p>

---

## Table of contents

- [Highlights](#highlights)
- [Feature tour](#feature-tour)
- [Screenshots](#screenshots)
- [Architecture](#architecture)
- [Project structure](#project-structure)
- [Tech stack](#tech-stack)
- [Quick start](#quick-start)
- [Documentation](#documentation)
- [Security & privacy](#security--privacy)
- [Testing](#testing)
- [Roadmap](#roadmap-not-yet-built)
- [License](#license)

---

## Highlights

- 🔗 **Smart links** — custom aliases, expiration, password protection, optional consent gate, reserved-word/collision checks, UTM builder
- 📊 **Privacy-respecting analytics** — visit trends, top countries/devices/browsers/OS/referrers, date-range filters, CSV/JSON export
- 🧭 **Recon & OSINT toolkit** — subdomain enumeration, DNS propagation checks, technology detection, robots.txt/sitemap parsing, cookie analysis, WHOIS, SSL inspection
- 🛡️ **Security Center** — DNS/WHOIS/SSL checks, security-headers analyzer, reputation scoring, combined into a 0–100 score with history
- 📱 **QR codes** — server-generated PNG/SVG, customizable size/colors/error-correction, optional embedded logo
- 🧰 **URL tools** — encoder/decoder, UTM builder, SSRF-hardened URL analyzer, redirect-chain checker
- 🔑 **Tiered API keys** — Free/Pro/Business, hashed at rest, per-tier rate limits
- 🪝 **Webhooks** — HMAC-signed, event-driven, async delivery with retry backoff and a delivery log
- 🔔 **Notifications** — in-app + email, triggered by first visits, expirations, webhook failures, low security scores
- 🔐 **Serious auth** — refresh-token rotation, email verification, password reset, 2FA (TOTP + backup codes), session management, RBAC (`SUPER_ADMIN → ADMIN → MANAGER → USER → VIEWER`) enforced server-side
- 📲 **Devices module** — AirDroid-style remote screen control via a companion Android client

## Feature tour

### Links & campaigns
Create tracked links with custom aliases, expiration dates, password protection, and an optional visitor consent gate. Group links into campaigns and drill into per-campaign performance: total clicks, unique visitors, CTR, top country/device/browser, and a visit timeline. The redirect system never trusts request input for its target — the destination is only ever read back from the database, closing off the usual open-redirect surface.

### Analytics
A filterable, exportable analytics page: stat cards, visit trends over time, and breakdowns by country, device, browser, OS, and referrer. Every visit records IP intelligence (mock provider by default, real-provider adapter ready to wire in) and UA-derived signals, including a bot-confidence score. The raw client IP is recorded on every visit; the richer device/browser/UTM fingerprint is only captured when the visitor has explicitly consented (see [`docs/SECURITY.md`](./docs/SECURITY.md#privacy)).

### Security Center & recon/OSINT
Analyze any domain you own or are authorized to test:

- DNS records, DNS propagation across resolvers, WHOIS, SSL certificate details
- Subdomain enumeration and technology/stack detection
- `robots.txt` / sitemap parsing
- Cookie analysis (flags, scope, security attributes)
- Security-headers analyzer (CSP, HSTS, X-Frame-Options, etc.) and a reputation check (mock by default, real adapter ready)

All findings roll up into a single 0–100 security score with full scan history.

### QR codes & URL tools
Generate a QR code (PNG/SVG) for any link with configurable size, colors, error-correction level, and an optional embedded logo. The URL tools page adds an encoder/decoder, a UTM builder, an SSRF-hardened URL analyzer (title/description/favicon preview), and a redirect-chain checker.

### API, webhooks & notifications
Issue tiered API keys (Free/Pro/Business) as an alternate credential for the whole API — shown once, hashed at rest, rate-limited per tier. Subscribe to webhooks (`link.created/clicked`, `campaign.created/completed`, `security.alert`) delivered with HMAC signatures, async retry backoff, and a delivery log. The in-app + email notification center covers a link's first visit, link expiry, webhook failures, and low security scores, with per-type email preferences.

### Devices (remote control)
A companion Android client (`android/`) pairs with the platform to enable AirDroid-style remote screen viewing/control, built alongside its own signaling protocol (see [`docs/DEVICE_CONTROL_PROTOCOL.md`](./docs/DEVICE_CONTROL_PROTOCOL.md)).

### Security baseline (platform-wide)
Rate limiting, security headers, CORS, a standard error envelope, structured JSON logs, an audit log, IDOR-safe ownership checks throughout, and SSRF-hardened outbound fetching everywhere a user-supplied URL is fetched server-side.

## Screenshots

Every screen below is a real capture of the running app (light and dark theme, empty states and populated ones) — not mockups.

### Sign-in & account

<table>
<tr>
<td width="33%"><img src="docs/screenshots/01-login.png" alt="Login page"><br><sub>Login</sub></td>
<td width="33%"><img src="docs/screenshots/02-register.png" alt="Register page"><br><sub>Create an account</sub></td>
<td width="33%"><img src="docs/screenshots/03-forgot-password.png" alt="Forgot password page"><br><sub>Password reset</sub></td>
</tr>
</table>

### Dashboard — light & dark

<table>
<tr>
<td width="50%"><img src="docs/screenshots/04-dashboard.png" alt="Dashboard, light theme"><br><sub>Light theme</sub></td>
<td width="50%"><img src="docs/screenshots/20-dashboard-dark.png" alt="Dashboard, dark theme"><br><sub>Dark theme</sub></td>
</tr>
</table>

A summary across every project: total links, visits, unique visitors, today's visits, active projects, and a uniqueness ratio, plus a visit trend chart and top countries/devices/browsers/referrers.

### Projects — from empty state to a live campaign

<table>
<tr>
<td width="50%"><img src="docs/screenshots/05-projects-empty.png" alt="Projects page, empty state"><br><sub>1. Empty state — first-run guidance</sub></td>
<td width="50%"><img src="docs/screenshots/06-projects-create.png" alt="Create project dialog"><br><sub>2. Create a project</sub></td>
</tr>
<tr>
<td width="50%"><img src="docs/screenshots/07-projects-list.png" alt="Projects list with a campaign"><br><sub>3. The new project, in the list</sub></td>
<td width="50%"><img src="docs/screenshots/08-project-detail.png" alt="Project detail page"><br><sub>4. Project detail — performance at a glance</sub></td>
</tr>
</table>

### Links — creating a tracked link end to end

<table>
<tr>
<td width="50%"><img src="docs/screenshots/09-links-empty.png" alt="Links page, empty state"><br><sub>1. Empty state</sub></td>
<td width="50%"><img src="docs/screenshots/10-links-create.png" alt="Create tracking link dialog"><br><sub>2. Destination, alias, options, UTM tags</sub></td>
</tr>
<tr>
<td colspan="2"><img src="docs/screenshots/11-links-list.png" alt="Links list with created links"><br><sub>3. Both links, ready to track — visits, uniques, status, and per-row actions</sub></td>
</tr>
</table>

### Analytics

<p align="center"><img src="docs/screenshots/12-analytics.png" alt="Analytics page" width="860"></p>

### URL Solutions toolkit

<p align="center"><img src="docs/screenshots/13-url-tools.png" alt="URL Solutions — encode/decode, UTM builder, analyzer, redirect checker, QR codes" width="860"></p>

### Security Center (recon / OSINT)

<p align="center"><img src="docs/screenshots/14-security.png" alt="Security Center — domain reconnaissance" width="860"></p>

### Platform — API, webhooks, notifications, devices, settings

<table>
<tr>
<td width="50%"><img src="docs/screenshots/15-api.png" alt="API keys page"><br><sub>Tiered API keys</sub></td>
<td width="50%"><img src="docs/screenshots/16-webhooks.png" alt="Webhooks page"><br><sub>Webhooks</sub></td>
</tr>
<tr>
<td width="50%"><img src="docs/screenshots/17-notifications.png" alt="Notifications page"><br><sub>Notifications</sub></td>
<td width="50%"><img src="docs/screenshots/18-devices.png" alt="Devices page"><br><sub>Devices (remote control)</sub></td>
</tr>
<tr>
<td colspan="2"><img src="docs/screenshots/19-settings.png" alt="Settings page"><br><sub>Settings</sub></td>
</tr>
</table>

### Empty & error states

Handled deliberately, not left as blank screens:

<table>
<tr>
<td width="50%"><img src="docs/screenshots/21-404.png" alt="404 page"><br><sub>404 — unknown app route</sub></td>
<td width="50%"><img src="docs/screenshots/22-link-not-found.png" alt="Tracking link not found page"><br><sub>Unknown/expired tracking link</sub></td>
</tr>
</table>

## Architecture

```mermaid
flowchart TB
    NGINX[nginx — reverse proxy]
    FE[Frontend — React + TS + Vite]
    BE[Backend — FastAPI + async SQLAlchemy]
    PG[(PostgreSQL<br/>primary store)]
    REDIS[(Redis<br/>cache / queue / rate limit)]
    WORKER[Background worker<br/>emails, webhooks, jobs]
    EXT[[External integrations<br/>IP intel · reputation · email · domain intel<br/>all adapter-based & mockable]]

    NGINX --> FE
    NGINX --> BE
    FE <-- REST API --> BE
    BE --> PG
    BE --> REDIS
    BE --> WORKER
    WORKER --> PG
    WORKER --> REDIS
    BE -.-> EXT
    WORKER -.-> EXT
```

Backend modules under `backend/app/`:

```text
app/
├── api/v1/          REST endpoints (auth, campaigns, links, analytics, tracking,
│                    qr, url_tools, security_center, api_keys, webhooks,
│                    notifications, devices, dashboard)
├── core/            config, DB session, settings
├── models/          SQLAlchemy models
├── schemas/         Pydantic request/response schemas
├── services/        business logic (one service per domain)
├── repositories/    data-access layer
├── middleware/      rate limiting, security headers, error envelope
├── security/        auth, RBAC, hashing, tokens
├── analytics/       aggregation logic
├── integrations/    provider adapters — ip_intelligence/, reputation/, email/, domain_intel/
├── workers/         background job handlers
└── utils/
```

## Project structure

```text
Aventrix/
├── android/       companion Android client (device control)
├── backend/       FastAPI application + Alembic migrations + tests
├── frontend/      React + TypeScript + Vite SPA
├── worker/        background worker Dockerfile/entrypoint
├── nginx/         reverse proxy config (dev + production)
├── docker/        supporting Docker assets
├── scripts/       dev-setup helpers, DB backup, Let's Encrypt init
├── docs/          SETUP, ARCHITECTURE, DATABASE, API, SECURITY,
│                  ENVIRONMENT, DEPLOYMENT, DEPLOY_VPS, CONTRIBUTING,
│                  DEVICE_CONTROL_PROTOCOL
├── docker-compose.yml       development stack
├── docker-compose.prod.yml  production stack
├── LICENSE
└── .env.example   every configurable environment variable
```

## Tech stack

**Frontend** — React 18 · TypeScript · Vite · Tailwind CSS · Radix primitives · TanStack Query · React Router

**Backend** — Python · FastAPI · Pydantic · SQLAlchemy (async) · Alembic

**Data** — PostgreSQL · Redis (cache, rate limiting, queue)

**Infra** — Docker Compose · nginx · a dedicated background worker service

**Mobile** — Kotlin / Android (companion device-control client)

## Quick start

**With Docker (recommended):**

```bash
cp .env.example .env      # edit secrets/URLs as needed
docker compose up
```

Or run `scripts/dev-setup.ps1` (Windows) / `scripts/dev-setup.sh` (macOS/Linux) — it creates `.env` for you and checks whether Docker is on your PATH.

This brings up Postgres, Redis, the API, the background worker, the frontend dev server, and nginx. Migrations and a development admin seed run automatically on backend startup — watch the logs for a one-time printed admin password.

| Service | URL |
| --- | --- |
| App (via nginx) | http://localhost:8080 |
| Frontend directly | http://localhost:5173 |
| API docs (Swagger) | http://localhost:8000/api/docs |

**Without Docker:** see [`docs/SETUP.md`](./docs/SETUP.md) for running the backend and frontend locally against your own Postgres/Redis.

**Android client:** see [`android/README.md`](./android/README.md) to build the companion app (`./gradlew assembleDebug`).

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
| [DEPLOY_VPS.md](./docs/DEPLOY_VPS.md) | Step-by-step VPS deployment |
| [DEVICE_CONTROL_PROTOCOL.md](./docs/DEVICE_CONTROL_PROTOCOL.md) | Remote device-control signaling protocol |
| [CONTRIBUTING.md](./docs/CONTRIBUTING.md) | Code style, testing, PR expectations |

## Security & privacy

This platform is built around a strict rule: **no covert data collection.** Every feature that touches a visitor's device or data goes through explicit consent, never a silent default. Concretely:

- Visitor consent is a first-class UI step before any device/browser/UTM fingerprint is captured
- All external integrations (IP intelligence, reputation, email, domain intel) are adapter-based, configured via environment variables, and degrade gracefully with a mock provider when no key is configured — the app never crashes because a third-party key is missing
- Outbound fetches of user-supplied URLs (link previews, domain analysis, redirect checks) are SSRF-hardened: private IP ranges, localhost, internal networks, and cloud metadata endpoints are all blocked, with timeouts, response-size limits, and redirect limits enforced
- Authorization is checked server-side on every request (RBAC), not just hidden in the UI — no IDOR by ID-guessing
- Passwords, JWT secrets, and API keys are never hard-coded; secrets live only in `.env` (see `.env.example`)

Full threat model and known advisories live in [`docs/SECURITY.md`](./docs/SECURITY.md).

> **Responsible use only.** The recon/OSINT and Security Center tooling (subdomain enumeration, DNS/WHOIS/SSL checks, header/reputation analysis) is intended for domains and assets you own or are explicitly authorized to test.

## Testing

```bash
# Backend
cd backend && pytest

# Frontend
cd frontend && npm test
```

Tests are written alongside features, not bolted on afterward — unit coverage for auth, link generation, validation, analytics, and the IP service; integration coverage for the database, API, auth flow, and redirect system; dedicated security tests for IDOR, SSRF, and rate limiting; component/form/navigation tests on the frontend.

## Roadmap (not yet built)

PDF report export · real-time SSE/WebSocket live-visitor dashboard · AI campaign/analytics assistant · full admin panel · multi-user workspaces · billing/subscriptions · CI/CD pipeline.

See [`docs/ARCHITECTURE.md`](./docs/ARCHITECTURE.md) for the complete built-vs-deferred breakdown.

## License

Released under the [MIT License](./LICENSE) — see the file for the full text.
