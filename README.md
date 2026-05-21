# SilentFlare

SilentFlare is a small monorepo for the public blog, the FastAPI backend, and
the admin frontend. This README is the local development starting point and the
high-level project map for future AI-assisted work.

## Project Overview

- `apps/blog`: Astro/Yukina public blog frontend. It reads published posts from the backend public APIs.
- `apps/api`: FastAPI backend with SQLite-backed public post APIs and admin post CRUD APIs.
- `apps/admin`: Vue 3 + Vite admin frontend for managing posts with a ByteMD editor.
- `docs/API_CONTRACT.md`: Current API contract for public and admin endpoints.
- `.github/workflows/ci.yml`: GitHub Actions CI for admin build and API smoke test.

## Directory Structure

```text
apps/
  api/      FastAPI backend
  admin/    Vue 3 + Vite admin frontend
  blog/     Astro/Yukina blog frontend
docs/
  API_CONTRACT.md
.github/
  workflows/
    ci.yml
```

## Local Backend Setup On Windows CMD

```cmd
cd apps\api
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

If port `8000` is blocked on Windows, use `8001`:

```cmd
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

## Local Admin Setup On Windows CMD

```cmd
cd apps\admin
npm install
copy .env.example .env
npm run dev -- --host 127.0.0.1 --port 5174
```

## Local Blog Setup On Windows CMD

Start the backend before running or building the blog.

```cmd
cd apps\blog
pnpm install
copy .env.example .env
pnpm run dev -- --host 127.0.0.1 --port 4321
```

## Environment Variables

`apps/api/.env`:

```text
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
JWT_SECRET_KEY=change-this-local-dev-secret
SILENTFLARE_DATABASE_PATH=data/blog.db
```

`apps/admin/.env`:

```text
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Use `http://127.0.0.1:8001/api/v1` if the backend is running on port `8001`.

`apps/blog/.env`:

```text
PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Use `http://127.0.0.1:8001/api/v1` if the backend is running on port `8001`.

## Validation Commands

Admin build:

```cmd
cd apps\admin
npm run build
```

Backend smoke test:

```cmd
cd apps\api
python scripts\smoke_test.py --base-url http://127.0.0.1:8000
```

Blog build:

```cmd
cd apps\blog
pnpm run build
```

## CI

GitHub Actions runs on push and pull request to `main`:

- Admin build: installs `apps/admin` dependencies and runs `npm run build`.
- API smoke test: installs `apps/api` dependencies, compiles backend code, starts Uvicorn, and runs `scripts/smoke_test.py`.

## Current Status

- API works.
- Admin CRUD works.
- Admin uses a ByteMD editor.
- Blog reads public posts from the backend.

## Notes

- Blog build needs the backend API running.
- Admin uses `VITE_API_BASE_URL`.
- Blog uses `PUBLIC_API_BASE_URL`.
- Local backend may run on `8001` if `8000` is blocked on Windows.
- Do not put real secrets into `.env.example` files or this README.
