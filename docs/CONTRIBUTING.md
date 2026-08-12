# Contributing

## Before opening a PR

Backend:

```bash
cd backend
ruff check app/ scripts/ tests/
pytest
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run lint
npm run test
npm run build
```

All four frontend checks and both backend checks should pass. Tests are written alongside the code they cover, not after — if you add an endpoint or a non-trivial function, add its test in the same change.

## Style

- Backend: type hints everywhere, service layer stays framework-agnostic (raises domain exceptions from `app/services/exceptions.py`, not `HTTPException` — the API layer translates), repositories are thin query helpers, no business logic in routers beyond orchestration.
- Frontend: function components + hooks, TanStack Query for all server state (no ad hoc `useEffect` fetching), Zod schemas colocated with the form that uses them.
- No dead code, no speculative abstraction for features that don't exist yet. If something is deferred, it's absent, not stubbed.

## Security-sensitive changes

Anything touching auth, the redirect/consent flow, IDOR-relevant ownership checks, or external URL fetching should include a test that would fail without the fix, not just a manual check.
