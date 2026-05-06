from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

BCRYPT_MAX_PASSWORD_BYTES = 72


def safe_password(value: str) -> str:
    """Return a bcrypt-safe password (<= 72 UTF-8 bytes).

    Render production safety: bcrypt hard-limits to 72 bytes and passlib/bcrypt raises
    ValueError when exceeded. This helper truncates on UTF-8 boundaries.
    """
    if not value:
        return ""
    data = value.encode("utf-8")
    if len(data) <= BCRYPT_MAX_PASSWORD_BYTES:
        return value

    cut = data[:BCRYPT_MAX_PASSWORD_BYTES]
    while cut:
        try:
            return cut.decode("utf-8")
        except UnicodeDecodeError:
            cut = cut[:-1]
    return ""


def verify_password(plain: str, hashed: str) -> bool:
    raw_len = len((plain or "").encode("utf-8"))
    safe = safe_password(plain)
    safe_len = len(safe.encode("utf-8"))
    print("BCRYPT VERIFY INPUT LEN:", raw_len, "SAFE LEN:", safe_len)
    if raw_len > BCRYPT_MAX_PASSWORD_BYTES:
        print("BCRYPT WARNING: verify input exceeded 72 bytes; truncating safely.")
    try:
        return pwd_context.verify(safe, hashed)
    except ValueError as e:
        print("BCRYPT VERIFY ERROR:", repr(e))
        return False


def safe_hash(pwd: str) -> str:
    raw_len = len((pwd or "").encode("utf-8"))
    safe = safe_password(pwd)
    safe_len = len(safe.encode("utf-8"))
    print("BCRYPT HASH INPUT LEN:", raw_len, "SAFE LEN:", safe_len)
    if raw_len > BCRYPT_MAX_PASSWORD_BYTES:
        print("BCRYPT WARNING: hash input exceeded 72 bytes; truncating safely.")
    return pwd_context.hash(safe)


def get_password_hash(password: str) -> str:
    return safe_hash(password)


def create_access_token(*, subject: str, extra: dict[str, Any] | None = None) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload: dict[str, Any] = {"sub": subject, "exp": expire}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    settings = get_settings()
    try:
        return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    except JWTError as e:
        raise ValueError("Invalid token") from e
