from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from sqlmodel import Session, select

from app.core.security import require_admin
from app.db.session import get_session
from app.models.post import Post


router = APIRouter(prefix="/api/v1/admin/uploads", tags=["admin-uploads"], dependencies=[Depends(require_admin)])

UPLOAD_COVERS_DIR = Path(__file__).resolve().parents[2] / "uploads" / "covers"

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}

SUFFIX_EXTENSIONS = {
    ".jpeg": ".jpg",
    ".jpg": ".jpg",
    ".png": ".png",
    ".webp": ".webp",
    ".gif": ".gif",
}


def upload_path_for_filename(filename: str) -> str:
    return f"/uploads/covers/{filename}"


def cover_url_for_path(request: Request, path: str) -> str:
    return str(request.base_url).rstrip("/") + path


def normalized_cover_path(cover_url: str) -> str:
    parsed = urlparse(cover_url)
    path = parsed.path or cover_url
    return path if path.startswith("/") else f"/{path}"


def posts_by_cover_path(session: Session) -> dict[str, list[int]]:
    posts = session.exec(select(Post)).all()
    usage: dict[str, list[int]] = {}

    for post in posts:
        if not post.cover_url:
            continue
        if post.id is None:
            continue

        path = normalized_cover_path(post.cover_url)
        usage.setdefault(path, []).append(post.id)

    return usage


def safe_cover_file_path(filename: str) -> Path:
    if not filename or "/" in filename or "\\" in filename or Path(filename).name != filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    covers_dir = UPLOAD_COVERS_DIR.resolve()
    file_path = (covers_dir / filename).resolve()
    if file_path.parent != covers_dir:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename")

    return file_path


def detect_image_extension(content: bytes, content_type: str | None, filename: str | None) -> str:
    if content_type and content_type not in CONTENT_TYPE_EXTENSIONS and content_type != "application/octet-stream":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image type")

    if content.startswith(b"\xff\xd8\xff"):
        detected_extension = ".jpg"
    elif content.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_extension = ".png"
    elif len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP":
        detected_extension = ".webp"
    elif content.startswith((b"GIF87a", b"GIF89a")):
        detected_extension = ".gif"
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported image file")

    expected_extension = CONTENT_TYPE_EXTENSIONS.get(content_type or "")
    if expected_extension is not None and expected_extension != detected_extension:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Image content type does not match file")

    original_extension = SUFFIX_EXTENSIONS.get(Path(filename or "").suffix.lower())
    if original_extension == detected_extension:
        return original_extension

    return detected_extension


@router.post("/cover")
async def upload_cover_image(request: Request, file: UploadFile = File(...)) -> dict[str, str]:
    content = await file.read()
    extension = detect_image_extension(content, file.content_type, file.filename)

    UPLOAD_COVERS_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        filename = f"{uuid4().hex}{extension}"
        destination = UPLOAD_COVERS_DIR / filename
        if not destination.exists():
            break

    destination.write_bytes(content)

    path = upload_path_for_filename(filename)
    return {
        "cover_url": cover_url_for_path(request, path),
        "path": path,
    }


@router.get("/covers")
def list_cover_images(request: Request, session: Session = Depends(get_session)) -> dict:
    UPLOAD_COVERS_DIR.mkdir(parents=True, exist_ok=True)
    usage = posts_by_cover_path(session)
    items = []

    for file_path in sorted(UPLOAD_COVERS_DIR.iterdir(), key=lambda path: path.name):
        if not file_path.is_file():
            continue

        stat = file_path.stat()
        path = upload_path_for_filename(file_path.name)
        used_by_post_ids = sorted(usage.get(path, []))
        items.append(
            {
                "filename": file_path.name,
                "path": path,
                "cover_url": cover_url_for_path(request, path),
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc)
                .replace(microsecond=0)
                .isoformat()
                .replace("+00:00", "Z"),
                "used": bool(used_by_post_ids),
                "used_by_post_ids": used_by_post_ids,
            }
        )

    return {"items": items, "total": len(items)}


@router.delete("/covers/{filename}")
def delete_cover_image(filename: str, session: Session = Depends(get_session)) -> dict[str, str]:
    file_path = safe_cover_file_path(filename)
    if not file_path.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cover file not found")

    path = upload_path_for_filename(filename)
    used_by_post_ids = posts_by_cover_path(session).get(path, [])
    if used_by_post_ids:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cover file is used by a post")

    file_path.unlink()
    return {"status": "deleted", "filename": filename}
