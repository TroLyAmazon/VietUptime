import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")

    # SQLite in instance/
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///status.sqlite")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    TIMEZONE = os.getenv("TIMEZONE", "Asia/Bangkok")

    # Admin (single owner account)
    OWNER_USERNAME = os.getenv("OWNER_USERNAME", "owner")
    OWNER_PASSWORD_HASH = os.getenv("OWNER_PASSWORD_HASH", "")

    # Optional: first-run seed
    SEED_TARGET_NAME = os.getenv("SEED_TARGET_NAME", "")
    SEED_TARGET_BASE_URL = os.getenv("SEED_TARGET_BASE_URL", "")
    SEED_TARGET_STATS_PATH = os.getenv("SEED_TARGET_STATS_PATH", "/api/stats")

    # Update checker
    UPDATE_URL = os.getenv("UPDATE_URL", "")

    # CSRF
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None

    # Session cookie (DEV)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False
