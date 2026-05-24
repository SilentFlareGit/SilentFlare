import os
from pathlib import Path
from typing import Generator

from sqlalchemy import inspect
from sqlmodel import Session, SQLModel, create_engine, select

from app.models.post import Post, PostStatus, utc_now_iso


API_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATABASE_PATH = API_ROOT / "data" / "blog.db"
DATABASE_PATH = Path(os.getenv("SILENTFLARE_DATABASE_PATH", DEFAULT_DATABASE_PATH))
DATABASE_URL = f"sqlite:///{DATABASE_PATH.as_posix()}"

DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SEED_POSTS = [
    {
        "id": 1,
        "title": "First Post",
        "slug": "first-post",
        "summary": "A short summary.",
        "seo_title": "First Post | SilentFlare",
        "meta_description": "A short summary for the first SilentFlare post.",
        "content_markdown": "# Hello",
        "cover_url": "http://127.0.0.1:8000/uploads/covers/first-post.jpg",
        "status": PostStatus.published.value,
        "category": "Notes",
        "tags": ["personal", "blog"],
        "created_at": "2026-05-20T12:00:00Z",
        "updated_at": "2026-05-20T12:00:00Z",
        "published_at": "2026-05-20T12:00:00Z",
    },
    {
        "id": 2,
        "title": "Building SilentFlare",
        "slug": "building-silentflare",
        "summary": "Notes from the first backend pass.",
        "seo_title": "Building SilentFlare | SilentFlare",
        "meta_description": "Notes from the first backend pass.",
        "content_markdown": "# Building SilentFlare\n\nThis is mock content for the first API version.",
        "cover_url": "http://127.0.0.1:8000/uploads/covers/building-silentflare.jpg",
        "status": PostStatus.published.value,
        "category": "Development",
        "tags": ["fastapi", "backend"],
        "created_at": "2026-05-20T13:00:00Z",
        "updated_at": "2026-05-20T13:00:00Z",
        "published_at": "2026-05-20T13:00:00Z",
    },
]


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    migrate_existing_posts_table()
    seed_posts_if_empty()


def migrate_existing_posts_table() -> None:
    inspector = inspect(engine)
    if "posts" not in inspector.get_table_names():
        return

    columns = {column["name"] for column in inspector.get_columns("posts")}
    now = utc_now_iso()

    with engine.begin() as connection:
        if "status" not in columns:
            connection.exec_driver_sql("ALTER TABLE posts ADD COLUMN status VARCHAR NOT NULL DEFAULT 'published'")
        if "created_at" not in columns:
            connection.exec_driver_sql(f"ALTER TABLE posts ADD COLUMN created_at VARCHAR NOT NULL DEFAULT '{now}'")
        if "updated_at" not in columns:
            connection.exec_driver_sql(f"ALTER TABLE posts ADD COLUMN updated_at VARCHAR NOT NULL DEFAULT '{now}'")
        if "seo_title" not in columns:
            connection.exec_driver_sql("ALTER TABLE posts ADD COLUMN seo_title VARCHAR NOT NULL DEFAULT ''")
        if "meta_description" not in columns:
            connection.exec_driver_sql("ALTER TABLE posts ADD COLUMN meta_description VARCHAR NOT NULL DEFAULT ''")

        connection.exec_driver_sql("CREATE UNIQUE INDEX IF NOT EXISTS ix_posts_slug_unique ON posts (slug)")


def seed_posts_if_empty() -> None:
    with Session(engine) as session:
        existing_post = session.exec(select(Post)).first()
        if existing_post is not None:
            return

        session.add_all(Post(**post) for post in SEED_POSTS)
        session.commit()


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
