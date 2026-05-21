# SilentFlare Admin Panel

Minimal admin frontend for managing blog posts on admin.silentflare.com.

Built with Vue 3 + Vite.

## Setup (Windows CMD)

```cmd
cd apps\admin
copy .env.example .env
npm install
npm run dev
```

The dev server starts at http://localhost:5174.

## Environment Variables

| Variable             | Description        | Default                                  |
| -------------------- | ------------------ | ---------------------------------------- |
| `VITE_API_BASE_URL`  | Backend API base   | `http://127.0.0.1:8000/api/v1`           |

Set these in `.env` (git-ignored) or `.env.local`.

## Pages

| Route               | Description                |
| -------------------- | -------------------------- |
| `#/login`            | Admin login                |
| `#/posts`            | List all posts             |
| `#/posts/new`        | Create a new post          |
| `#/posts/:id/edit`   | Edit an existing post      |

## Production Build

```cmd
npm run build
npm run preview
```

The build output goes to `dist/`.
