"""Register, log in, refresh, log out."""
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.dependencies import DB, CurrentUser
from app.models import RefreshToken, User
from app.schemas import RefreshRequest, Token, UserCreate, UserOut
from app.security import (
    create_access_token,
    hash_password,
    hash_refresh_token,
    new_refresh_token,
    password_needs_rehash,
    refresh_token_expiry,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def _issue_tokens(db: Session, user_id: int) -> Token:
    """Create an access token plus a new refresh token (only its hash is stored)."""
    refresh = new_refresh_token()
    db.add(RefreshToken(
        user_id=user_id,
        token_hash=hash_refresh_token(refresh),
        expires_at=refresh_token_expiry(),
    ))
    db.commit()
    return Token(access_token=create_access_token(user_id), refresh_token=refresh)


@router.post("/register", response_model=UserOut, status_code=201)
def register(data: UserCreate, db: DB):
    user = User(username=data.username, password_hash=hash_password(data.password))
    db.add(user)
    try:
        db.commit()
    except IntegrityError:  # the UNIQUE constraint on username was violated
        db.rollback()
        raise HTTPException(status_code=409, detail="Username already taken")
    return user


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    """Exchange username + password (sent as form data) for an access + refresh token."""
    user = db.scalar(select(User).where(User.username == form.username))
    stored = user.password_hash if user else None
    if not verify_password(form.password, stored):
        raise _unauthorized("Incorrect username or password")
    if password_needs_rehash(stored):  # upgrade old hashes transparently
        user.password_hash = hash_password(form.password)
    return _issue_tokens(db, user.id)


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: DB):
    """Swap a refresh token for a fresh pair. Each refresh token works once
    (rotation); presenting an already-used one revokes the user's whole session set,
    since it suggests the token was stolen."""
    token = db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(data.refresh_token))
    )
    if token is None:
        raise _unauthorized("Invalid refresh token")
    if token.revoked:
        db.execute(update(RefreshToken).where(RefreshToken.user_id == token.user_id).values(revoked=True))
        db.commit()
        raise _unauthorized("Refresh token already used")
    if token.expires_at < datetime.now(timezone.utc):
        raise _unauthorized("Refresh token expired")
    token.revoked = True
    return _issue_tokens(db, token.user_id)


@router.post("/logout", status_code=204)
def logout(data: RefreshRequest, db: DB):
    """Revoke a refresh token. Idempotent: unknown tokens are ignored."""
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.token_hash == hash_refresh_token(data.refresh_token))
        .values(revoked=True)
    )
    db.commit()


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return user
