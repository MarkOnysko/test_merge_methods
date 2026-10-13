"""Pydantic models: the shapes of requests and responses."""
from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)


class UserOut(BaseModel):
    id: int
    username: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PostIn(BaseModel):
    """What a client sends when creating or updating a post."""
    title: str
    body: str


class PostOut(PostIn):
    """What we send back: the same fields plus server-generated ones."""
    id: int
    created_at: str
    author_id: int


class CommentIn(BaseModel):
    body: str = Field(min_length=1)


class CommentOut(CommentIn):
    id: int
    post_id: int
    author_id: int
    created_at: str
