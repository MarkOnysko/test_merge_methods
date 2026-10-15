"""Reusable dependencies, e.g. 'who is making this request?'"""
from typing import Annotated

from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.security import decode_access_token

# Tells FastAPI to read 'Authorization: Bearer <token>' and powers the
# "Authorize" button in /docs. tokenUrl is where clients get a token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

DB = Annotated[Session, Depends(get_db)]


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: DB) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        user_id = decode_access_token(token)
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise unauthorized
    user = db.get(User, user_id)
    if user is None:
        raise unauthorized
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


@dataclass
class Pagination:
    """?limit=20&offset=0 query parameters, validated and reusable."""
    limit: Annotated[int, Query(ge=1, le=100, description="Page size")] = 20
    offset: Annotated[int, Query(ge=0, description="How many items to skip")] = 0


Paging = Annotated[Pagination, Depends()]
