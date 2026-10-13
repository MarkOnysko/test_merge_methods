# Minimal Blog (FastAPI)

A tiny blog-post API: create, read, update and delete posts, stored in SQLite.

## Setup

```bash
cd blog
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Open http://127.0.0.1:8000/docs for interactive API docs.

## Try it

```bash
# create
curl -X POST localhost:8000/posts -H 'Content-Type: application/json' \
  -d '{"title": "Hello", "body": "My first post"}'

# list / read
curl localhost:8000/posts
curl localhost:8000/posts/1

# update
curl -X PUT localhost:8000/posts/1 -H 'Content-Type: application/json' \
  -d '{"title": "Hello again", "body": "Edited"}'

# delete
curl -X DELETE localhost:8000/posts/1
```

## How `main.py` is organised

1. **Database** – `sqlite3` with one `posts` table, created on startup.
2. **Schemas** – Pydantic models (`PostIn`, `PostOut`) validate requests and shape responses.
3. **App** – a `FastAPI` instance; the `lifespan` hook initialises the DB.
4. **Routes** – five endpoints covering CRUD under `/posts`.

## Next steps

Add authentication, comments, pagination, or swap `sqlite3` for SQLAlchemy/SQLModel.
