import os
from datetime import timedelta


class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///grouper.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret")
    PERMANENT_SESSION_LIFETIME = timedelta(days=1)
    MAX_GROUPS = int(os.environ.get("MAX_GROUPS", 5))
    MAX_MEMBERS = int(os.environ.get("MAX_MEMBERS", 10))
