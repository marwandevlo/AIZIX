from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.database import get_db
from app.db.models import Portfolio, User
from app.deps import CurrentUser

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterBody(BaseModel):
    email: EmailStr
    password: str = Field(max_length=128)


class LoginBody(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthUserOut(BaseModel):
    email: str


class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: AuthUserOut


class UserOut(BaseModel):
    id: int
    email: str
    balance_usd: float
    prefs: dict[str, object]

    model_config = {"from_attributes": True}


@router.post("/register", response_model=AuthTokenResponse)
def register(body: RegisterBody, db: Session = Depends(get_db)) -> AuthTokenResponse:
    email = body.email.lower().strip()
    print("SIGNUP REQUEST:", email)
    try:
        if len(body.password or "") < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must contain at least 8 characters",
            )
        if db.query(User).filter(User.email == email).first():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
        user = User(
            email=email,
            hashed_password=get_password_hash(body.password),
            balance_usd=12_540.25,
        )
        db.add(user)
        db.flush()
        db.add(
            Portfolio(
                user_id=user.id,
                balance_usd=user.balance_usd,
                portfolio_value_usd=user.balance_usd,
                peak_equity_usd=user.balance_usd,
            )
        )
        db.commit()
        db.refresh(user)
        token = create_access_token(subject=str(user.id))
        return AuthTokenResponse(access_token=token, user=AuthUserOut(email=user.email))
    except HTTPException:
        raise
    except Exception as e:
        print("SIGNUP ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/login", response_model=AuthTokenResponse)
def login(body: LoginBody, db: Session = Depends(get_db)) -> AuthTokenResponse:
    email = body.email.lower().strip()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not verify_password(body.password, user.hashed_password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        token = create_access_token(subject=str(user.id))
        return AuthTokenResponse(access_token=token, user=AuthUserOut(email=user.email))
    except HTTPException:
        raise
    except Exception as e:
        print("LOGIN ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser) -> UserOut:
    try:
        prefs = json.loads(user.prefs_json or "{}")
    except json.JSONDecodeError:
        prefs = {}
    return UserOut(id=user.id, email=user.email, balance_usd=user.balance_usd, prefs=prefs)
