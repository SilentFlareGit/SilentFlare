from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status

from app.core.security import require_admin


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

    path = f"/uploads/covers/{filename}"
    return {
        "cover_url": str(request.base_url).rstrip("/") + path,
        "path": path,
    }
