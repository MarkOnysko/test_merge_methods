"""Blog post CRUD. Reading is public; writing requires a logged-in user,
and only a post's author may edit or delete it."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from app.dependencies import DB, CurrentUser
from app.models import Post, User
from app.schemas import PostIn, PostOut

router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_or_404(db, post_id: int) -> Post:
    post = db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


def _require_author(post: Post, user: User) -> None:
    if post.author_id != user.id:
        raise HTTPException(status_code=403, detail="You can only change your own posts")


@router.post("", response_model=PostOut, status_code=201)
def create_post(data: PostIn, db: DB, user: CurrentUser):
    post = Post(title=data.title, body=data.body, author_id=user.id)
    db.add(post)
    db.commit()
    return post


@router.get("", response_model=list[PostOut])
def list_posts(db: DB):
    return db.scalars(select(Post).order_by(Post.id.desc())).all()


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: DB):
    return get_post_or_404(db, post_id)


@router.put("/{post_id}", response_model=PostOut)
def update_post(post_id: int, data: PostIn, db: DB, user: CurrentUser):
    post = get_post_or_404(db, post_id)
    _require_author(post, user)
    post.title, post.body = data.title, data.body
    db.commit()
    return post


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, db: DB, user: CurrentUser):
    post = get_post_or_404(db, post_id)
    _require_author(post, user)
    db.delete(post)  # comments go with it (cascade)
    db.commit()
