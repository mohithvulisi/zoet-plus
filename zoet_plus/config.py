from __future__ import annotations

import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv


load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOCAL_DATA_DIR = PROJECT_ROOT / "data"


def get_setting(name: str, default: str = "") -> str:
    """Read Streamlit secrets first, then environment variables."""
    value = ""
    try:
        value = str(st.secrets.get(name, "") or "")
    except Exception:
        value = ""

    if value:
        return value

    return str(os.getenv(name, default) or default)


def get_bool_setting(name: str, default: bool = False) -> bool:
    raw = get_setting(name, str(default)).strip().lower()
    return raw in {"1", "true", "yes", "y", "on"}


def normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg2://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg2://" + url.removeprefix("postgresql://")
    return url


def get_database_url() -> tuple[str, bool]:
    configured = get_setting("DATABASE_URL", "").strip()
    if configured:
        return normalize_database_url(configured), False

    allow_sqlite = get_bool_setting("ZOET_ALLOW_SQLITE_FALLBACK", True)
    if not allow_sqlite:
        raise RuntimeError("DATABASE_URL is required when SQLite fallback is disabled.")

    LOCAL_DATA_DIR.mkdir(exist_ok=True)
    return f"sqlite:///{LOCAL_DATA_DIR / 'zoet_local.db'}", True


def get_app_base_url() -> str:
    return get_setting("APP_BASE_URL", "http://localhost:8501").rstrip("/")
