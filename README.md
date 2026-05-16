# Demo Carwash Backend API

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white)

FastAPI backend for carwash operations, built with a modular clean architecture, JWT authentication, idempotency keys for critical endpoints, and request rate limiting.

## Feature Scope

- Auth and session: `/api/v1/auth/*`
- Account management: `/api/v1/accounts/*`
- Service type management: `/api/v1/service-types/*`
- Ticket operations: `/api/v1/tickets/*`
- Billing transactions: `/api/v1/transactions/*`
- Analytics: `/api/v1/analytics/*`
- Health and DB smoke-check endpoints

## Tech Stack

- Python 3.12
- FastAPI
- PostgreSQL 16
- SQLAlchemy (async) + asyncpg
- Pydantic v2
- Alembic
- slowapi (rate limiter)
- pytest + ruff
- Docker + Docker Compose

## Architecture

The project uses a modular clean architecture under `app/modules/*`.

- `api`: routes, schemas, dependencies
- `application`: use cases, DTOs, ports, query models
- `domain`: entities, value objects, repository interfaces
- `infra`: repository implementations, unit of work, adapters

Shared concerns are in `app/shared/*` (config, middleware, error handling, DB lifecycle).

## Base URL and API Docs

- API base path: `/api/v1` (from `app.main -> include_router(..., prefix=settings.API_VERSION)`)
- Swagger UI: `http://localhost:8000/docs`

## Roles

Current roles used in the system:

- `ADMIN`
- `OWNER`
- `CASHIER`

Current role enforcement examples:

- Account management: `ADMIN`, `OWNER`
- Service catalog management: `ADMIN`, `OWNER`
- Ticket list/void operations: `ADMIN`, `OWNER`, `CASHIER`
- Payment processing: `CASHIER`
- Analytics: `OWNER`

Important note for ticket creation:

- `POST /api/v1/tickets` is enforced using `get_current_device` (device context), not `RoleChecker`.
- This endpoint requires a valid authenticated device/session context and an `Idempotency-Key` header.

## Auth Flow

1. `POST /api/v1/auth/login` returns `access_token` + `refresh_token`
2. Use `Authorization: Bearer <access_token>` for protected requests
3. `POST /api/v1/auth/refresh` returns a new token pair
4. `POST /api/v1/auth/logout` revokes the refresh token
5. `GET /api/v1/auth/me` returns the currently authenticated user context

Default token settings in config:

- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_HOURS=8`
- `REFRESH_TOKEN_EXPIRE_DAYS=7`

## Endpoint Summary

- Health:
  - `GET /api/v1/health`
  - `GET /api/v1/test-db`
- Auth:
  - `POST /api/v1/auth/login`
  - `POST /api/v1/auth/refresh`
  - `POST /api/v1/auth/logout`
  - `GET /api/v1/auth/me`
- Accounts:
  - `POST /api/v1/accounts`
  - `GET /api/v1/accounts`
  - `GET /api/v1/accounts/{account_id}`
  - `PATCH /api/v1/accounts/{account_id}/activate`
  - `PATCH /api/v1/accounts/{account_id}/deactivate`
  - `DELETE /api/v1/accounts/{account_id}`
- Service Types:
  - `POST /api/v1/service-types`
  - `GET /api/v1/service-types`
  - `GET /api/v1/service-types/name/{service_name}`
  - `GET /api/v1/service-types/{service_type_id}`
  - `PATCH /api/v1/service-types/{service_type_id}`
  - `PATCH /api/v1/service-types/{service_type_id}/activate`
  - `PATCH /api/v1/service-types/{service_type_id}/deactivate`
  - `DELETE /api/v1/service-types/{service_type_id}`
- Tickets:
  - `POST /api/v1/tickets`
  - `GET /api/v1/tickets`
  - `PATCH /api/v1/tickets/{ticket_id}/void`
- Transactions:
  - `POST /api/v1/transactions`
  - `GET /api/v1/transactions`
- Analytics:
  - `GET /api/v1/analytics/dashboard-summary`
  - `GET /api/v1/analytics/daily-revenue`
  - `GET /api/v1/analytics/top-services`
  - `GET /api/v1/analytics/payment-method-summary`

## Example Requests

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "cashier_01",
    "password": "secret123"
  }'
```

### Create Ticket (Idempotent)

```bash
curl -X POST http://localhost:8000/api/v1/tickets \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: ticket-20260516-001" \
  -d '{
    "service_type_id": 1
  }'
```

### Process Transaction (Idempotent)

```bash
curl -X POST http://localhost:8000/api/v1/transactions \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: txn-20260516-001" \
  -d '{
    "ticket_id": 1,
    "plate_number": "B 1234 XYZ",
    "payment_method": "cash",
    "payment_metadata": {}
  }'
```

### Analytics Dashboard Summary

```bash
curl "http://localhost:8000/api/v1/analytics/dashboard-summary?target_date=2026-05-16" \
  -H "Authorization: Bearer <access_token>"
```

## Environment Variables

Start from `.env.local.example`, then adjust values in `.env`.

Required/common runtime variables:

- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_HOST`
- `DB_PORT`
- `ALEMBIC_DATABASE_URL`
- `SECRET_KEY`
- `PORT`
- `HOST`
- `API_VERSION` (example: `/api/v1`)

Optional variables (defaults are defined in `settings.py`):

- `ALGORITHM` (default `HS256`)
- `ACCESS_TOKEN_EXPIRE_HOURS` (default `8`)
- `REFRESH_TOKEN_EXPIRE_DAYS` (default `7`)
- `CORS_ORIGINS` (default `[*]`)
- `CORS_ALLOW_METHODS` (default `GET,POST,PUT,PATCH,OPTIONS`)
- `CORS_ALLOW_HEADERS` (default `Authorization,Content-Type,Accept`)

## Active Rate Limits

- `GET /api/v1/health` -> `5/minute`
- `GET /api/v1/test-db` -> `10/minute`
- `POST /api/v1/auth/login` -> `10/minute`
- `POST /api/v1/auth/refresh` -> `10/second`
- `POST /api/v1/auth/logout` -> `10/second`
- `POST /api/v1/accounts` -> `10/minute`
- `POST /api/v1/service-types` -> `10/minute`
- `PATCH /api/v1/service-types/{service_type_id}` -> `20/minute`
- `DELETE /api/v1/service-types/{service_type_id}` -> `10/minute`
- `POST /api/v1/tickets` -> `30/minute`
- `PATCH /api/v1/tickets/{ticket_id}/void` -> `20/minute`
- `POST /api/v1/transactions` -> `20/minute`

## Local Development

### Prerequisites

- Python 3.12+
- Docker + Docker Compose

### Run with Docker

```bash
docker compose up --build
```

### Run without Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.local.example .env
python3 -m app.main
```

## Quality Commands

```bash
make format
make format-check
make lint
make test
```

## Directory Structure

```text
app/
  api/
  modules/
    analytics/
    billing/
    carwash_operation/
    identity/
    service_catalog/
  shared/

tests/
migrations/
docker/
```
