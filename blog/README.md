# Minimal Blog (FastAPI + JWT)

A tiny blog-post API with user accounts. Anyone can read posts; logged-in users can create posts and edit/delete their own. Data lives in SQLite.

## Setup

```bash
cd blog
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY=$(openssl rand -hex 32)   # optional locally, required in production
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs. Use the **Authorize** button there to log in and try protected routes.

## Try it

```bash
# 1. register, then log in to get a token
curl -X POST localhost:8000/auth/register -H 'Content-Type: application/json' \
  -d '{"username": "alice", "password": "s3cret-password"}'

TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -d 'username=alice&password=s3cret-password' | python -c 'import sys,json; print(json.load(sys.stdin)["access_token"])')

# 2. create a post (needs the token)
curl -X POST localhost:8000/posts -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"title": "Hello", "body": "My first post"}'

# 3. read posts (public)
curl localhost:8000/posts

# 4. edit your own post
curl -X PUT localhost:8000/posts/1 -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"title": "Hello again", "body": "Edited"}'

# 5. comment on a post (needs the token), then list / edit / delete
curl -X POST localhost:8000/posts/1/comments -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"body": "Nice post!"}'
curl localhost:8000/posts/1/comments
curl -X PUT localhost:8000/comments/1 -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' -d '{"body": "Edited"}'
curl -X DELETE localhost:8000/comments/1 -H "Authorization: Bearer $TOKEN"

# 6. delete the post (also removes its comments)
curl -X DELETE localhost:8000/posts/1 -H "Authorization: Bearer $TOKEN"
```

## Project layout

```
app/
├── main.py          # creates the app, includes routers, inits DB on startup
├── config.py        # settings (SECRET_KEY, token lifetime, DB path)
├── database.py      # SQLite connection dependency + table creation
├── schemas.py       # Pydantic request/response models
├── security.py      # password hashing, JWT create/decode
├── dependencies.py  # get_current_user: turns a bearer token into a user
└── routers/
    ├── auth.py      # POST /auth/register, POST /auth/login, GET /auth/me
    ├── posts.py     # CRUD under /posts
    └── comments.py  # comments on posts
```

## How the auth flow works

1. `POST /auth/login` checks the password and returns a signed JWT whose `sub` is the user id (expires after 30 minutes).
2. The client sends it back as `Authorization: Bearer <token>`.
3. Routes that declare `user: CurrentUser` run `get_current_user`, which verifies the signature and expiry and loads the user. Missing/invalid token → `401`. Editing or deleting someone else's post or comment → `403`.

## Notes

- Passwords are hashed with PBKDF2 from the standard library to keep dependencies small; for a real app consider `argon2` or `bcrypt`.
- The schema changed (users, `posts.author_id`, comments). If you have an old `blog.db`, delete it so it is recreated.
