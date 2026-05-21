# SilentFlare API

Minimal FastAPI backend for the public blog APIs.

The API uses SQLite by default at `apps/api/data/blog.db`. Set
`SILENTFLARE_DATABASE_PATH` to point at a different SQLite file.

Admin auth reads these environment variables:

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `JWT_SECRET_KEY`

For local development, copy `.env.example` to `.env`. The example credentials
are:

- Username: `admin`
- Password: `admin123`

## Run on Windows CMD

From the repository root:

```cmd
cd apps\api
python -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

The database tables are created on startup. If the posts table is empty, the
current two public mock posts are seeded automatically.

## Initialize Database Only

From `apps\api`:

```cmd
.venv\Scripts\activate.bat
python -c "from app.db.session import init_db; init_db()"
```

Open:

- Health: http://127.0.0.1:8000/api/v1/health
- Posts: http://127.0.0.1:8000/api/v1/posts
- One post: http://127.0.0.1:8000/api/v1/posts/first-post
- Swagger: http://127.0.0.1:8000/docs

## Test Admin APIs From Swagger

1. Start the backend with the run command above.
2. Open http://127.0.0.1:8000/docs.
3. Run `POST /api/v1/auth/login` with:

```json
{
  "username": "admin",
  "password": "admin123"
}
```

4. Copy the `access_token` from the response.
5. Click `Authorize` in Swagger.
6. Enter the token as the HTTP Bearer value.
7. Use the `/api/v1/admin/posts` endpoints to create, update, or delete posts.

Draft posts appear in admin APIs but not in the public `GET /api/v1/posts`
response. Published posts appear in both.

## Run Smoke Tests

Start the backend first. If port `8000` is busy, start it on `8001`:

```cmd
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

Then run:

```cmd
python scripts\smoke_test.py --base-url http://127.0.0.1:8001
```

For the default `8000` port:

```cmd
python scripts\smoke_test.py --base-url http://127.0.0.1:8000
```

## Current Scope

- Public blog endpoints only
- Minimal token-protected admin post APIs
- SQLite-backed posts seeded from the current mock data
- No admin frontend
- No upload
