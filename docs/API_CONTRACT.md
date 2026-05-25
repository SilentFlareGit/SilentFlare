# SilentFlare Blog API Contract

## Domains

- Main site: https://silentflare.com
- Blog frontend: https://blog.silentflare.com
- API backend: https://api.silentflare.com
- Admin panel: https://admin.silentflare.com

## Public Blog APIs

Public post endpoints return published posts only. Draft posts are only visible
through authenticated admin APIs.

### GET /api/v1/health

Response:

```json
{
  "status": "ok"
}
```

### GET /api/v1/posts

Response:

```json
{
  "items": [
    {
      "id": 1,
      "title": "First Post",
      "slug": "first-post",
      "summary": "A short summary.",
      "seo_title": "First Post | SilentFlare",
      "meta_description": "A short summary for the first SilentFlare post.",
      "cover_url": "https://api.silentflare.com/uploads/covers/first-post.jpg",
      "category": "Notes",
      "tags": ["personal", "blog"],
      "published_at": "2026-05-20T12:00:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/v1/posts/{slug}

Response:

```json
{
  "id": 1,
  "title": "First Post",
  "slug": "first-post",
  "summary": "A short summary.",
  "seo_title": "First Post | SilentFlare",
  "meta_description": "A short summary for the first SilentFlare post.",
  "content_markdown": "# Hello",
  "cover_url": "https://api.silentflare.com/uploads/covers/first-post.jpg",
  "category": "Notes",
  "tags": ["personal", "blog"],
  "published_at": "2026-05-20T12:00:00Z"
}
```

## Admin APIs

Admin APIs use Bearer token authentication. Get a token from
`POST /api/v1/auth/login`, then send it as:

```http
Authorization: Bearer <access_token>
```

### POST /api/v1/auth/login

Request:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

Response:

```json
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

### POST /api/v1/auth/logout

Requires authentication.

Response:

```json
{
  "status": "ok"
}
```

### POST /api/v1/admin/uploads/cover

Requires authentication. Uploads a cover image and returns a `cover_url` string
that can be saved in a post.

Request: `multipart/form-data`

- `file`: image file. Supported types: JPEG, PNG, WebP, GIF.

Response:

```json
{
  "cover_url": "http://127.0.0.1:8000/uploads/covers/6f1f7f4f0b784b3e8f98d0f01cfc3a2d.png",
  "path": "/uploads/covers/6f1f7f4f0b784b3e8f98d0f01cfc3a2d.png"
}
```

### GET /api/v1/admin/uploads/covers

Requires authentication. Lists cover files directly under `/uploads/covers/`
and reports whether each file is referenced by any post `cover_url`.

Response:

```json
{
  "items": [
    {
      "filename": "6f1f7f4f0b784b3e8f98d0f01cfc3a2d.png",
      "path": "/uploads/covers/6f1f7f4f0b784b3e8f98d0f01cfc3a2d.png",
      "cover_url": "http://127.0.0.1:8000/uploads/covers/6f1f7f4f0b784b3e8f98d0f01cfc3a2d.png",
      "size_bytes": 1234,
      "modified_at": "2026-05-23T12:00:00Z",
      "used": true,
      "used_by_post_ids": [1]
    }
  ],
  "total": 1
}
```

### DELETE /api/v1/admin/uploads/covers/{filename}

Requires authentication. Deletes an unused cover file. Files referenced by any
post `cover_url` return `409 Conflict` and are not deleted.

The admin `/media` page uses these cover APIs for cleanup: used files are shown
as `Used` / `In use` and cannot be deleted, while unused files expose a
`Delete` button and can be removed.

Response:

```json
{
  "status": "deleted",
  "filename": "6f1f7f4f0b784b3e8f98d0f01cfc3a2d.png"
}
```

### GET /api/v1/admin/posts

Requires authentication. Lists both draft and published posts.

Optional query parameters:

- `search`: case-insensitive match across title, slug, summary, category,
  tags, `seo_title`, and `meta_description`.
- `status`: `draft`, `published`, or `all`. Missing or `all` returns both
  draft and published posts.
- `seo`: `ok`, `missing`, or `all`. `ok` means both `seo_title` and
  `meta_description` are non-empty after trim; `missing` means either field is
  empty or whitespace.

Example:

```http
GET /api/v1/admin/posts?status=published&seo=ok&search=release
```

Response:

```json
{
  "items": [
    {
      "id": 1,
      "title": "First Post",
      "slug": "first-post",
      "summary": "A short summary.",
      "seo_title": "First Post | SilentFlare",
      "meta_description": "A short summary for the first SilentFlare post.",
      "content_markdown": "# Hello",
      "cover_url": "https://api.silentflare.com/uploads/covers/first-post.jpg",
      "status": "published",
      "category": "Notes",
      "tags": ["personal", "blog"],
      "created_at": "2026-05-20T12:00:00Z",
      "updated_at": "2026-05-20T12:00:00Z",
      "published_at": "2026-05-20T12:00:00Z"
    }
  ],
  "total": 1
}
```

### GET /api/v1/admin/posts/{id}

Requires authentication. Returns one draft or published post by numeric `id`.

Response:

```json
{
  "id": 1,
  "title": "First Post",
  "slug": "first-post",
  "summary": "A short summary.",
  "seo_title": "First Post | SilentFlare",
  "meta_description": "A short summary for the first SilentFlare post.",
  "content_markdown": "# Hello",
  "cover_url": "https://api.silentflare.com/uploads/covers/first-post.jpg",
  "status": "published",
  "category": "Notes",
  "tags": ["personal", "blog"],
  "created_at": "2026-05-20T12:00:00Z",
  "updated_at": "2026-05-20T12:00:00Z",
  "published_at": "2026-05-20T12:00:00Z"
}
```

### POST /api/v1/admin/posts

Requires authentication. Creates a draft or published post. If `slug` is
missing, it is generated from `title`. Slugs must be unique.

Request:

```json
{
  "title": "New Draft",
  "summary": "Draft summary.",
  "seo_title": "Draft SEO Title",
  "meta_description": "Draft meta description.",
  "content_markdown": "# Draft",
  "cover_url": "",
  "status": "draft",
  "category": "Notes",
  "tags": ["draft"]
}
```

Response: `201 Created`

```json
{
  "id": 3,
  "title": "New Draft",
  "slug": "new-draft",
  "summary": "Draft summary.",
  "seo_title": "Draft SEO Title",
  "meta_description": "Draft meta description.",
  "content_markdown": "# Draft",
  "cover_url": "",
  "status": "draft",
  "category": "Notes",
  "tags": ["draft"],
  "created_at": "2026-05-21T10:00:00Z",
  "updated_at": "2026-05-21T10:00:00Z",
  "published_at": ""
}
```

### PUT /api/v1/admin/posts/{id}

Requires authentication. Updates provided fields and refreshes `updated_at`.

Request:

```json
{
  "title": "Updated Draft",
  "summary": "Updated summary.",
  "seo_title": "Updated SEO Title",
  "meta_description": "Updated meta description.",
  "status": "published",
  "tags": ["updated"]
}
```

Response: admin post response.

### DELETE /api/v1/admin/posts/{id}

Requires authentication. Hard deletes a post for now.

Response:

```json
{
  "status": "deleted",
  "id": 3
}
```

## Local Development

The backend reads these environment variables:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `JWT_SECRET_KEY`
- `SILENTFLARE_DATABASE_PATH`

Local example credentials are documented in `apps/api/.env.example`. Do not use
the example secret values in production.

Start the local backend on `8011` when the usual ports are occupied:

```cmd
uvicorn app.main:app --reload --host 127.0.0.1 --port 8011
```

Run the backend smoke test from `apps/api`:

```cmd
python scripts\smoke_test.py --base-url http://127.0.0.1:8011
```

Run admin E2E from `apps/admin` against that backend:

```cmd
set "VITE_API_BASE_URL=http://127.0.0.1:8011/api/v1" && npm run test:e2e
```

Expected result: Playwright reports the admin suite passing. The suite covers
login, post CRUD, cover upload, used cover protection on `/media`, and unused
cover deletion from `/media`.
