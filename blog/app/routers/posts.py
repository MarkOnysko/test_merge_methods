"""Blog post CRUD. Reading is public; writing requires a logged-in user,
and only a post's author may edit or delete it."""
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.dependencies import DB, CurrentUser, Paging
from app.models import Post, Tag, User
from app.schemas import Page, PostIn, PostOut

router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_or_404(db, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


def _require_author(post: Post, user: User) -> None:
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="You can only change your own posts")


def _tags_for(db: Session, names: list[str]) -> list[Tag]:
    """Reuse existing tags, create the missing ones."""
    if not names:
        return []
    existing = {t.name: t for t in db.scalars(select(Tag).where(Tag.name.in_(names)))}
    return [existing.get(n) or Tag(name=n) for n in names]


def _escape_like(text: str) -> str:
    """Make % and _ in user input match literally in a LIKE pattern."""
    return text.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


@router.post("", response_model=PostOut, status_code=201)
def create_post(data: PostIn, db: DB, user: CurrentUser):
    post = Post(title=data.title, body=data.body, author_id=user.id, tags=_tags_for(db, data.tags))
    db.add(post)
    db.commit()
    db.refresh(post)  # reload so tags come back in the same (sorted) order as GET
    return post


@router.get("", response_model=Page[PostOut])
def list_posts(
    db: DB,
    paging: Paging,
    q: Annotated[str | None, Query(min_length=1, description="Search title and body")] = None,
    tag: Annotated[str | None, Query(description="Only posts with this tag")] = None,
):
    query = select(Post)
    if q:
        pattern = f"%{_escape_like(q)}%"
        query = query.where(
            or_(Post.title.ilike(pattern, escape="\\"), Post.body.ilike(pattern, escape="\\"))
        )
    if tag:
        query = query.where(Post.tags.any(Tag.name == tag.strip().lower()))

    total = db.scalar(select(func.count()).select_from(query.subquery()))
    posts = db.scalars(
        query.options(selectinload(Post.tags))  # one extra query instead of one per post
        .order_by(Post.id.desc())
        .limit(paging.limit)
        .offset(paging.offset)
    ).all()
    return {"items": posts, "total": total, "limit": paging.limit, "offset": paging.offset}


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: DB):
    return get_post_or_404(db, post_id)


@router.put("/{post_id}", response_model=PostOut)
def update_post(post_id: int, data: PostIn, db: DB, user: CurrentUser):
    post = get_post_or_404(db, post_id)
    _require_author(post, user)
    post.title, post.body = data.title, data.body
    post.tags = _tags_for(db, data.tags)
    db.commit()
    db.refresh(post)
    return post


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, db: DB, user: CurrentUser):
    post = get_post_or_404(db, post_id)
    _require_author(post, user)
    db.delete(post)  # comments go with it (cascade)
    db.commit()
