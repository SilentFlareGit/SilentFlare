from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.db.session import get_session
from app.models.post import Post
from app.schemas.post import PostDetailResponse, PostListItem, PostListResponse


router = APIRouter(prefix="/api/v1", tags=["public-posts"])


@router.get("/posts", response_model=PostListResponse)
def list_posts(session: Session = Depends(get_session)) -> PostListResponse:
    posts = session.exec(select(Post).where(Post.status == "published").order_by(Post.id)).all()
    items = [PostListItem.model_validate(post) for post in posts]

    return PostListResponse(items=items, total=len(items))


@router.get("/posts/{slug}", response_model=PostDetailResponse)
def get_post(slug: str, session: Session = Depends(get_session)) -> Post:
    post = session.exec(select(Post).where(Post.slug == slug, Post.status == "published")).first()
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return post
