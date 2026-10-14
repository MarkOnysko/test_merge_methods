"""Settings, read from environment variables with development defaults."""
import os

# Any SQLAlchemy URL works, e.g. postgresql+psycopg://user:pass@host/dbname
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///blog.db")

# Used to sign JWTs. Always set a real, random value in production:
#   export SECRET_KEY=$(openssl rand -hex 32)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # short-lived: refresh tokens do the long-term work
REFRESH_TOKEN_EXPIRE_DAYS = 7
