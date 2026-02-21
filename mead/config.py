"""Mead CMF — configuration."""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{os.environ.get('DB_NAME', 'blog.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = "static/uploads"
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

    # Active theme (folder name inside mead/themes/)
    ACTIVE_THEME = os.environ.get("ACTIVE_THEME", "default")
