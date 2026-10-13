"""Comments on posts. Reading is public; adding requires login, and only a
comment's author may edit or delete it."""
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.dependencies import DB, CurrentUser
from app.routers.posts import get_post_or_404
from app.schemas import CommentIn, CommentOut

router = APIRouter(tags=["comments"])


def get_comment_or_404(db, comment_id: int):
    row = db.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return row


def require_author(comment, user) -> None:
    if comment["author_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="You can only change your own comments")


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(post_id: int, comment: CommentIn, db: DB, user: CurrentUser):
    get_post_or_404(db, post_id)  # 404 if the post doesn't exist
    now = datetime.now(timezone.utc).isoformat()
    cur = db.execute(
        "INSERT INTO comments (post_id, author_id, body, created_at) VALUES (?, ?, ?, ?)",
        (post_id, user["id"], comment.body, now),
    )
    db.commit()
    return dict(get_comment_or_404(db, cur.lastrowid))


@router.get("/posts/{post_id}/comments", response_model=list[CommentOut])
def list_comments(post_id: int, db: DB):
    get_post_or_404(db, post_id)
    rows = db.execute(
        "SELECT * FROM comments WHERE post_id = ? ORDER BY id", (post_id,)
    ).fetchall()
    return [dict(r) for r in rows]


@router.put("/comments/{comment_id}", response_model=CommentOut)
def update_comment(comment_id: int, data: CommentIn, db: DB, user: CurrentUser):
    require_author(get_comment_or_404(db, comment_id), user)
    db.execute("UPDATE comments SET body = ? WHERE id = ?", (data.body, comment_id))
    db.commit()
    return dict(get_comment_or_404(db, comment_id))


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: DB, user: CurrentUser):
    require_author(get_comment_or_404(db, comment_id), user)
    db.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    db.commit()
