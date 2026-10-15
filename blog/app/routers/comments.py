"""Comments on posts. Reading is public; adding requires login, and only a
comment's author may edit or delete it."""
from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.dependencies import DB, CurrentUser, Paging
from app.models import Comment, User
from app.routers.posts import get_post_or_404
from app.schemas import CommentIn, CommentOut, Page

router = APIRouter(tags=["comments"])


def get_comment_or_404(db, comment_id: int) -> Comment:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=404, detail="Comment not found")
    return comment


def require_author(comment: Comment, user: User) -> None:
    if comment.author_id != user.id:
        raise HTTPException(status_code=403, detail="You can only change your own comments")


@router.post("/posts/{post_id}/comments", response_model=CommentOut, status_code=201)
def add_comment(post_id: int, data: CommentIn, db: DB, user: CurrentUser):
    get_post_or_404(db, post_id)  # 404 if the post doesn't exist
    comment = Comment(post_id=post_id, author_id=user.id, body=data.body)
    db.add(comment)
    db.commit()
    return comment


@router.get("/posts/{post_id}/comments", response_model=Page[CommentOut])
def list_comments(post_id: int, db: DB, paging: Paging):
    get_post_or_404(db, post_id)
    query = select(Comment).where(Comment.post_id == post_id)
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    comments = db.scalars(
        query.order_by(Comment.id).limit(paging.limit).offset(paging.offset)
    ).all()
    return {"items": comments, "total": total, "limit": paging.limit, "offset": paging.offset}


@router.put("/comments/{comment_id}", response_model=CommentOut)
def update_comment(comment_id: int, data: CommentIn, db: DB, user: CurrentUser):
    comment = get_comment_or_404(db, comment_id)
    require_author(comment, user)
    comment.body = data.body
    db.commit()
    return comment


@router.delete("/comments/{comment_id}", status_code=204)
def delete_comment(comment_id: int, db: DB, user: CurrentUser):
    comment = get_comment_or_404(db, comment_id)
    require_author(comment, user)
    db.delete(comment)
    db.commit()
