"""Reusable dependencies, e.g. 'who is making this request?'"""
import sqlite3
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.database import get_db
from app.security import decode_access_token

# Tells FastAPI to read 'Authorization: Bearer <token>' and powers the
# "Authorize" button in /docs. tokenUrl is where clients get a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DB = Annotated[sqlite3.Connection, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> sqlite3.Row:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized
    user = db.execute("SELECT id, username FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[sqlite3.Row, Depends(get_current_user)]
