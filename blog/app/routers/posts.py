"""Blog post CRUD. Reading is public; writing requires a logged-in user,
and only a post's author may edit or delete it."""
from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

from app.dependencies import DB, CurrentUser
from app.schemas import PostIn, PostOut

router = APIRouter(prefix="/posts", tags=["posts"])


def get_post_or_404(db, post_id: int):
    row = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return row


def _require_author(post, user) -> None:
    if post["author_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only change your own posts")


@router.post("", response_model=PostOut, status_code=201)
def create_post(post: PostIn, db: DB, user: CurrentUser):
    now = datetime.now(timezone.utc).isoformat()
    cur = db.execute(
        "INSERT INTO posts (title, body, created_at, author_id) VALUES (?, ?, ?, ?)",
        (post.title, post.body, now, user["id"]),
    )
    db.commit()
    return dict(get_post_or_404(db, cur.lastrowid))


@router.get("", response_model=list[PostOut])
def list_posts(db: DB):
    rows = db.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


@router.get("/{post_id}", response_model=PostOut)
def get_post(post_id: int, db: DB):
    return dict(get_post_or_404(db, post_id))


@router.put("/{post_id}", response_model=PostOut)
def update_post(post_id: int, post: PostIn, db: DB, user: CurrentUser):
    _require_author(get_post_or_404(db, post_id), user)
    db.execute(
        "UPDATE posts SET title = ?, body = ? WHERE id = ?",
        (post.title, post.body, post_id),
    )
    db.commit()
    return dict(get_post_or_404(db, post_id))


@router.delete("/{post_id}", status_code=204)
def delete_post(post_id: int, db: DB, user: CurrentUser):
    _require_author(get_post_or_404(db, post_id), user)
    db.execute("DELETE FROM comments WHERE post_id = ?", (post_id,))  # no orphans
    db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    db.commit()
