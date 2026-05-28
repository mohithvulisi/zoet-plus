from __future__ import annotations

from contextlib import contextmanager
from threading import Lock
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_database_url


class Base(DeclarativeBase):
    pass


_ENGINE = None
_SESSION_FACTORY = None
_LOCK = Lock()


def get_engine():
    global _ENGINE
    if _ENGINE is None:
        with _LOCK:
            if _ENGINE is None:
                database_url, is_sqlite = get_database_url()
                kwargs = {"pool_pre_ping": True}
                if is_sqlite:
                    kwargs["connect_args"] = {"check_same_thread": False}
                _ENGINE = create_engine(database_url, **kwargs)
    return _ENGINE


def get_session_factory():
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        with _LOCK:
            if _SESSION_FACTORY is None:
                _SESSION_FACTORY = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _SESSION_FACTORY


def init_db() -> None:
    from . import models  # noqa: F401

    Base.metadata.create_all(get_engine())


@contextmanager
def session_scope() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
