from __future__ import annotations

import re
import uuid
from dataclasses import dataclass

import bcrypt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import MeetingParticipant, User


USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9._-]{2,39}$")


@dataclass(frozen=True)
class AuthResult:
    ok: bool
    message: str
    user: User | None = None


def normalize_username(username: str) -> str:
    return str(username or "").strip().lower()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def validate_signup(username: str, display_name: str, password: str) -> str | None:
    if not USERNAME_PATTERN.match(username):
        return "Use 3-40 characters: lowercase letters, numbers, dot, dash, or underscore."
    if len(str(display_name or "").strip()) < 2:
        return "Display name must be at least 2 characters."
    if len(password) < 8:
        return "Password must be at least 8 characters."
    return None


def validate_display_name(display_name: str) -> str | None:
    display_name = str(display_name or "").strip()
    if len(display_name) < 2:
        return "Display name must be at least 2 characters."
    if len(display_name) > 80:
        return "Display name must be 80 characters or fewer."
    return None


def create_user(session: Session, username: str, display_name: str, password: str) -> AuthResult:
    username = normalize_username(username)
    display_name = str(display_name or "").strip()
    error = validate_signup(username, display_name, password)
    if error:
        return AuthResult(False, error)

    user = User(
        id=str(uuid.uuid4()),
        username=username,
        display_name=display_name,
        password_hash=hash_password(password),
    )
    session.add(user)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        return AuthResult(False, "That username is already taken.")

    return AuthResult(True, "Account created.", user)


def authenticate_user(session: Session, username: str, password: str) -> AuthResult:
    username = normalize_username(username)
    if not username or not password:
        return AuthResult(False, "Username and password are required.")

    user = session.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        return AuthResult(False, "Invalid username or password.")

    return AuthResult(True, "Logged in.", user)


def get_user_by_id(session: Session, user_id: str | None) -> User | None:
    if not user_id:
        return None
    return session.get(User, user_id)


def get_user_by_username(session: Session, username: str | None) -> User | None:
    username = normalize_username(username or "")
    if not username:
        return None
    return session.scalar(select(User).where(User.username == username))


def update_display_name(session: Session, user_id: str, display_name: str) -> AuthResult:
    display_name = str(display_name or "").strip()
    error = validate_display_name(display_name)
    if error:
        return AuthResult(False, error)

    user = session.get(User, user_id)
    if not user:
        return AuthResult(False, "User not found.")

    user.display_name = display_name
    for participant in session.query(MeetingParticipant).filter(MeetingParticipant.user_id == user_id).all():
        participant.display_name = display_name
    session.flush()
    return AuthResult(True, "Display name updated.", user)
