"""Pydantic models: the shapes of requests and responses."""
from datetime import datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_validator


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


T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """One page of results plus enough info to fetch the next one."""
    items: list[T]
    total: int  # matches across all pages
    limit: int
    offset: int


class PostIn(BaseModel):
    """What a client sends when creating or updating a post."""
    title: str
    body: str
    tags: list[str] = Field(default_factory=list, max_length=10)

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, tags: list[str]) -> list[str]:
        """Trim, lowercase, drop duplicates (keeping order), enforce 1-30 chars."""
        cleaned = list(dict.fromkeys(t.strip().lower() for t in tags))
        if any(not 1 <= len(t) <= 30 for t in cleaned):
            raise ValueError("each tag must be 1-30 characters")
        return cleaned


class PostOut(PostIn):
    """What we send back: the same fields plus server-generated ones."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    author_id: int

    @field_validator("tags", mode="before")
    @classmethod
    def tag_names(cls, tags):
        """The ORM gives Tag objects; the API shows just their names."""
        return [getattr(t, "name", t) for t in tags]


class CommentIn(BaseModel):
    body: str = Field(min_length=1)


class CommentOut(CommentIn):
    model_config = ConfigDict(from_attributes=True)

    id: int
    post_id: int
    author_id: int
    created_at: datetime
