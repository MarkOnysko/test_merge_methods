"""A minimal blog-post API built with FastAPI.

Run it:    uvicorn main:app --reload
Explore:   http://127.0.0.1:8000/docs
"""
import sqlite3
from contextlib import closing, asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = "blog.db"


# --- Step 1: database -------------------------------------------------------
def get_db() -> sqlite3.Connection:
    """Open a connection whose rows can be read like dicts."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with closing(get_db()) as db:
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                body       TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        db.commit()


# --- Step 2: schemas (request/response shapes) ------------------------------
class PostIn(BaseModel):
    """What a client sends when creating or updating a post."""
    title: str
    body: str


class PostOut(PostIn):
    """What we send back: the same fields plus server-generated ones."""
    id: int
    created_at: str


# --- Step 3: the app --------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create the table on startup
    yield


app = FastAPI(title="Minimal Blog", lifespan=lifespan)


# --- Step 4: routes (CRUD) --------------------------------------------------
@app.post("/posts", response_model=PostOut, status_code=201)
def create_post(post: PostIn):
    now = datetime.now(timezone.utc).isoformat()
    with closing(get_db()) as db:
        cur = db.execute(
            "INSERT INTO posts (title, body, created_at) VALUES (?, ?, ?)",
            (post.title, post.body, now),
        )
        db.commit()
        row = db.execute("SELECT * FROM posts WHERE id = ?", (cur.lastrowid,)).fetchone()
    return dict(row)


@app.get("/posts", response_model=list[PostOut])
def list_posts():
    with closing(get_db()) as db:
        rows = db.execute("SELECT * FROM posts ORDER BY id DESC").fetchall()
    return [dict(r) for r in rows]


@app.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: int):
    with closing(get_db()) as db:
        row = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return dict(row)


@app.put("/posts/{post_id}", response_model=PostOut)
def update_post(post_id: int, post: PostIn):
    with closing(get_db()) as db:
        cur = db.execute(
            "UPDATE posts SET title = ?, body = ? WHERE id = ?",
            (post.title, post.body, post_id),
        )
        db.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Post not found")
        row = db.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    return dict(row)


@app.delete("/posts/{post_id}", status_code=204)
def delete_post(post_id: int):
    with closing(get_db()) as db:
        cur = db.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        db.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Post not found")
