"""Register, log in, refresh, log out."""
import sqlite3
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import DB, CurrentUser
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


def _issue_tokens(db: sqlite3.Connection, user_id: int) -> Token:
    """Create an access token plus a new refresh token (only its hash is stored)."""
    refresh = new_refresh_token()
    db.execute(
        "INSERT INTO refresh_tokens (user_id, token_hash, expires_at) VALUES (?, ?, ?)",
        (user_id, hash_refresh_token(refresh), refresh_token_expiry().isoformat()),
    )
    db.commit()
    return Token(access_token=create_access_token(user_id), refresh_token=refresh)


@router.post("/register", response_model=UserOut, status_code=201)
def register(user: UserCreate, db: DB):
    try:
        cur = db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (user.username, hash_password(user.password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already taken")
    return {"id": cur.lastrowid, "username": user.username}


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DB):
    """Exchange username + password (sent as form data) for an access + refresh token."""
    row = db.execute("SELECT * FROM users WHERE username = ?", (form.username,)).fetchone()
    stored = row["password_hash"] if row else None
    if not verify_password(form.password, stored):
        raise _unauthorized("Incorrect username or password")
    if password_needs_rehash(stored):  # upgrade old hashes transparently
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(form.password), row["id"]),
        )
    return _issue_tokens(db, row["id"])


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: DB):
    """Swap a refresh token for a fresh pair. Each refresh token works once
    (rotation); presenting an already-used one revokes the user's whole session set,
    since it suggests the token was stolen."""
    row = db.execute(
        "SELECT * FROM refresh_tokens WHERE token_hash = ?",
        (hash_refresh_token(data.refresh_token),),
    ).fetchone()
    if row is None:
        raise _unauthorized("Invalid refresh token")
    if row["revoked"]:
        db.execute("UPDATE refresh_tokens SET revoked = 1 WHERE user_id = ?", (row["user_id"],))
        db.commit()
        raise _unauthorized("Refresh token already used")
    if datetime.fromisoformat(row["expires_at"]) < datetime.now(timezone.utc):
        raise _unauthorized("Refresh token expired")
    db.execute("UPDATE refresh_tokens SET revoked = 1 WHERE id = ?", (row["id"],))
    return _issue_tokens(db, row["user_id"])


@router.post("/logout", status_code=204)
def logout(data: RefreshRequest, db: DB):
    """Revoke a refresh token. Idempotent: unknown tokens are ignored."""
    db.execute(
        "UPDATE refresh_tokens SET revoked = 1 WHERE token_hash = ?",
        (hash_refresh_token(data.refresh_token),),
    )
    db.commit()


@router.get("/me", response_model=UserOut)
def me(user: CurrentUser):
    return dict(user)
