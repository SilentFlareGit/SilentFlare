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

### GET /api/v1/admin/posts

Requires authentication. Lists all posts, including drafts.

Response:

```json
{
  "items": [
    {
      "id": 1,
      "title": "First Post",
      "slug": "first-post",
      "summary": "A short summary.",
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

Requires authentication. Returns one post, including drafts.

Response:

```json
{
  "id": 1,
  "title": "First Post",
  "slug": "first-post",
  "summary": "A short summary.",
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
  "status": "published"
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
