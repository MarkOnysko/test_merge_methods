"""Password hashing and JWT creation/verification."""
import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt

from app import config

_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """PBKDF2-HMAC-SHA256 with a random salt, stored as 'salt$hash' (hex)."""
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _ITERATIONS)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$")
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), bytes.fromhex(salt_hex), _ITERATIONS
    )
    return hmac.compare_digest(digest.hex(), digest_hex)


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
