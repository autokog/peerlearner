import os
import re
from datetime import timedelta


def _int_env(name: str, default: int) -> int:
    """Read an integer env var, stripping any stray non-digit characters."""
    raw = os.environ.get(name, "")
    digits = re.sub(r"\D", "", raw)
    return int(digits) if digits else default


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///grouper.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    SESSION_COOKIE_SAMESITE = "None"
    SESSION_COOKIE_SECURE = True
    MAX_GROUPS = _int_env("MAX_GROUPS", 5)
    MAX_MEMBERS = _int_env("MAX_MEMBERS", 10)
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "")
