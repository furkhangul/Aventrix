# Deployment

This build targets a single-VPS Docker Compose deployment (Postgres + Redis + backend + worker + frontend + nginx), matching `docker-compose.yml`. This checklist is the *why*; **`docs/DEPLOY_VPS.md` is the concrete, copy-pasteable walkthrough** (`docker-compose.prod.yml`, TLS via Let's Encrypt, a production nginx/frontend build) — start there if you're actually deploying.

## Production-shaped changes from local dev

- `APP_ENV=production` — disables the auto-seeded admin account (`scripts/seed.py` becomes a no-op)
- `COOKIE_SECURE=true` — cookies require HTTPS
- `APP_DEBUG=false`
- Real, unique `APP_SECRET_KEY` and `JWT_SECRET_KEY` (never reuse the `.env.example` placeholders)
- Terminate TLS in front of `nginx` (or configure certs directly in `nginx/nginx.conf`) and add an HTTP→HTTPS redirect block — the current config only handles the single unified origin, no TLS termination is configured
- Point `DATABASE_URL`/`REDIS_URL` at managed or hardened instances rather than the compose-local containers, if scaling beyond one host
- Build the frontend for production (`docker/frontend.Dockerfile` currently runs the Vite **dev** server — for production, build a static bundle with `npm run build` and serve `dist/` via nginx directly instead of proxying to the Vite dev server)

## Pre-deploy checklist

- [ ] HTTPS terminated, HTTP redirects to HTTPS
- [ ] `APP_SECRET_KEY` / `JWT_SECRET_KEY` are real random values, not the example placeholders
- [ ] `.env` is not committed and not baked into any image layer
- [ ] `COOKIE_SECURE=true`, `APP_ENV=production`
- [ ] Database backups configured (not automated by this build — see below)
- [ ] Rate limiting verified against a real Redis (not the in-memory fallback)
- [ ] CORS origins (`CORS_ORIGINS`) restricted to the real frontend origin
- [ ] Security headers verified present (`curl -I` your deployed origin)
- [ ] Structured logs shipped somewhere durable; confirm no secrets appear in them
- [ ] `/health` and `/ready` wired into your orchestrator's health checks
- [ ] Frontend built for production, not served via the dev server

## Backups

Not automated in this build. For Postgres, the standard approach is a scheduled `pg_dump` (or your managed provider's snapshot feature) with a retention window and a documented, *tested* restore procedure — untested backups are not backups. This is flagged as a gap, not implemented, to avoid a false sense of coverage.

## Data retention

`ip_intelligence` cache rows carry an `expires_at` (24h TTL) but nothing currently purges expired rows or old `visits` — see `docs/DATABASE.md`. A scheduled cleanup job is natural future work alongside the "Scheduled Tasks" phase.
