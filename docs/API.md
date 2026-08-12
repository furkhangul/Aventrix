# API

Full interactive reference: `GET /api/docs` (Swagger UI) or `GET /api/openapi.json`. This page is a map, not a spec.

All endpoints are versioned under `/api/v1`. Auth is via an HttpOnly `access_token` cookie (short-lived) + `refresh_token` cookie (rotated on use) — there is no bearer token in response bodies by design (nothing for XSS to steal from JS-readable storage). A `Bearer <api_key>` header (see API keys below) is also accepted by `get_current_user` and authenticates against every endpoint a session cookie would — it's an alternate credential, not a separate API surface.

Every error response uses the same envelope:

```json
{ "error": { "message": "...", "code": 422, "details": [ /* present on 422 only */ ] } }
```

## Auth — `/api/v1/auth`

| Method & path | Notes |
| --- | --- |
| `POST /register` | Rate-limited. Auto-logs in on success. |
| `POST /login` | Rate-limited. Returns `requires_2fa` + a short-lived pending token if 2FA is enabled, instead of a session. |
| `POST /2fa/verify-login` | Exchanges the pending token + TOTP/backup code for a real session. |
| `POST /logout` / `POST /refresh` | Refresh rotates: old session revoked, new one issued. |
| `GET /me` / `PATCH /me` / `POST /me/avatar` / `DELETE /me` | Avatar upload is type/size-restricted, filename never derived from user input. |
| `GET /sessions` / `DELETE /sessions/{id}` | IDOR-checked — only your own sessions. |
| `GET /login-history` | Paginated audit log filtered to login events. |
| `POST /forgot-password` / `POST /reset-password` | Reset never reveals whether the email exists; completing a reset revokes all other sessions. |
| `POST /change-password` | Revokes all sessions except the current one. |
| `POST /verify-email` / `POST /resend-verification` | |
| `POST /2fa/setup` / `POST /2fa/confirm` / `POST /2fa/disable` / `POST /2fa/backup-codes/regenerate` | |

## Campaigns — `/api/v1/campaigns`

Standard CRUD (`POST`, `GET` list w/ pagination+search+status filter, `GET /{id}`, `PATCH /{id}`, `DELETE /{id}`). List/detail responses include `link_count`, `total_visits`, `unique_visitors` (batched aggregation, not N+1). Every read/write is scoped to `Campaign.user_id == current_user.id` — a different user's campaign 404s, it doesn't 403 (existence isn't leaked).

## Links — `/api/v1/links`

Same CRUD shape, plus `PUT /{id}/password` to set/clear password protection independently. `POST /` validates the target URL (scheme allowlist + blocks localhost/link-local/metadata-IP targets), checks alias collisions and the reserved-word list, and generates a random 7-character code when no custom alias is given.

## Dashboard — `/api/v1/dashboard`

| Path | Returns |
| --- | --- |
| `GET /summary?range=` | total/unique visits, today's visits, active campaigns, links, uniqueness rate |
| `GET /timeseries?range=` | daily visit counts for the range |
| `GET /top/{dimension}?range=` | `dimension` ∈ `country, device, browser, referrer, os` |

`range` ∈ `today, yesterday, 7d, 30d, 90d, custom` (custom needs `start`/`end` ISO datetimes). All queries are scoped to the current user's own links via a join — never global.

## Analytics — `/api/v1/analytics`

| Method & path | Notes |
| --- | --- |
| `GET /overview?range=&link_id=&campaign_id=` | Same shape as dashboard summary/timeseries/top-dimension, but filterable to one link or campaign. `link_id`/`campaign_id` are ownership-checked — a filter naming another user's resource 404s. |
| `GET /export?range=&link_id=&campaign_id=&format=csv\|json` | Streams a downloadable report (totals + top-5 breakdowns per dimension). No PDF export — CSV/JSON only. |

## QR Codes — `/api/v1/qr` (behind `ENABLE_QR`)

| Method & path | Notes |
| --- | --- |
| `GET /generate?data=&size=&fg_color=&bg_color=&error_correction=&format=png\|svg&logo_id=` | Stateless — generates and streams the image on every call, nothing persisted. |
| `GET /links/{link_id}?...` | Same params, but resolves an owned link's short URL server-side instead of taking `data` directly. |
| `POST /logo` | Multipart upload (PNG/JPEG/WEBP, ≤1MB) for the optional center logo; returns a `logo_id` to pass to the generate calls. |

## URL Tools — `/api/v1/url-tools`

| Method & path | Notes |
| --- | --- |
| `POST /analyze` | SSRF-hardened fetch of the given URL; returns final URL, status, timing, content-type, and (for HTML) title/description/favicon. Rate-limited. |
| `POST /redirect-check` | Follows the redirect chain manually, re-validating SSRF safety on *every* hop (max 10), so a safe first URL can't hide a redirect to an internal address. Rate-limited. |

Encode/decode and the UTM builder are pure frontend utilities — no backend calls.

## Security Center — `/api/v1/security-center` (behind `ENABLE_DOMAIN_ANALYZER`)

| Method & path | Notes |
| --- | --- |
| `POST /scan` | Runs DNS (dnspython), WHOIS (python-whois), an SSL certificate check (stdlib `ssl`/`socket`), a security-headers check, and a reputation check (mock by default; real adapter needs `REPUTATION_API_KEY`) against a domain; persists the result and computes a 0–100 score (headers 35% / SSL 35% / reputation 30%). A score below `SECURITY_SCAN_ALERT_THRESHOLD` fires a `security.alert` webhook event and a notification. Rate-limited. |
| `GET /scans` / `GET /scans/{id}` | Paginated scan history, ownership-scoped. |

## API keys — `/api/v1/api-keys`

| Method & path | Notes |
| --- | --- |
| `POST ""` | Body: `{name, tier}` (`FREE`/`PRO`/`BUSINESS`). Returns the raw key (`fw_live_...`) exactly once — only its hash is ever stored. |
| `GET ""` | Masked list (`key_prefix` only). |
| `POST /{id}/rotate` | Revokes the old key, issues a new one with the same name/tier, returns the new raw key once. |
| `DELETE /{id}` | Revokes. |

Keys authenticate like a JWT (see above) and are rate-limited per tier on a rolling 24h window (`RATE_LIMIT_API_KEY_{FREE,PRO,BUSINESS}_PER_DAY`).

## Webhooks — `/api/v1/webhooks` (behind `ENABLE_WEBHOOK`)

| Method & path | Notes |
| --- | --- |
| `POST ""` | Body: `{url, description?, events[]}`. `url` is SSRF-validated at creation *and* re-validated on every delivery attempt. Returns the signing secret (`whsec_...`) once. |
| `GET ""` / `PATCH /{id}` / `DELETE /{id}` | Standard CRUD; list/detail never re-expose the full secret, only a masked preview. |
| `POST /{id}/test` | Sends a synthetic `webhook.test` delivery immediately (not queued) for setup verification. |
| `GET /{id}/deliveries` | Paginated delivery log (status, response code, attempt count, next retry time). |

Events: `link.created`, `link.clicked`, `campaign.created`, `campaign.completed`, `security.alert`. Delivery is async (Redis-queued, consumed by the worker process), signed via `X-Webhook-Signature: sha256=<hmac>` over the raw JSON body, and retried on failure with backoff (2m/10m/30m/2h/6h, capped at `WEBHOOK_MAX_RETRY_ATTEMPTS`); a delivery that exhausts all retries triggers a `WEBHOOK_DELIVERY_FAILED` notification.

## Notifications — `/api/v1/notifications`

| Method & path | Notes |
| --- | --- |
| `GET ""?unread_only=&page=` | Paginated, includes `unread_count`. |
| `PATCH /{id}/read` / `POST /read-all` / `DELETE /{id}` | |
| `GET /preferences` / `PATCH /preferences` | Per-type email on/off switches (`{"LINK_EXPIRED": false, ...}`); a type absent from the map defaults to enabled. |

Triggers: a link's first-ever visit, a link expiring (swept by the worker), a webhook's final delivery failure, and a security scan below the alert threshold. Each also sends an email via the existing mock/SMTP provider unless the user has disabled that type.

## Public tracking — `/t/{code}` and `/api/v1/t/{code}/*`

No auth. `GET /t/{code}` is the literal short-link entry point (redirect or gate). `GET /api/v1/t/{code}/meta` and `POST /api/v1/t/{code}/resolve` back the consent/password gate page — see `docs/ARCHITECTURE.md` for the full flow.

## System

`GET /health` (liveness, no dependency checks) and `GET /ready` (checks Postgres + Redis, returns 503 if either is down).
