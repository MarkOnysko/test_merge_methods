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

# login returns {"access_token": ..., "refresh_token": ...}
curl -s -X POST localhost:8000/auth/login -d 'username=alice&password=s3cret-password'
TOKEN=<paste access_token>

# when the access token expires (15 min), trade the refresh token for a new pair
curl -X POST localhost:8000/auth/refresh -H 'Content-Type: application/json' \
  -d '{"refresh_token": "<refresh_token>"}'

# log out (revokes the refresh token)
curl -X POST localhost:8000/auth/logout -H 'Content-Type: application/json' \
  -d '{"refresh_token": "<refresh_token>"}'

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
    ├── auth.py      # POST /auth/register, /auth/login, /auth/refresh, /auth/logout, GET /auth/me
    ├── posts.py     # CRUD under /posts
    └── comments.py  # comments on posts
```

## How the auth flow works

1. `POST /auth/login` checks the password (Argon2) and returns two tokens:
   - an **access token**, a signed JWT whose `sub` is the user id, valid 15 minutes;
   - a **refresh token**, a random string valid 7 days. Only its SHA-256 hash is stored, so it can be revoked and a database leak doesn't expose usable tokens.
2. The client sends the access token as `Authorization: Bearer <token>`. Routes that declare `user: CurrentUser` verify its signature and expiry. Missing/invalid token → `401`. Changing someone else's post or comment → `403`.
3. When the access token expires, `POST /auth/refresh` exchanges the refresh token for a new pair. Refresh tokens are **rotated**: each works once. Presenting an already-used one revokes all of that user's refresh tokens, because it suggests theft.
4. `POST /auth/logout` revokes a refresh token. (An access token already issued stays valid until it expires.)

## Notes

- Passwords use Argon2id (`argon2-cffi`). Hashes are upgraded automatically at login if the parameters get stronger. Accounts created with the previous PBKDF2 version can no longer log in; re-register them or reset the database.
- The schema changed (users, `posts.author_id`, comments, `refresh_tokens`). If you have an old `blog.db`, delete it so it is recreated.
