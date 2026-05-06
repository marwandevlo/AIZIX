from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_token
from app.db.database import get_db
from app.db.models import User

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    settings = get_settings()

    token: str | None = creds.credentials if creds and creds.scheme.lower() == "bearer" else None
    auth_header = request.headers.get("Authorization")
    if not token and auth_header and auth_header.lower().startswith("bearer "):
        token = auth_header.split(None, 1)[1].strip()

    if token:
        try:
            data = decode_token(token)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            ) from None
        sub = data.get("sub")
        if not sub:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        try:
            user_id = int(sub)
        except (TypeError, ValueError):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        user = db.get(User, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive or missing")
        return user

    if settings.require_auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    demo = db.query(User).filter(User.email == settings.demo_user_email).one_or_none()
    if not demo:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Demo user not seeded — run server startup or register.",
        )
    return demo


CurrentUser = Annotated[User, Depends(get_current_user)]
