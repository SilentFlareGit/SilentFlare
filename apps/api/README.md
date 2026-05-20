# SilentFlare API

Minimal FastAPI backend for the public blog APIs.

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

Open:

- Health: http://127.0.0.1:8000/api/v1/health
- Posts: http://127.0.0.1:8000/api/v1/posts
- One post: http://127.0.0.1:8000/api/v1/posts/first-post

## Current Scope

- Public blog endpoints only
- Mock posts only
- No admin APIs
- No database
- No auth
