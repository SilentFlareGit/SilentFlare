# SilentFlare

SilentFlare is a small monorepo for the public blog, the FastAPI backend, and
the admin frontend. This README is the local development starting point and the
high-level project map for future AI-assisted work.

## Project Overview

- `apps/api`: FastAPI backend with public blog APIs, admin post CRUD APIs, and authenticated cover image upload at `POST /api/v1/admin/uploads/cover`.
- `apps/blog`: Astro/Yukina public blog frontend. It reads published posts from the backend public APIs.
- `apps/admin`: Vue 3 + Vite admin frontend with login, posts CRUD, ByteMD editing, split Markdown preview, search/status filters, quick publish/unpublish, public view links, cover image upload, cover URL auto-fill, cover preview, and Playwright E2E coverage.
- `docs/API_CONTRACT.md`: Current API contract for public and admin endpoints.
- `.github/workflows/ci.yml`: GitHub Actions CI for admin build, API smoke test, blog build, and admin E2E.

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
VITE_PUBLIC_BLOG_BASE_URL=http://localhost:4321
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

Admin Playwright E2E:

```cmd
cd apps\admin
npm run test:e2e
```

Local admin E2E requires the API backend running unless CI starts it for the job. The suite covers login, create/edit/delete, publish/unpublish, Markdown preview, public links, and cover upload.

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
- Blog build: installs `apps/blog` dependencies, starts the backend, and runs `pnpm run build`.
- Admin E2E: runs the Playwright admin test suite with the backend available in CI, including cover upload coverage.

## Current Status

- API provides public blog APIs, admin post CRUD, and authenticated cover image upload.
- Blog reads published posts from the backend.
- Admin supports login, posts CRUD, ByteMD editing, split Markdown preview, search/status filters, quick publish/unpublish, public View links, View Public Post links, cover image upload, cover URL auto-fill, and cover preview.
- CI covers admin build, API smoke test, blog build, and admin Playwright E2E.

## Notes

- Blog build needs the backend API running.
- Admin uses `VITE_API_BASE_URL` and `VITE_PUBLIC_BLOG_BASE_URL`.
- Blog uses `PUBLIC_API_BASE_URL`.
- Uploaded files are served by the API under `/uploads`.
- Local backend may run on `8001` if `8000` is blocked on Windows.
- Do not put real secrets into `.env.example` files or this README.
