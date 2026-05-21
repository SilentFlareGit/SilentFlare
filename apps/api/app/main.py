from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.db.session import init_db
from app.routers.admin_posts import router as admin_posts_router
from app.routers.auth import router as auth_router
from app.routers.public_posts import router as public_posts_router


app = FastAPI(title="SilentFlare Blog API")
UPLOADS_DIR = Path(__file__).resolve().parent.parent / "uploads"

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://blog.silentflare.com",
        "https://admin.silentflare.com",
        "http://localhost:4321",
        "http://127.0.0.1:4321",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOADS_DIR), name="uploads")
app.include_router(auth_router)
app.include_router(admin_posts_router)
app.include_router(public_posts_router)


class HealthResponse(BaseModel):
    status: str


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> dict[str, str]:
    return {"status": "ok"}
