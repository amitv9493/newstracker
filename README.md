# newsextractor

API for registering news article URLs, fetching their content in the background, and storing a summary and category. Requests are served by FastAPI. PostgreSQL holds article records. Redis and Celery run the scrape and summarization jobs.

Scraping and summarization are placeholders. `scrap_url` returns a fixed string, and `summarize_and_categorize_article` writes fixed summary and category text. The HTTP API, persistence, and task pipeline around them are wired up.

## Stack

| Piece | Role |
| --- | --- |
| Python 3.13 | Runtime (`requires-python` in `pyproject.toml`) |
| FastAPI + Uvicorn | HTTP API and OpenAPI docs |
| SQLAlchemy 2 | ORM and sessions |
| Alembic | Schema migrations |
| PostgreSQL (`psycopg2`) | Article storage |
| Celery + Redis | Background jobs and results |
| Pydantic Settings | Configuration from `.env` |

Dependencies are declared in `pyproject.toml` and locked in `uv.lock`.

## Architecture

The app follows a controller → service → model layout.

- **Controllers** (`app/controllers`) define routes and pass dependencies into services. They do not talk to the database or the broker directly, except the health route, which calls `check_database`.
- **Services** (`app/services`) hold the use cases: create and list articles, enqueue processing, and check the database.
- **Models** (`app/models`) are SQLAlchemy tables.
- **Schemas** (`app/schemas`) are request and response models.
- **Tasks** (`app/tasks`) are Celery jobs. They open their own database session.
- **Core** (`app/core`) holds settings, the engine, the Celery app, and exception handlers.

Database integrity errors and broker failures are not caught inside services. FastAPI exception handlers in `app/core/handlers.py` turn them into HTTP responses. Services raise `AppError` subclasses (for example `BrokerUnavailable`) when a failure is part of the use case.

```
POST /api/v1/articles
        │
        ▼
  articles row (status: pending)
        │
POST /api/v1/articles/{id}/process
        │
        ▼
  Celery: tasks.process_article
        │  scrap_url → content + content_hash
        │  status: processing → completed | failed
        ▼
  Celery: tasks.process_article_summary
        │  summary + category
        ▼
  articles row updated
```

## Project layout

```
newsextractor/
├── main.py                     # Uvicorn entrypoint (127.0.0.1:8000, reload)
├── pyproject.toml
├── alembic.ini
├── alembic/                    # Migrations; URL comes from Settings
├── app/
│   ├── main.py                 # FastAPI app, /api/v1 router
│   ├── dependencies.py         # DbSession dependency
│   ├── controllers/            # health, tasks, articles
│   ├── services/
│   ├── schemas/
│   ├── models/                 # Article (file is named arcticle.py)
│   ├── tasks/jobs.py           # Celery tasks
│   ├── helpers/                # pagination, ArticleStatus, scraper
│   └── core/                   # config, database, celery, errors
└── .env.example
```

## Prerequisites

- Python 3.13
- [uv](https://docs.astral.sh/uv/) (or another installer that can read `pyproject.toml`)
- PostgreSQL with a database named `newsextractor` (or whatever `DATABASE_URL` points at)
- Redis, used as the Celery broker and result backend

## Setup

```bash
cp .env.example .env
uv sync
```

Create the database if it does not exist, then apply migrations. Alembic reads `DATABASE_URL` through `app.core.config.settings`, not the URL commented in `alembic.ini`.

```bash
createdb newsextractor
uv run alembic upgrade head
```

## Configuration

Settings live in `app/core/config.py` and are loaded from `.env` with Pydantic Settings. Environment variable names are the uppercase field names.

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `postgresql+psycopg2://postgres:postgres@localhost:5432/newsextractor` | SQLAlchemy connection URL |
| `CELERY_BROKER_URL` | `redis://localhost:6379/0` | Celery broker |
| `CELERY_RESULT_BACKEND` | `redis://localhost:6379/1` | Celery result store |

Unknown environment variables are ignored. The engine uses `pool_pre_ping=True`.

## Running

Start the API:

```bash
uv run python main.py
```

That runs `uvicorn` on `http://127.0.0.1:8000` with reload. Equivalent:

```bash
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Interactive docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs). ReDoc: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc).

Start a worker in a second terminal. Tasks are registered from `app.tasks.jobs` via the Celery `include` list.

```bash
uv run celery -A app.core.celery_app:celery_app worker --loglevel=info
```

PostgreSQL and Redis must be running before the API and worker start.

## API

All routes are under `/api/v1`.

### Health

`GET /api/v1/health`

Runs `SELECT 1`. Returns `{"status": "ok"}` when the database accepts the query. A database outage is handled as `503` with `{"detail": "database unavailable"}`.

### Articles

`POST /api/v1/articles`

Registers a URL for a company. Title, content, category, and summary start empty. Status is `pending`.

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/articles \
  -H 'Content-Type: application/json' \
  -d '{"company_name": "Acme", "url": "https://example.com/story"}'
```

`company_name` must be 1–255 characters after trimming. `url` must be a valid HTTP(S) URL.

If a row already exists for the same `company_name` and `url`, the handler returns that row and does not insert another one.

`GET /api/v1/articles`

Returns a page of articles, newest-id order is insertion order (`ORDER BY id`).

| Query | Default | Notes |
| --- | --- | --- |
| `page` | `1` | Minimum 1 |
| `page_size` | `20` | 1–100 |
| `company_name` | omitted | Exact match after trim; omitted or blank means no filter |

```bash
curl -s 'http://127.0.0.1:8000/api/v1/articles?page=1&page_size=20&company_name=Acme'
```

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20,
  "pages": 0
}
```

`POST /api/v1/articles/{article_id}/process`

Queues `tasks.process_article` and responds `202` with the Celery task id. The route does not wait for scraping to finish.

The service skips enqueue when it cannot find the article (the response body is then `null`). It rejects articles whose status is `processing` or `completed` with HTTP 400.

### Tasks

`POST /api/v1/tasks`

Queues `tasks.process_message`. The body is a JSON string, not an object. Responds `202`:

```bash
curl -s -X POST http://127.0.0.1:8000/api/v1/tasks \
  -H 'Content-Type: application/json' \
  -d '"hello"'
```

```json
{"task_id": "<celery-id>", "status": "queued"}
```

A blank message is accepted by the API and fails inside the worker (`ValueError`). If Redis is unreachable, the API returns `503` with `{"detail": "task broker unavailable"}`.

## Background jobs

| Task name | Argument | What it does |
| --- | --- | --- |
| `tasks.process_message` | message string | Logs and returns the message. Rejects a blank string. |
| `tasks.process_article` | article id | Sets status to `processing`, calls `scrap_url`, stores `content` and a SHA-256 `content_hash` of `company_name + url + content`, then sets `completed` or `failed`. On the success path it enqueues `tasks.process_article_summary`. |
| `tasks.process_article_summary` | article id | Calls `summarize_and_categorize_article` and saves `summary` and `category`. |

`content_hash` is `sha256(company_name + url + content)` as hex. The column is unique.

Article status values (`app/helpers/enums.py`):

| Value | Meaning |
| --- | --- |
| `pending` | Row created, not yet scraped |
| `processing` | Worker has started |
| `completed` | Scrape finished without an exception |
| `failed` | Scrape raised |

## Data model

Table `articles`:

| Column | Type | Notes |
| --- | --- | --- |
| `id` | integer | Primary key |
| `company_name` | string | Indexed |
| `title` | string | Indexed; unused by the current create path |
| `content` | text | Indexed; filled by the scrape task |
| `url` | string | Indexed |
| `category` | string | Indexed; filled by the summary task |
| `summary` | text | Indexed; filled by the summary task |
| `status` | string | Indexed; see status table above |
| `content_hash` | string | Unique index; filled after scrape |
| `created_at` | datetime | Set on insert (`datetime.now`) |
| `updated_at` | datetime | Set on insert; not refreshed on later updates |

## Errors

Handlers are registered in `app/core/handlers.py`.

| Condition | Status | Body |
| --- | --- | --- |
| `ConflictError` or SQLAlchemy `IntegrityError` | 409 | `{"detail": "resource already exists"}` (or the `ConflictError` detail) |
| Database driver or disconnect errors | 503 | `{"detail": "database unavailable"}` |
| `BrokerUnavailable` | 503 | `{"detail": "task broker unavailable"}` |
| Any other unhandled exception | 500 | `{"detail": "internal server error"}` |
| Request validation (Pydantic / query bounds) | 422 | FastAPI’s default validation body |

`get_db` rolls the session back if the request raises, then closes it.

## Migrations

Generate a revision after model changes (review the file before applying it):

```bash
uv run alembic revision --autogenerate -m "describe the change"
uv run alembic upgrade head
```

Current head is `fdc67fffcf21` (adds `articles.status`). History starts at `07a15337122f`.

## Pagination

`Pagination` in `app/helpers/pagination.py` is a FastAPI dependency. Declare it on a route to get `page` and `page_size` query parameters. `paginate(query, params)` returns `total`, `items`, `page`, `page_size`, and `pages`. The list endpoint uses response model `Page[Article]`.
