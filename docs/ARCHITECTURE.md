# Architecture

## Layout

```text
Aventrix/
├── backend/
│   └── app/
│       ├── main.py            FastAPI app, middleware, mounts
│       ├── api/                route handlers (v1/*, redirect.py)
│       ├── core/                config, security, rate limiting, logging, errors, cookies
│       ├── models/               SQLAlchemy models + portable GUID/JSON types
│       ├── schemas/              Pydantic request/response models
│       ├── services/             business logic, framework-agnostic
│       ├── repositories/         thin DB query helpers
│       ├── integrations/         external-provider adapters (email, ip_intelligence, domain_intel, reputation)
│       ├── workers/               queue.py (producer), runner.py (consumer), scheduler.py (periodic sweep)
│       ├── analytics/            UA parsing, bot-confidence heuristic
│       └── middleware/            security headers
├── worker/Dockerfile           runs `python -m app.workers.runner`
├── frontend/src/
│   ├── pages/                   route-level components
│   ├── components/               ui/ (design system), layout/, feature components
│   ├── hooks/                    TanStack Query hooks per resource
│   └── lib/                      api client, types, utils
├── nginx/nginx.conf             prod-shaped reverse proxy (one origin)
└── docker-compose.yml
```

## Request flow: a tracking link click

```text
Visitor clicks https://domain/t/ABC123
        │
        ▼
GET /t/{code}  (app/api/redirect.py)
        │
        ├─ link missing/expired/disabled → 302 → {frontend}/t/not-found
        │
        ├─ needs password or consent → 302 → {frontend}/t/{code}/gate
        │        │
        │        ▼
        │   frontend calls GET /api/v1/t/{code}/meta (needs_password / needs_consent)
        │   visitor submits password and/or accepts/declines consent
        │        │
        │        ▼
        │   POST /api/v1/t/{code}/resolve → records Visit, returns target_url
        │   frontend does window.location.href = target_url
        │
        └─ no gate needed → records Visit inline → 302 straight to target_url
```

`record_visit()` (`app/services/visit_service.py`) always writes synchronously and fast — no external calls. If consent was given, `dispatch_ip_enrichment()` pushes a job onto a Redis-backed queue (`app/workers/queue.py`); a separate worker process (`app/workers/runner.py`) consumes it and fills in geo/ISP/VPN fields via the IP-intelligence provider chain. The raw IP is passed through the queue message only — it is never written to the database, only its salted hash (see `docs/SECURITY.md`).

## Why a hand-rolled queue instead of Celery

Section 7 of the spec allows "Celery or a modern async task system." Celery's synchronous kombu client, invoked inline from an async FastAPI request handler, turned out to hang indefinitely in this environment when the broker was unreachable — its own configured socket timeouts weren't honored, and the blocked worker thread outlived any `asyncio.wait_for` wrapped around it (a `concurrent.futures` thread pool won't let the process exit while a job is stuck). `redis.asyncio` — already used successfully by the rate limiter — doesn't have that failure mode: it fails fast and predictably, so `app/workers/queue.py` builds directly on it (a Redis list as the job queue, `BLPOP` in the consumer). It's ~60 lines total and keeps the whole request path async-native with no thread-pool escape hatch.

## Provider adapters

External integrations never crash the app or require a real key to run:

- `app/integrations/email/` — `MockEmailProvider` (logs + in-memory outbox, default) and `SmtpEmailProvider` (real, inert until `SMTP_*` is set)
- `app/integrations/ip_intelligence/` — `MockIPIntelligenceProvider` (deterministic per-IP sample data, default) and `IpinfoProvider` (real, inert until `IP_INTELLIGENCE_API_KEY` is set), selected via a fallback chain in `factory.py`
- `app/integrations/reputation/` — same shape, `MockReputationProvider` (default) and `SafeBrowsingReputationProvider` (real, inert until `REPUTATION_API_KEY` is set), used by Security Center
- `app/integrations/domain_intel/` — DNS (`dnspython`) and WHOIS (`python-whois`) lookups, plus an SSL certificate check (stdlib `ssl`/`socket`). These are always real, not mock/real-adapter pairs — DNS and WHOIS are open protocols needing no API key, and a direct TLS handshake is the only way to actually read a certificate

Email/IP/reputation all follow the same shape: an abstract base class, an `is_configured` property, a `mock`/`use_mock_providers` switch in settings, and a factory function — so adding a real maps provider later is a new file, not a refactor.

## SSRF-safe server-side fetching

`app/utils/url_validation.py` is a cheap, string-only pre-check used at link-creation time (it never issues a request itself). Anything that actually fetches a user-supplied URL server-side — URL Tools' analyzer/redirect-checker, Security Center's header check, webhook delivery — goes through `app/utils/safe_fetch.py` instead, which resolves DNS itself and validates the *resolved* IP before connecting, and re-validates on every hop of a redirect chain rather than trusting httpx's built-in following. See `docs/SECURITY.md` for the documented residual risk (no IP-pinning on the TLS connection).

## Background worker: multiple queues + a periodic sweep

`app/workers/runner.py` now runs three tasks concurrently via `asyncio.gather`: the original visit-enrichment consumer, a webhook-delivery consumer (`app/workers/queue.py`'s `WEBHOOK_DELIVERY_QUEUE`), and a periodic sweep (`app/workers/scheduler.py`, every `WORKER_SWEEP_INTERVAL_SECONDS`) that retries due webhook deliveries and sends `LINK_EXPIRED` notifications for links that just expired. There's still no external scheduler dependency — the sweep is a plain `asyncio.sleep` loop, which is the smallest thing that satisfies "retry later" and "check periodically" without pulling one in.

## Devices module: remote screen control (WebRTC signaling)

`app/api/v1/devices.py` + `app/services/device_service.py` / `device_signaling_service.py` / `turn_credential_service.py` implement pairing and WebRTC signaling for controlling a user's own paired Android device from the browser. Full protocol and threat-model details live in `docs/DEVICE_CONTROL_PROTOCOL.md`; summary:

- **First real-time feature in the app.** Everything above this module is request/response; this adds a `WebSocket` endpoint (`WS /api/v1/devices/sessions/{session_id}/signal`) purely for SDP/ICE signaling — no media, no dashboard live-updates. It's unrelated to `ENABLE_REALTIME` (that flag is reserved for a future live-updating dashboard) and has its own flag, `ENABLE_DEVICE_CONTROL` (default **off**).
- **No media touches the backend.** The signaling relay (Redis pub/sub, mirroring `workers/queue.py`'s `redis.asyncio` usage) only ever forwards small JSON offer/answer/ICE messages between the two peers of a session. Actual video/input traffic is peer-to-peer WebRTC, optionally relayed through the `coturn` container — the FastAPI process structurally cannot record or inspect it.
- **No mock mode for TURN.** Unlike the other integrations above, there's no meaningful fake for NAT traversal. `coturn` is required infra for cross-network sessions, but same-machine/same-LAN connections (including this module's own test suite and the browser-to-browser loopback in `docs/DEVICE_CONTROL_PROTOCOL.md`) work over STUN/direct candidates alone. The whole module is gated behind `ENABLE_DEVICE_CONTROL`, so an unconfigured `coturn` never surfaces as an error elsewhere.
- **Android client is a separate, later deliverable.** This backend/frontend pass ships the full pairing + signaling contract (`docs/DEVICE_CONTROL_PROTOCOL.md`) and a working web-to-web loopback; no Android app exists yet. `MediaProjection` (screen capture) and `AccessibilityService` (input injection) both require explicit, OS-enforced user consent on the device — the same consent-first posture this app already applies to the tracking-link consent gate.

## What's built vs. deferred

Built (spec phases 1–16 plus the analytics/API/notification pieces of later phases): architecture, database, auth+RBAC, dashboard, URL system, redirect system, consent, analytics (dashboard + a filterable/exportable Analytics page), IP intelligence, QR code generation, URL Tools (encode/decode, UTM builder, analyzer, redirect checker), Security Center (DNS/WHOIS/SSL/headers/reputation scoring), API key management, webhooks, notification center (in-app + email), Devices module backend + web frontend (pairing, WebRTC signaling; `ENABLE_DEVICE_CONTROL` stays off by default).

Deferred: PDF export (CSV/JSON only), real-time SSE/WebSocket dashboard (`ENABLE_REALTIME` stays off), AI campaign/analytics assistant (`ENABLE_AI` stays off), admin panel, workspaces/teams, billing/subscriptions, CI/CD pipeline, full production-hardening checklist, the Devices module's Android client (see `docs/DEVICE_CONTROL_PROTOCOL.md`).
