"""App entry point: creates the FastAPI app and plugs in the routers.

Run from the blog/ directory:  uvicorn app.main:app --reload
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers import auth, posts


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()  # create tables on startup
    yield


app = FastAPI(title="Minimal Blog", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(posts.router)
