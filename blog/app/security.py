"""Password hashing (Argon2) and token helpers (JWT access, opaque refresh)."""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerifyMismatchError

from app import config

_hasher = PasswordHasher()  # Argon2id with the library's recommended parameters
# Verified against when a username doesn't exist, so login takes about the
# same time either way and can't be used to discover valid usernames.
_DUMMY_HASH = _hasher.hash("dummy-password")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, stored: str | None) -> bool:
    try:
        return _hasher.verify(stored or _DUMMY_HASH, password) and stored is not None
    except (VerifyMismatchError, InvalidHashError):
        return False


def password_needs_rehash(stored: str) -> bool:
    """True if the hash was made with weaker parameters than the current ones."""
    return _hasher.check_needs_rehash(stored)


# --- access tokens: short-lived, signed JWTs ---------------------------------
def create_access_token(user_id: int) -> str:
    """Sign a token whose subject ('sub') is the user id and which expires soon."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, config.SECRET_KEY, algorithm=config.ALGORITHM)


def decode_access_token(token: str) -> int:
    """Return the user id from a valid token; raises jwt.InvalidTokenError otherwise
    (bad signature, expired, malformed...)."""
    payload = jwt.decode(token, config.SECRET_KEY, algorithms=[config.ALGORITHM])
    return int(payload["sub"])


# --- refresh tokens: long-lived, random, stored hashed so they can be revoked --
def new_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    # A fast hash is fine here: the token is 256 bits of randomness, not a password.
    return hashlib.sha256(token.encode()).hexdigest()


def refresh_token_expiry() -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=config.REFRESH_TOKEN_EXPIRE_DAYS)
