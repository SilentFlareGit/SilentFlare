from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


app = FastAPI(title="SilentFlare Blog API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://blog.silentflare.com",
        "http://localhost:4321",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


MOCK_POSTS = [
    {
        "id": 1,
        "title": "First Post",
        "slug": "first-post",
        "summary": "A short summary.",
        "content_markdown": "# Hello",
        "cover_url": "https://api.silentflare.com/uploads/covers/first-post.jpg",
        "category": "Notes",
        "tags": ["personal", "blog"],
        "published_at": "2026-05-20T12:00:00Z",
    },
    {
        "id": 2,
        "title": "Building SilentFlare",
        "slug": "building-silentflare",
        "summary": "Notes from the first backend pass.",
        "content_markdown": "# Building SilentFlare\n\nThis is mock content for the first API version.",
        "cover_url": "https://api.silentflare.com/uploads/covers/building-silentflare.jpg",
        "category": "Development",
        "tags": ["fastapi", "backend"],
        "published_at": "2026-05-20T13:00:00Z",
    },
]


class HealthResponse(BaseModel):
    status: str


class PostListItem(BaseModel):
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
    id: int
    title: str
    slug: str
    summary: str
    content_markdown: str
    cover_url: str
    category: str
    tags: list[str]
    published_at: str


@app.get("/api/v1/health", response_model=HealthResponse)
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/posts", response_model=PostListResponse)
def list_posts() -> dict[str, object]:
    items = [
        {
            "id": post["id"],
            "title": post["title"],
            "slug": post["slug"],
            "summary": post["summary"],
            "cover_url": post["cover_url"],
            "category": post["category"],
            "tags": post["tags"],
            "published_at": post["published_at"],
        }
        for post in MOCK_POSTS
    ]

    return {"items": items, "total": len(items)}


@app.get("/api/v1/posts/{slug}", response_model=PostDetailResponse)
def get_post(slug: str) -> dict[str, object]:
    for post in MOCK_POSTS:
        if post["slug"] == slug:
            return post

    raise HTTPException(status_code=404, detail="Post not found")
