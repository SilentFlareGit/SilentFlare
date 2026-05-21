from fastapi import APIRouter, Depends, HTTPException, status

from app.core.security import create_access_token, require_admin, verify_admin_credentials
from app.schemas.auth import LoginRequest, StatusResponse, TokenResponse


router = APIRouter(prefix="/api/v1/auth", tags=["admin-auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest) -> TokenResponse:
    if not verify_admin_credentials(payload.username, payload.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username or password")

    return TokenResponse(access_token=create_access_token(payload.username))


@router.post("/logout", response_model=StatusResponse)
def logout(_: str = Depends(require_admin)) -> StatusResponse:
    return StatusResponse(status="ok")
