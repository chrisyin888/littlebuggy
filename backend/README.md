# LittleBuggy API (V1)

FastAPI + PostgreSQL/SQLite. Ingests **real** public signals (respiratory proxies, AQHI, weather), builds a parent-friendly summary, stores `trend_snapshots` with **source metadata**, exposes `GET /api/homepage-summary`.

**Homepage:** in **dev**, the Vue app loads **`public/data/homepage-summary.json`**. In **production**, the bundle requests **`GET /api/homepage-summary`** first (latest `trend_snapshots` row) and falls back to that static file if the API fails. Regenerate locally: **`npm run weekly:homepage`** (writes `public/data/...` only).

**Admin trigger (updates production API data):** set **`ADMIN_HOMEPAGE_TOKEN`**, then **`POST /api/admin/homepage-snapshot/regenerate`** with header **`X-Admin-Token`**. Runs the same fetch+polish pipeline as `npm run weekly:homepage` and **inserts a new `trend_snapshots` row** so `GET /api/homepage-summary` returns fresh content. Optionally set **`HOMEPAGE_SUMMARY_OUTPUT_PATH`** so the same handler also writes JSON on the API machine (usually local dev). Frontend **`/admin/update`** calls this when the API is reachable.

## Python package layout

The importable package is **`app`**, and it lives **inside** `backend/`. Python must see `backend/` on the module search path.

**Always `cd backend` first** (or set `PYTHONPATH` to the `backend` directory — see below).

## Layout

```
backend/                 ← working directory for all commands below
  app/
    __init__.py
    main.py              # FastAPI app + CORS + table bootstrap
    config/              # settings (pydantic-settings) + cities (homepage regions)
      __init__.py
      settings.py
      cities.py
    database.py          # SQLAlchemy engine + SessionLocal + get_db
    models/              # ORM
    schemas/             # Pydantic response models
    api/routes/          # HTTP endpoints
    services/            # fetch_*_real, snapshot_pipeline, build_summary, save_snapshot
    jobs/                # run_update, run_weekly_respiratory, run_daily_environment
    utils/               # reserved
  requirements.txt
```

## Flow

### Job entrypoints (what runs where)

| Entry | What it does | MVP |
|--------|----------------|-----|
| **`app/jobs/run_update.py`** (`python3 -m app.jobs.run_update`) | **Full** pipeline: BC respiratory (PHAC wastewater API) + AQHI + weather → new `trend_snapshots` row. | Safe anytime; use for **first bootstrap**, local dev, or a **single daily cron** if you prefer one job over two. |
| **`app/jobs/run_daily_environment.py`** | **AQHI + weather** only; copies RSV/flu/COVID labels from the **latest** row. If the table is **empty**, runs a **full** pipeline once (so the first scheduled run never saves all-`Unknown` viruses). | **Recommended daily** on production. |
| **`app/jobs/run_weekly_respiratory.py`** | **Respiratory** fetch only; copies air/weather from the **latest** row. | **Recommended weekly** (source updates roughly weekly). |
| **`app/services/snapshot_pipeline.py`** | Library: `run_snapshot_job(db, city_id=…, mode)` — shared fetches with ``homepage_summary_builder``; **not** run directly; jobs loop `CITIES`. | — |

**Cadence (production-safe MVP):** run **`run_daily_environment` daily** (fresh air + weather) and **`run_weekly_respiratory` weekly** (fresh virus trend labels). Alternatively, a **single daily** `run_update` is simpler operationally but hits every upstream API every day.

**Operator check:** `GET /api/status` — database reachability, `last_snapshot_at`, per-source `ok` flags, and whether `GET /api/homepage-summary` would return 200 (latest row by `created_at`, including `sources` and `data_quality_note`).

### Data sources (stability labels)

| Signal | Implementation | Label |
|--------|----------------|--------|
| RSV / flu / COVID trend text | [PHAC Health Infobase wastewater API](https://health-infobase.canada.ca/) — BC (`pruid=59`), `covN2` / `rsv` / `fluA`+`fluB` rolling averages | **Official API** (wastewater proxy; not BCCDC lab positivity) |
| Clinical context link | [BCCDC respiratory viruses](https://www.bccdc.ca/health-info/diseases-conditions/covid-19/data#respiratory) | **Official public webpage** (reference URL in metadata) |
| AQHI | [MSC GeoMet](https://api.weather.gc.ca/) `aqhi-observations-realtime` (Metro Vancouver bbox) | **Official API** |
| Weather | [Open-Meteo](https://open-meteo.com/) forecast current | **Third-party API** (no API key for typical use) |

## Why `ModuleNotFoundError: No module named 'app'`?

- Running **`python3 app/jobs/run_update.py`** executes a **file**, not the **`app` package**. The project root on `sys.path` is wrong unless you use **`-m`** or set **`PYTHONPATH`**.

**Correct (recommended):**

```bash
cd backend
python3 -m app.jobs.run_update
```

**From repo root** (without `cd backend`):

```bash
PYTHONPATH=backend python3 -m app.jobs.run_update
```

(Adjust path if your folder name differs.)

## Local setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### PostgreSQL (recommended)

Create a DB and set:

```bash
export DATABASE_URL=postgresql://USER:PASS@localhost:5432/littlebuggy
```

### Quick test with SQLite (optional)

```bash
cd backend
export DATABASE_URL=sqlite:///./littlebuggy.db
python3 -m app.jobs.run_update
```

### Run API

```bash
cd backend
export DATABASE_URL=...   # same as above
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Manual job + logs

```bash
cd backend
export DATABASE_URL=...
python3 -m app.jobs.run_update
```

You should see INFO logs for fetch, `outdoor_feel`, and saved `id`.

### Smoke-test the endpoints

```bash
curl -s http://127.0.0.1:8000/api/status | jq
curl -s http://127.0.0.1:8000/api/homepage-summary | jq
```

If you have not run the job yet, the API returns **404** with a hint to run `python3 -m app.jobs.run_update`.

## Render

### Web service (Little Buggy API — this repo)

Deploy the API from the **Little Buggy** Git repository. Use a **dedicated** Render Web Service for this app (do not point your static site at an unrelated FastAPI service).

**Manual dashboard settings**

| Field | Value |
|--------|--------|
| **Root Directory** | `backend` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Health Check Path** | `/health` |

**Environment variables**

| Key | Required | Notes |
|-----|----------|--------|
| `DATABASE_URL` | Yes (production) | Render PostgreSQL **Internal Database URL** (or other Postgres URL). Without it, the app falls back to SQLite on ephemeral disk — not suitable for production. |
| `CORS_ORIGINS` | Recommended | Comma-separated **origins** your static site uses (no spaces), e.g. `https://your-static.onrender.com,https://littlebuggy.ca`. Use `*` only for quick tests. |
| `PYTHON_VERSION` | Optional | e.g. `3.12.0` if not using `runtime.txt` / dashboard Python version. |
| `ADMIN_HOMEPAGE_TOKEN` | Optional | Long secret for admin POST routes and virus-trends cron; omit to disable those endpoints. |

**Routes to verify after deploy** (replace `BASE` with your service URL, no trailing slash):

- `GET BASE/health` — JSON including `"status":"ok"`
- `GET BASE/wait-times` — JSON with `hospitals`, `upcc_centres`, `checked_at`
- `GET BASE/virus-trends` — JSON snapshot (defaults if never refreshed)

**Static site:** set **`VITE_API_BASE_URL`** to the same **`BASE`** (the Web Service’s public `https://…` URL, no trailing slash) when building the frontend.

`runtime.txt` pins the Python version for Render.

`main.py` calls `create_all` on startup so tables appear on first deploy (fine for V1; move to Alembic later).

### Scheduled updates (cron)

Use **two** cron jobs for different cadences (same `DATABASE_URL` as the web service; root directory `backend`):

| Cadence | Command |
|---------|---------|
| Weekly (respiratory) | `python3 -m app.jobs.run_weekly_respiratory` |
| Daily (AQHI, weather) | `python3 -m app.jobs.run_daily_environment` |

Optional **all-in-one** (e.g. local dev): `python3 -m app.jobs.run_update`.

If the platform runs from **repo root**:

```bash
PYTHONPATH=backend python3 -m app.jobs.run_daily_environment
```

### Dependency note

- **`httpx`** is required for outbound HTTP to PHAC, GeoMet, and Open-Meteo (`requirements.txt`).

## Next steps (when you need them)

- Alembic migrations instead of `create_all`.
- Auth on a future “admin refresh” endpoint (optional; cron is enough for V1).
- Structured logging / Sentry.
