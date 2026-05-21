from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PostStatusValue = Literal["draft", "published"]


class PostListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    summary: str
    cover_url: str
    category: str
    tags: list[str]
    published_at: str


class PostListResponse(BaseModel):
    items: list[PostListItem]
    total: int


class PostDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    summary: str
    content_markdown: str
    cover_url: str
    category: str
    tags: list[str]
    published_at: str


class AdminPostCreate(BaseModel):
    title: str
    slug: str | None = None
    summary: str
    content_markdown: str
    cover_url: str = ""
    status: PostStatusValue = "draft"
    category: str = "Notes"
    tags: list[str] = Field(default_factory=list)
    published_at: str | None = None


class AdminPostUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    summary: str | None = None
    content_markdown: str | None = None
    cover_url: str | None = None
    status: PostStatusValue | None = None
    category: str | None = None
    tags: list[str] | None = None
    published_at: str | None = None


class AdminPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    slug: str
    summary: str
    content_markdown: str
    cover_url: str
    status: PostStatusValue
    category: str
    tags: list[str]
    created_at: str
    updated_at: str
    published_at: str


class AdminPostListResponse(BaseModel):
    items: list[AdminPostResponse]
    total: int


class DeletePostResponse(BaseModel):
    status: str
    id: int
