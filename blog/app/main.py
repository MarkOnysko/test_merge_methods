"""App entry point: creates the FastAPI app and plugs in the routers.

Tables are created by Alembic migrations, not by the app. Before the first run
(and after pulling model changes), from the blog/ directory:

    alembic upgrade head
    uvicorn app.main:app --reload
"""
from fastapi import FastAPI

from app.routers import auth, comments, posts

app = FastAPI(title="Minimal Blog")
app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(comments.router)
