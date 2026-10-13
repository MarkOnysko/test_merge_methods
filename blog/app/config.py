"""Settings, read from environment variables with development defaults."""
import os

DB_PATH = os.getenv("DB_PATH", "blog.db")

# Used to sign JWTs. Always set a real, random value in production:
#   export SECRET_KEY=$(openssl rand -hex 32)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
