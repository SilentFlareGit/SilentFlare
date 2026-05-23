# SilentFlare

SilentFlare is a small monorepo for the public blog, the FastAPI backend, and
the admin frontend. This README is the local development starting point and the
high-level project map for future AI-assisted work.

## Project Overview

- `apps/api`: FastAPI backend with public blog APIs, admin post CRUD APIs, authenticated cover image upload, and cover media listing/deletion for unused files.
- `apps/blog`: Astro/Yukina public blog frontend. It reads published posts from the backend public APIs.
- `apps/admin`: Vue 3 + Vite admin frontend with login, posts CRUD, ByteMD editing, split Markdown preview, search/status filters, quick publish/unpublish, public view links, cover upload, media cleanup, and Playwright E2E coverage.
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

If port `8000` is blocked on Windows, use `8011` for local testing:

```cmd
uvicorn app.main:app --reload --host 127.0.0.1 --port 8011
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

Use `http://127.0.0.1:8011/api/v1` if the backend is running on port `8011`.

`apps/blog/.env`:

```text
PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

Use `http://127.0.0.1:8011/api/v1` if the backend is running on port `8011`.

## Validation Commands

Admin build:

```cmd
cd apps\admin
npm run build
```

Admin Playwright E2E:

```cmd
cd apps\admin
set "VITE_API_BASE_URL=http://127.0.0.1:8011/api/v1" && npm run test:e2e
```

Local admin E2E requires the API backend running unless CI starts it for the job. Expected result: Playwright reports the admin spec passing, such as `1 passed`. The suite covers login, post CRUD, cover upload, used cover display on `/media` without a delete button, and unused cover deletion from `/media`.

Backend smoke test:

```cmd
cd apps\api
python scripts\smoke_test.py --base-url http://127.0.0.1:8011
```

Run `scripts\smoke_test.py` from `apps\api`; its relative imports and paths assume that working directory.

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
- Admin E2E: runs the Playwright admin test suite with the backend available in CI, including cover upload, used media protection, and unused media deletion.

## Current Status

- API provides public blog APIs, admin post CRUD, authenticated cover image upload, cover media listing, and unused cover deletion. Uploaded cover files are served under `/uploads/covers/...`.
- Blog reads published posts from the backend.
- Admin supports login, posts CRUD, ByteMD editing, split Markdown preview, search/status filters, quick publish/unpublish, public View links, View Public Post links, cover upload, cover preview, posts-list cover thumbnails, and `/media` cleanup. Used covers show `Used` / `In use` and cannot be deleted; unused covers show `Delete` and can be removed.
- CI covers admin build, API smoke test, blog build, and admin Playwright E2E.

## Notes

- Blog build needs the backend API running.
- Admin uses `VITE_API_BASE_URL` and `VITE_PUBLIC_BLOG_BASE_URL`.
- Blog uses `PUBLIC_API_BASE_URL`.
- Uploaded files are served by the API under `/uploads`, including cover images under `/uploads/covers/...`.
- Local backend often uses `8011` to avoid Windows port conflicts.
- Do not put real secrets into `.env.example` files or this README.
