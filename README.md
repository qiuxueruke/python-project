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
uv run fastapi dev src/fastapi_app/main.py
```

- API: http://127.0.0.1:8000
- Docs: http://127.0.0.1:8000/docs

### Example API flow

1. `POST /api/auth/register` — register
2. `POST /api/auth/login` — get `access_token` (stored in Redis)
3. `GET /api/users/me` — header: `Authorization: Bearer <token>`
4. `GET /api/notifications` — list notifications for current user

## Modular layout

```
src/fastapi_app/
├── main.py                 # create app, mount routers
├── core/                   # shared infrastructure
│   ├── config.py           # settings from .env
│   ├── db.py               # SQLAlchemy engine / Session
│   └── redis.py            # Redis client
├── models/                 # DB tables (User, Notification)
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
- Login sessions are stored in Redis as `session:<token> → user_id`

## Root files

| Path | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata and dependencies |
| `uv.lock` | Locked dependency versions |
| `.python-version` | Pins Python 3.13 for uv |
| `.venv/` | Project virtualenv (gitignored) |
| `.env` / `.env.example` | Local secrets and connection URLs |
| `.gitignore` | Ignore `.venv`, `.env`, caches |
| `.vscode/settings.json` | Point Cursor at `.venv` Python |
