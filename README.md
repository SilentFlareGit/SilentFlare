# SilentFlare

SilentFlare is a small monorepo for the public blog, the FastAPI backend, and
the admin frontend. This README is the local development starting point and the
high-level project map for future AI-assisted work.

## Project Overview

- `apps/api`: FastAPI backend with public blog APIs, admin post CRUD APIs, server-side admin post filtering/pagination, post SEO fields, authenticated cover image upload, and cover media listing/deletion for unused files.
- `apps/blog`: Astro/Yukina public blog frontend. It reads published posts from the backend public APIs, shows category/tag badges, and uses post SEO fields on detail pages.
- `apps/admin`: Vue 3 + Vite admin frontend with login, posts CRUD, normal Save/Update, Save/Update and keep editing, internal post preview, SEO title/meta description editing, server-side search/status/SEO filters, simple posts pagination, ByteMD editing, split Markdown preview, quick publish/unpublish, public view links, cover upload, media cleanup, and Playwright E2E coverage.
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

For local E2E, start the backend on port `8011` first to avoid common Windows
port conflicts:

```cmd
cd apps\api
uvicorn app.main:app --reload --host 127.0.0.1 --port 8011
```

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

Local admin E2E requires the API backend running unless CI starts it for the
job. Expected result: Playwright reports the admin suite passing. The suite
covers login, post CRUD, server-side post filters/pagination, admin preview,
cover upload, used cover display on `/media` without a delete action, unused
cover deletion from `/media`, and the admin Save/Update and keep editing
workflow.

Backend smoke test:

```cmd
cd apps\api
python scripts\smoke_test.py --base-url http://127.0.0.1:8011
```

Run `scripts\smoke_test.py` from `apps\api`; its relative imports and paths assume that working directory.

Blog type check:

```cmd
cd apps\blog
pnpm run check
```

Blog build:

```cmd
cd apps\blog
pnpm run build
```

## CI

GitHub Actions runs on push and pull request to `main`:

- Admin build: installs `apps/admin` dependencies and runs `npm run build`.
- API smoke test: installs `apps/api` dependencies, compiles backend code, starts Uvicorn, and runs `scripts/smoke_test.py`, including admin post filter and pagination coverage.
- Blog build: installs `apps/blog` dependencies, starts the backend, runs `pnpm run check`, and builds with `PUBLIC_API_STRICT=true` so backend-fed post fetch is verified.
- Admin E2E: runs the Playwright admin test suite with the backend available in CI, including post CRUD, Save/Update and keep editing, preview from the posts list and edit form, server-side post filtering/pagination, cover upload, used media protection, and unused media deletion.

## Current Status

- API provides public blog APIs, admin post CRUD, admin post list filters (`search`, `status`, `seo`) with pagination (`limit`, `offset`, `total` before pagination), `seo_title` / `meta_description`, authenticated cover image upload, cover media listing, and unused cover deletion. Uploaded cover files are served under `/uploads/covers/...`.
- Blog reads published posts from the backend. Post lists and detail pages display category/tags as non-linked badges/spans. Post detail pages use `seo_title` for HTML title/meta/OG/Twitter title when present, falling back to `title`; descriptions use `meta_description`, falling back to `summary`.
- Admin supports login, posts CRUD, normal Save/Update actions that return to the Posts list, and Save/Update and keep editing actions that keep the user in the editing workflow. For new posts, keep editing routes to the newly created post's edit page. Admin also supports internal post preview, SEO Title and Meta Description editing, server-side search/status/SEO filters, Previous/Next posts pagination with `Page N of M` and `Showing X of Y posts`, ByteMD editing, split Markdown preview, quick publish/unpublish, public View links, View Public Post links, cover upload, cover preview, posts-list cover thumbnails, and `/media` cleanup. Draft posts can be previewed inside admin without publishing; this preview is not public and does not expose drafts through `apps/blog`. `SEO OK` means both SEO fields are non-empty after trim; `Missing SEO` means either field is empty. Admin post search matches title, slug, category, summary, tags, `seo_title`, and `meta_description`. On `/media`, used cover files show `Used` / `In use` and cannot be deleted; unused cover files show `Delete` and can be removed.
- CI covers admin build, API smoke test, blog build, and admin Playwright E2E.

## Notes

- Blog build needs the backend API running.
- Admin uses `VITE_API_BASE_URL` and `VITE_PUBLIC_BLOG_BASE_URL`.
- Blog uses `PUBLIC_API_BASE_URL`.
- Local blog builds keep API fallback behavior unless `PUBLIC_API_STRICT=true` is set.
- Uploaded files are served by the API under `/uploads`, including cover images under `/uploads/covers/...`.
- Local backend often uses `8011` to avoid Windows port conflicts.
- Do not put real secrets into `.env.example` files or this README.
