from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, JSON, String
from sqlmodel import Field, SQLModel


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class PostStatus(str, Enum):
    draft = "draft"
    published = "published"


class Post(SQLModel, table=True):
    __tablename__ = "posts"

    id: int | None = Field(default=None, primary_key=True)
    title: str
    slug: str = Field(sa_column=Column(String, unique=True, index=True, nullable=False))
    summary: str
    seo_title: str = ""
    meta_description: str = ""
    content_markdown: str
    cover_url: str
    status: str = Field(default=PostStatus.published.value)
    category: str
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON, nullable=False))
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    published_at: str = ""
