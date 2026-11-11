# Taskflow API

An async project/task-management REST API: JWT authentication,
membership-based authorization (only project owners/members can see or
modify a project's tasks), pagination and filtering, and background
notifications -- built on FastAPI and SQLAlchemy 2.0's async ORM.

## Why this project

A multi-resource API with real authentication and authorization is a
different set of engineering concerns than a data-processing library or
a desktop GUI: async request handling, database session management,
password/token security, and testing an HTTP API in isolation. Built
incrementally, one feature per branch/pull request.

## Installation

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
pip install -e ".[dev]"
```

## Running it

```bash
uvicorn taskflow.main:app --reload
```

Interactive API docs (Swagger UI) are then available at
http://127.0.0.1:8000/docs.

## Features

- **JWT authentication.** Register with email/password (bcrypt-hashed),
  log in via the OAuth2 password grant, and use the returned bearer
  token on subsequent requests.

## Project layout

```
src/taskflow/
    config.py         Environment-driven settings
    database.py         Async engine/session setup
    security.py           Password hashing and JWT create/verify
    dependencies.py          get_current_user and other shared dependencies
    models/                    SQLAlchemy ORM models
    schemas/                     Pydantic request/response schemas
    api/                            One router module per resource
    main.py                            FastAPI application factory
tests/              pytest suite (async, isolated in-memory DB per test)
```

## Authentication

```bash
curl -X POST localhost:8000/auth/register \
    -H "Content-Type: application/json" \
    -d '{"email": "alice@example.com", "password": "correct-horse", "display_name": "Alice"}'

curl -X POST localhost:8000/auth/login \
    -d "username=alice@example.com&password=correct-horse"
# -> {"access_token": "...", "token_type": "bearer"}

curl localhost:8000/auth/me -H "Authorization: Bearer <access_token>"
```

## Testing

```bash
pytest --cov=taskflow --cov-report=term-missing
ruff check src tests
```

## License

MIT -- see [LICENSE](LICENSE).
