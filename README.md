# LittleBuggy

Vue 3 + Vite frontend and FastAPI backend for a parent-friendly Metro Vancouver health snapshot (RSV, flu, COVID signals, air quality, weather).

## Local development

### Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=sqlite:///./littlebuggy.db   # optional; this is the default
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- API: `http://127.0.0.1:8000` — try `/health`, `/api/status`, and `/api/homepage-summary` (after a DB snapshot job; the **homepage UI does not call the API** — it uses `public/data/homepage-summary.json`).
- Copy `backend/.env.example` to `backend/.env` if you want persistent env vars.

### Frontend

```bash
npm install
npm run dev
```

- Leave `VITE_API_BASE_URL` **unset** so `/api` is proxied to `http://127.0.0.1:8000` (override with `VITE_DEV_PROXY_TARGET` in `.env` if your API port differs).
- This stack is **Vite**, so the build-time variable is `VITE_API_BASE_URL` (not `VUE_APP_*` from older Vue CLI templates).
- **Homepage data (MVP):** the site reads **`/data/homepage-summary.json`**. Weekly refresh: **`npm run weekly:homepage`** (details below). No database required.

### Snapshot jobs (local, optional for homepage)

From `backend/` with the same `DATABASE_URL` as the API:

```bash
python3 -m app.jobs.run_update
```

See `backend/README.md` for weekly vs daily jobs (useful if you later serve the homepage from the API + DB).

### Weekly homepage update (no database)

This is the **simplest** path: one command regenerates the JSON, you commit it, the static site deploy picks it up. **No Postgres, no cron, no API** needed for the live homepage.

#### A. Command to run (pick one)

From the **repository root** (not `backend/`):

```bash
npm run weekly:homepage
```

Same script as:

```bash
npm run update:homepage-summary
```

Or directly:

```bash
python3 scripts/update_homepage_summary.py
```

All of these write **`public/data/homepage-summary.json`**.

#### B. Requirements

| Need | Notes |
|------|--------|
| **Python 3** | 3.10+ recommended (match `backend/runtime.txt` if you deploy the API too). |
| **Dependencies** | **Homepage JSON only:** `pip install -r scripts/requirements-homepage.txt` (just **httpx**). Full API work: `pip install -r backend/requirements.txt`. |
| **Network** | The script calls public PHAC, ECCC, and Open-Meteo endpoints. |
| **Environment variables** | **None** for this script (no `DATABASE_URL`, no API keys for current feeds). |
| **Working directory** | Must be the **repo root** so `public/data/` resolves correctly. |

#### C. Weekly routine, local test, and failures

**Routine (about once a week):**

1. **`cd`** to the **repo root**.
2. **`source .venv/bin/activate`** (or any venv where you ran `pip install -r scripts/requirements-homepage.txt`).
3. **`npm run weekly:homepage`** — the script prints a **health block** (dates, card sanity, source `ok` count) and any **warnings** to the terminal; JSON never embeds stack traces.
4. Optional: **`npm run weekly:homepage:check`** — validates the file on disk (no network).
5. **Preview:** `npm run dev` (hard-refresh if needed), or **`npm run build && npm run preview`** for a production-like check.
6. **Ship:** `git add public/data/homepage-summary.json` → commit → push.
7. **Deploy** your static host so **`dist/data/homepage-summary.json`** matches after `npm run build`.

**If one data source fails:** the run **still writes** `public/data/homepage-summary.json`. Cards may show **Unknown** / **Unavailable**; `sources.*.status` is **error** where applicable; **`data_quality_note`** stays **one calm parent-facing line** (polish step, not raw HTTP text). Check the terminal **Warnings** list for detail. Re-run when feeds recover, or ship partial data if that’s acceptable for the week.

**If the script exits with an error before “Wrote …”:** fix Python path / deps (`pip install -r scripts/requirements-homepage.txt`), confirm you’re at repo root, and check network. After a total merge failure, the script can still emit a **minimal valid JSON** so the site doesn’t break—re-run when possible.

You can automate step 1 in **GitHub Actions** (schedule: weekly) using the same command after `pip install -r backend/requirements.txt`, then commit via a bot token or open a PR with the updated JSON.

#### D. What is live data vs editorial vs illustrative

| Kind | What it is |
|------|------------|
| **Fetched from public sources (at script run time)** | BC respiratory **signals** (PHAC Health Infobase wastewater API — population-level, not a clinic test), **AQHI** for Metro Vancouver (MSC GeoMet / open data), **current weather** (Open-Meteo). Raw strings and **source names, URLs, refresh labels, and `updated_at`** come from this step. |
| **Editorially summarized (in our code)** | **`short_summary`** / **`summary`**: short plain-language sentences built from those numbers (see `backend/app/services/homepage_public_polish.py`). **`live_vs_illustrative_note`**: fixed explainer of what this snapshot covers. **`data_quality_note`**: rewritten into one calm line if a fetch failed. **Outdoor feel** comes from a **rules-based** phrase (`build_summary`), not a separate public API. |
| **Illustrative only (in the Vue app, not in the JSON file)** | **Map bubbles** except Vancouver RSV (which follows the snapshot). **“Stories from the neighbourhood”**, **active buzz** cold/tummy cards, and similar sections are **mood / editorial** — they are labeled in the UI and are **not** official neighbourhood statistics. |

#### E. Optional admin page (`/admin/update`)

This is **not** for visitors: the route is **unlisted** (no nav link). Bookmark **`/admin/update`** for yourself.

1. Run the **API** with **`ADMIN_HOMEPAGE_TOKEN`** set to a long random secret (`backend/.env.example`). If unset, **`POST /api/admin/homepage-snapshot/regenerate`** returns **503**.
2. Run the **frontend** (`npm run dev`) and open **`/admin/update`**.
3. Paste the same secret (stored only in **session storage** for that tab).
4. Click **Update homepage snapshot** for **warnings, `updated_at`, sources OK count, preview**, and whether the server wrote a file.

**Disk write:** only if **`HOMEPAGE_SUMMARY_OUTPUT_PATH`** is set and writable (common locally: `../public/data/homepage-summary.json` from `backend/`). On split static + API hosting, use **Download full JSON** → commit **`public/data/homepage-summary.json`** → deploy.

**Production:** set **`VITE_API_BASE_URL`** to your API origin. Prefer a specific **`CORS_ORIGINS`** instead of `*` if you enable this endpoint.

### 中文说明：首页是「离线生成 JSON，网站只读文件」

你要的版本**从头到尾**就是这样实现的，**不是**「用户每次打开网站，浏览器里实时去抓数据、再分析」的版本。

| 步骤 | 说明 |
|------|------|
| **① 生成** | 在你本机或 CI（需要联网）运行 **`npm run weekly:homepage`**（或 `python3 scripts/update_homepage_summary.py`）。脚本此时才会访问 PHAC、加拿大 AQHI、Open-Meteo 等**公开接口**，合并结果并写成家长向文案，输出到 **`public/data/homepage-summary.json`**。 |
| **② 发布** | 把该 JSON **提交进 Git**，再执行 **`npm run build`** 部署静态站；构建产物里是 **`dist/data/homepage-summary.json`**。 |
| **③ 访客打开网站** | 前端**只**请求这个静态路径（例如 `/data/homepage-summary.json`），**不会**在每次页面加载时再去调用上述数据源做分析。 |

**结论：** 抓取和分析只发生在**你运行脚本的那一刻**；网站运行时**没有**「实时爬虫首页」。首页也**不依赖 Postgres**；数据库与 `GET /api/homepage-summary` 仅保留为将来若要改回 API 模式时的可选后端。

**生成 JSON 的脚本**只依赖 **`httpx`**（见 `scripts/requirements-homepage.txt`），**不需要安装 SQLAlchemy**；它导入的是 `homepage_summary_builder`，不会加载 `snapshot_pipeline` 里的数据库代码。

数据加载在应用里**只从一处触发**：`App.vue` 挂载时调用 `ensureHomepageSnapshot()`（读取静态 JSON），首页 `HomeView` **不再重复拉取**。

---

## Deploying on Render

Use **two services** plus **PostgreSQL** (Render Postgres or any external URL SQLAlchemy supports):

| Render service | Type | Purpose |
|----------------|------|---------|
| API | Web Service (Python) | FastAPI + Uvicorn |
| Site | Static Site | Built Vue app (`dist/`) |

You can create both from the repo using **Blueprint** (`render.yaml`) or manually with the settings below.

### 1. PostgreSQL

1. On Render: **New → PostgreSQL**, create an instance.
2. Copy the **Internal Database URL** for use on the API and cron jobs (same network, no egress charges).

### 2. Backend (Web Service)

| Setting | Value |
|---------|--------|
| Root directory | `backend` |
| Build command | `pip install -r requirements.txt` |
| Start command | `python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |

**Environment variables (API):**

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | Postgres connection string (Internal URL on Render). |
| `CORS_ORIGINS` | Recommended | Comma-separated allowed origins for browser requests, e.g. `https://littlebuggy-web.onrender.com`. Use `*` only for quick tests. |
| `PYTHON_VERSION` | Optional | Set to `3.12.0` if the dashboard does not pick Python 3.12; `backend/runtime.txt` also pins this. |

After deploy, open `https://<your-api-service>.onrender.com/health` — you should see `{"status":"ok"}`.

### 3. Frontend (Static Site)

| Setting | Value |
|---------|--------|
| Root directory | `.` (repo root) |
| Build command | `npm ci && npm run build` |
| Publish directory | `dist` |

**Environment variables (build-time):**

| Variable | Required | Description |
|----------|----------|-------------|
| `VITE_API_BASE_URL` | Optional | Only if the frontend calls your API for something other than the homepage summary. The homepage uses **`/data/homepage-summary.json`** — no API env needed for that. |

**SPA routing:** `render.yaml` rewrites unknown paths to `index.html`. Files under `public/data/` are copied to `dist/data/` and served as static assets (not rewritten).

**Order of operations:** run `npm run weekly:homepage`, commit `public/data/homepage-summary.json`, then `npm run build` and deploy `dist/`. Add API + Postgres later if you want live `GET /api/homepage-summary` again — swap the frontend loader to that URL when ready.

### 4. Pointing the frontend at the backend (optional)

The homepage summary does **not** call the API. If you add other client → API features later:

1. Set `VITE_API_BASE_URL` at static build time (no localhost in production bundles).
2. Set `CORS_ORIGINS` on the API to your static site’s public URL (or `https://your-custom-domain.com` later).

### 5. Scheduled snapshot jobs (Cron)

Cron jobs are **separate** from the web process: they do not replace or restart the API.

Cron jobs populate the **database** for `GET /api/homepage-summary` and `/api/status`; they are **not** required for the static homepage, which uses **`data/homepage-summary.json`** only. Keep them if you use the API or plan to switch the homepage to the API later.

**Critical:** each cron service must use the **same `DATABASE_URL`** string as the API web service (copy the Postgres **Internal Database URL**). If the URL differs, the API will keep serving an empty or stale database while jobs write elsewhere.

Create **New → Cron Job** on Render for each schedule (same repo, **root directory `backend`**, same env as API):

| Job | Suggested schedule (UTC) | Start command | Build command |
|-----|--------------------------|---------------|----------------|
| Daily environment (+ auto full bootstrap if DB empty) | `30 16 * * *` (adjust as needed) | `python3 -m app.jobs.run_daily_environment` | `pip install -r requirements.txt` |
| Weekly respiratory | `0 17 * * 1` (Mondays) | `python3 -m app.jobs.run_weekly_respiratory` | `pip install -r requirements.txt` |

**Simpler alternative (one job):** daily `python3 -m app.jobs.run_update` instead of the two rows above.

The repo `render.yaml` includes the two-cron MVP; you can remove or edit those blocks if you use the single-job approach.

Until a job has run at least once, `GET /api/homepage-summary` may return **404** — irrelevant for the static homepage. Use `GET /api/status` if you operate the API + DB path.

### 6. Custom domains later

1. **Static site:** Render dashboard → your static service → **Custom Domains** → add domain and DNS as instructed.
2. **API:** Same for the web service if you want `api.yourdomain.com`.
3. Update **`CORS_ORIGINS`** on the API to include the new frontend origin (`https://www.yourdomain.com`).
4. Rebuild the static site only if you change `VITE_API_BASE_URL` (e.g. if the public API URL changes).

### Blueprint (`render.yaml`)

From the Render dashboard: **New → Blueprint**, select this repository. Fill in **sync: false** variables when prompted (`DATABASE_URL`, `CORS_ORIGINS`; `VITE_API_BASE_URL` is optional for static-only homepage).

---

## Environment variables summary

### Render — API (Web Service) + Cron

- `DATABASE_URL` — PostgreSQL URL (**required** in production).
- `CORS_ORIGINS` — e.g. `https://<static-site>.onrender.com` (**recommended**).
- `PORT` — injected by Render; do not set manually.

### Render — Static Site (build)

- `VITE_API_BASE_URL` — Optional unless the bundle calls your API for non-homepage features.

### Local — optional `.env` files

- Repo root `.env`: `VITE_DEV_PROXY_TARGET`, or `VITE_API_BASE_URL` if you ever need a full URL in dev.
- `backend/.env`: `DATABASE_URL`, `CORS_ORIGINS`.

### External data API keys

None required for current PHAC / GeoMet / Open-Meteo integrations. Add keys here if you introduce paid or authenticated sources later.

---

## Exact commands (Render)

| Step | Command / path |
|------|----------------|
| **Backend start** | `python3 -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| **Homepage JSON (before static build)** | `npm run weekly:homepage` |
| **Frontend build** | `npm ci && npm run build` |
| **Frontend publish directory** | `dist` |

---

## Files in this repo

- `public/data/homepage-summary.json` — bundled homepage summary (regenerate with `npm run weekly:homepage`).
- `scripts/update_homepage_summary.py` — fetches public data, polishes copy, writes that file (imports `homepage_summary_builder`, **not** `snapshot_pipeline` / SQLAlchemy).
- `scripts/requirements-homepage.txt` — minimal deps (**httpx**) for that script alone.
- `render.yaml` — Blueprint for API + static site.
- `backend/runtime.txt` — Python version for Render.
- `.env.example` / `backend/.env.example` — documented variables (copy to `.env`; do not commit secrets).
