# Demo Carwash Backend API

FastAPI backend for carwash operations with modular architecture, role-based access control, async PostgreSQL access, idempotent command handling, and rate-limited critical endpoints.

## What This Project Covers

- Auth and session endpoints (`/api/v1/auth/*`)
- Account management (`/api/v1/accounts/*`)
- Service type management (`/api/v1/service-types/*`)
- Ticket operations (`/api/v1/tickets/*`)
- Billing transactions (`/api/v1/transactions/*`)
- Analytics reporting (`/api/v1/analytics/*`)
- Health and DB smoke-check endpoints

## Recent Updates

- Migrated dependency injection style to `Annotated[..., Depends(...)]` across route and dependency layers.
- Added targeted API limiter rules on important write endpoints.
- Refined billing unit-of-work transaction lifecycle handling (`commit`/`rollback` completion state and cleanup).
- Moved billing request hasher interface from `application/services` to `application/ports`.

## Tech Stack

- Python 3.12
- FastAPI
- PostgreSQL 16
- SQLAlchemy + asyncpg
- Pydantic v2
- slowapi (rate limiting)
- pytest + ruff
- Docker / Docker Compose

## Architecture

The codebase follows a modular, clean-architecture style under `app/modules/*`:

- `api`: HTTP routes, request/response schema mapping, dependency wiring
- `application`: use cases, DTOs, query models, ports
- `domain`: entities, value objects, repository contracts
- `infra`: DB repositories, adapters, unit of work, concrete implementations

Shared infrastructure lives in `app/shared/*` (settings, middleware, DB lifespan, error handlers, interfaces).

## API Base Path

All API endpoints are mounted under:

- `/api/v1`

Main route registration is in `app/api/v1/router.py`.

## Current Rate Limits

Global limiter integration is configured in `app/main.py`. Endpoint-level limits currently include:

- `GET /api/v1/health` -> `5/minute`
- `GET /api/v1/test-db` -> `10/minute`
- `POST /api/v1/auth/login` -> `10/second`
- `POST /api/v1/auth/refresh` -> `10/second`
- `POST /api/v1/auth/logout` -> `10/second`
- `POST /api/v1/accounts` -> `10/minute`
- `POST /api/v1/service-types` -> `10/minute`
- `PATCH /api/v1/service-types/{service_type_id}` -> `20/minute`
- `DELETE /api/v1/service-types/{service_type_id}` -> `10/minute`
- `POST /api/v1/tickets` -> `30/minute`
- `PATCH /api/v1/tickets/{ticket_id}/void` -> `20/minute`
- `POST /api/v1/transactions` -> `20/minute`

## Project Structure

```text
app/
  api/
    dependencies/
    v1/
  modules/
    analytics/
    billing/
    carwash_operation/
    identity/
    service_catalog/
  shared/
    config/
    error_handling/
    infra/
    interfaces/
    middleware/

tests/
migrations/
docker/
```

## Local Development

### Prerequisites

- Python 3.12+
- Docker + Docker Compose

### Run with Docker

```bash
docker compose up --build
```

API docs:

- `http://localhost:8000/docs`

### Run without Docker

1. Create virtual env and install dependencies:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

2. Set environment variables (copy from `.env.local.example` if needed).

3. Start API:

```bash
python3 -m app.main
```

## Quality and Tests

Use `Makefile` targets:

```bash
make lint
make format
make test
```

Equivalent direct commands use `.venv/bin/python` with `ruff` and `pytest`.

## Notes for Contributors

- Prefer `Annotated` dependency signatures instead of `param=Depends(...)`.
- Keep write endpoints idempotent where required (`Idempotency-Key`).
- Apply limiter rules to high-risk or high-cost mutation endpoints.
- Keep module boundaries clear (`application` ports/contracts vs `infra` implementations).
