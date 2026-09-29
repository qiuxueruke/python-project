# fastapi-app

FastAPI project managed with [uv](https://docs.astral.sh/uv/).

## Setup

```powershell
uv sync
copy .env.example .env
```

MySQL / Redis run on the Aliyun host `47.100.188.66` (see `docker-compose.yml`). Passwords contain `@`, so in URLs it must be written as `%40`.

If the database does not exist yet:

```sql
CREATE DATABASE fastapi_app CHARACTER SET utf8mb4;
```

The security group must allow your IP to reach ports `3306` and `6379`.

## Run

```powershell
uv sync
copy .env.example .env
uv run alembic upgrade head
uv run fastapi dev src/fastapi_app/main.py
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

### Database migrations (Alembic)

Table schema is managed by Alembic, not `create_all` at startup.

```powershell
# After changing models/
uv run alembic revision --autogenerate -m "describe_change"
# Review the new file under alembic/versions/, then apply:
uv run alembic upgrade head
```

| Command | Meaning |
|---------|---------|
| `alembic revision --autogenerate -m "..."` | Detect model changes, generate script |
| `alembic upgrade head` | Apply all pending migrations |
| `alembic downgrade -1` | Roll back one revision |
| `alembic current` | Show current DB revision |
| `alembic stamp head` | Mark DB as up-to-date without running SQL (existing DBs) |

### Example API flow

1. `POST /api/auth/register` — register
2. `POST /api/auth/login` — get `access_token` (stored in Redis)
3. `GET /api/users/me` — header: `Authorization: Bearer <token>`
4. `GET /api/notifications` — list notifications for current user

> Auth uses OAuth2 Password + JWT (not Redis session tokens).

## Modular layout

```
src/fastapi_app/
├── main.py                 # create app, mount routers
├── core/                   # shared infrastructure
│   ├── config.py           # settings from .env
│   ├── db.py               # SQLAlchemy engine / Session
│   └── redis.py            # Redis client
├── models/                 # DB tables (User, Notification)
├── crud/                   # DB operations by module
├── schemas/                # request/response Pydantic models
└── api/                    # HTTP modules (one file ≈ one module)
    ├── deps.py             # shared Depends (db, redis, current user)
    ├── router.py           # aggregate all module routers
    ├── auth.py             # 登录模块
    ├── users.py            # 用户信息模块
    └── notifications.py    # 通知模块
```

How modules stay separate:

- Each feature owns its **router** (`api/auth.py`, `api/users.py`, …)
- Shared DB/Redis wiring lives in **`core/`** + **`api/deps.py`**
- Request/response shapes live in **`schemas/`**, tables in **`models/`**
- `main.py` only creates the app and includes `api_router`

MySQL / Redis:

- Connection strings come from `.env` → `core/config.py`
- Routes get a DB session via `Depends(get_db)`
- Login issues JWT; protected routes use `Authorization: Bearer <token>`

## Root files

| Path | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata and dependencies |
| `uv.lock` | Locked dependency versions |
| `.python-version` | Pins Python 3.13 for uv |
| `.venv/` | Project virtualenv (gitignored) |
| `.env` / `.env.example` | Local secrets and connection URLs |
| `alembic.ini` | Alembic config |
| `alembic/` | Migration env + `versions/` scripts |
| `.gitignore` | Ignore `.venv`, `.env`, caches |
| `.vscode/settings.json` | Point Cursor at `.venv` Python |
