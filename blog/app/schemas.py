"""Pydantic models: the shapes of requests and responses."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)  # build from ORM objects

    id: int
    username: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class PostIn(BaseModel):
    """What a client sends when creating or updating a post."""
    title: str
    body: str


class PostOut(PostIn):
    """What we send back: the same fields plus server-generated ones."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    author_id: int


class CommentIn(BaseModel):
    body: str = Field(min_length=1)


class CommentOut(CommentIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    author_id: int
    created_at: datetime
