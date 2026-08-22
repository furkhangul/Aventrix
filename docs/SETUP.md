# Setup

## Option A — Docker (recommended)

Requires Docker Desktop.

```bash
cp .env.example .env
docker compose up
```

What happens on `backend` container start:

1. `alembic upgrade head` — applies all migrations
2. `python -m scripts.seed` — creates a development `SUPER_ADMIN` account (`SEED_ADMIN_EMAIL` in `.env`) with a **randomly generated password printed once to the console**. It's idempotent: re-running never resets or overwrites an existing account's password. In `APP_ENV=production` this step is skipped entirely — no auto-created account in production.
3. `uvicorn` starts with `--reload`

Services and ports:

| Service | Port | Notes |
| --- | --- | --- |
| `nginx` | 8080 | Unified origin — frontend + `/api` + `/t` behind one host, closest to production |
| `frontend` | 5173 | Vite dev server, hot reload |
| `backend` | 8000 | FastAPI, Swagger at `/api/docs` |
| `postgres` | 5432 | |
| `redis` | 6379 | |
| `worker` | — | Background job consumer (IP-intelligence enrichment queue), no exposed port |

Stop with `docker compose down`. Add `-v` to also drop the Postgres/Redis volumes.

## Option B — Manual local setup

You'll need Python 3.12+, Node 20+, a local PostgreSQL instance, and a local Redis instance (or accept that rate limiting/background enrichment fall back to reduced-functionality modes without Redis — see `docs/SECURITY.md`).

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS/Linux

pip install -r requirements-dev.txt   # includes requirements.txt + test tooling

# .env at the repo root is read via `../.env` when running from backend/
cp ../.env.example ../.env
# edit DATABASE_URL / REDIS_URL to point at your local instances, e.g.:
#   DATABASE_URL=postgresql+asyncpg://aventrix:change-me@localhost:5432/aventrix
#   REDIS_URL=redis://localhost:6379/0

alembic upgrade head
python -m scripts.seed
uvicorn app.main:app --reload
```

Run the worker in a second terminal:

```bash
cd backend && .venv\Scripts\activate
python -m app.workers.runner
```

Run tests (self-contained — uses an in-memory SQLite database, no live Postgres needed):

```bash
pytest
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` and `/t` to `http://localhost:8000` (see `vite.config.ts`) — no CORS setup needed for local dev regardless of which port you open the app on.

Frontend checks:

```bash
npm run typecheck
npm run lint
npm run test
npm run build
```

## First login

1. Watch the backend startup logs for the seeded admin email + one-time password (Docker) or run `python -m scripts.seed` yourself (manual setup).
2. Sign in, or just register a new account — registration auto-verifies nothing but logs you in immediately; email verification is a separate, non-blocking step in this build.
3. Create a campaign, create a link, visit `/t/<code>` in a browser to see the consent/redirect flow, then check the dashboard.
