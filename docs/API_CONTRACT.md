# SilentFlare Blog API Contract

## Domains

- Main site: https://silentflare.com
- Blog frontend: https://blog.silentflare.com
- API backend: https://api.silentflare.com
- Admin panel: https://admin.silentflare.com

## Public Blog APIs

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

### POST /api/v1/auth/login

Login to admin panel.

### POST /api/v1/auth/logout

Logout from admin panel.

### GET /api/v1/admin/posts

List all posts, including drafts.

### POST /api/v1/admin/posts

Create a new post.

### PUT /api/v1/admin/posts/{id}

Update a post.

### DELETE /api/v1/admin/posts/{id}

Delete a post.

### POST /api/v1/admin/upload

Upload cover images or article images.