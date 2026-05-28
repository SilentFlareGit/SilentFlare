import re
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.security import require_admin
from app.db.session import get_session
from app.models.post import Post, PostStatus, utc_now_iso
from app.schemas.post import (
    AdminPostCreate,
    AdminPostListResponse,
    AdminPostResponse,
    AdminPostUpdate,
    DeletePostResponse,
)


router = APIRouter(prefix="/api/v1/admin/posts", tags=["admin-posts"], dependencies=[Depends(require_admin)])


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "post"


def find_post_by_slug(session: Session, slug: str) -> Post | None:
    return session.exec(select(Post).where(Post.slug == slug)).first()


def ensure_unique_slug(session: Session, slug: str, current_post_id: int | None = None) -> None:
    existing = find_post_by_slug(session, slug)
    if existing is not None and existing.id != current_post_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists")


def make_unique_slug(session: Session, title: str) -> str:
    base_slug = slugify(title)
    slug = base_slug
    counter = 2

    while find_post_by_slug(session, slug) is not None:
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def published_at_for_status(status_value: str, published_at: str | None = None) -> str:
    if published_at is not None:
        return published_at
    if status_value == PostStatus.published.value:
        return utc_now_iso()
    return ""


def has_complete_seo(post: Post) -> bool:
    return bool(post.seo_title.strip() and post.meta_description.strip())


def matches_admin_search(post: Post, search: str) -> bool:
    needle = search.strip().lower()
    if not needle:
        return True

    values = [
        post.title,
        post.slug,
        post.summary,
        post.category,
        post.seo_title,
        post.meta_description,
        *post.tags,
    ]
    return any(needle in value.lower() for value in values)


@router.get("", response_model=AdminPostListResponse)
def list_admin_posts(
    search: str | None = None,
    status_filter: Literal["draft", "published", "all"] | None = Query(default=None, alias="status"),
    seo: Literal["ok", "missing", "all"] | None = None,
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: Session = Depends(get_session),
) -> AdminPostListResponse:
    statement = select(Post).order_by(Post.id)
    if status_filter in {PostStatus.draft.value, PostStatus.published.value}:
        statement = statement.where(Post.status == status_filter)

    posts = session.exec(statement).all()
    if seo == "ok":
        posts = [post for post in posts if has_complete_seo(post)]
    elif seo == "missing":
        posts = [post for post in posts if not has_complete_seo(post)]

    if search is not None:
        posts = [post for post in posts if matches_admin_search(post, search)]

    total = len(posts)
    if limit is not None:
        posts = posts[offset : offset + limit]

    items = [AdminPostResponse.model_validate(post) for post in posts]

    return AdminPostListResponse(items=items, total=total)


@router.get("/{id}", response_model=AdminPostResponse)
def get_admin_post(id: int, session: Session = Depends(get_session)) -> Post:
    post = session.get(Post, id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return post


@router.post("", response_model=AdminPostResponse, status_code=status.HTTP_201_CREATED)
def create_admin_post(payload: AdminPostCreate, session: Session = Depends(get_session)) -> Post:
    slug = slugify(payload.slug) if payload.slug else make_unique_slug(session, payload.title)
    ensure_unique_slug(session, slug)

    now = utc_now_iso()
    post = Post(
        title=payload.title,
        slug=slug,
        summary=payload.summary,
        seo_title=payload.seo_title,
        meta_description=payload.meta_description,
        content_markdown=payload.content_markdown,
        cover_url=payload.cover_url,
        status=payload.status,
        category=payload.category,
        tags=payload.tags,
        created_at=now,
        updated_at=now,
        published_at=published_at_for_status(payload.status, payload.published_at),
    )

    session.add(post)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists") from exc

    session.refresh(post)
    return post


@router.put("/{id}", response_model=AdminPostResponse)
def update_admin_post(id: int, payload: AdminPostUpdate, session: Session = Depends(get_session)) -> Post:
    post = session.get(Post, id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    data = payload.model_dump(exclude_unset=True)
    if "slug" in data and data["slug"] is not None:
        slug = slugify(data["slug"])
        ensure_unique_slug(session, slug, current_post_id=id)
        post.slug = slug

    for field_name in [
        "title",
        "summary",
        "seo_title",
        "meta_description",
        "content_markdown",
        "cover_url",
        "category",
        "tags",
    ]:
        if field_name in data:
            setattr(post, field_name, data[field_name])

    if "status" in data:
        post.status = data["status"]
        if data["status"] == PostStatus.published.value and not post.published_at:
            post.published_at = utc_now_iso()

    if "published_at" in data:
        post.published_at = data["published_at"] or ""

    post.updated_at = utc_now_iso()

    try:
        session.add(post)
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Slug already exists") from exc

    session.refresh(post)
    return post


@router.delete("/{id}", response_model=DeletePostResponse)
def delete_admin_post(id: int, session: Session = Depends(get_session)) -> DeletePostResponse:
    post = session.get(Post, id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    session.delete(post)
    session.commit()

    return DeletePostResponse(status="deleted", id=id)
