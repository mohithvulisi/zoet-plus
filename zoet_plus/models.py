from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True, index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    hosted_meetings: Mapped[list["Meeting"]] = relationship(back_populates="host")
    participations: Mapped[list["MeetingParticipant"]] = relationship(back_populates="user")


class Meeting(Base):
    __tablename__ = "meetings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    title: Mapped[str] = mapped_column(String(140), nullable=False)
    join_code: Mapped[str] = mapped_column(String(16), unique=True, index=True, nullable=False)
    host_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="scheduled", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    host: Mapped[User] = relationship(back_populates="hosted_meetings")
    participants: Mapped[list["MeetingParticipant"]] = relationship(back_populates="meeting", cascade="all, delete-orphan")


class MeetingParticipant(Base):
    __tablename__ = "meeting_participants"
    __table_args__ = (UniqueConstraint("meeting_id", "user_id", name="uq_meeting_participant_user"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    role: Mapped[str] = mapped_column(String(24), default="participant", nullable=False)
    status: Mapped[str] = mapped_column(String(24), default="joined", nullable=False)
    display_name: Mapped[str] = mapped_column(String(80), nullable=False)
    joined_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)

    meeting: Mapped[Meeting] = relationship(back_populates="participants")
    user: Mapped[User] = relationship(back_populates="participations")


class MeetingHistory(Base):
    __tablename__ = "meeting_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=False)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    action: Mapped[str] = mapped_column(String(60), nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class ModerationEvent(Base):
    __tablename__ = "moderation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meeting_id: Mapped[str | None] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=True)
    user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), index=True, nullable=True)
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    content_preview: Mapped[str | None] = mapped_column(String(180), nullable=True)
    flagged: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    action: Mapped[str] = mapped_column(String(40), default="allow", nullable=False)
    model: Mapped[str | None] = mapped_column(String(80), nullable=True)
    categories: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    category_scores: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class FocusEvent(Base):
    __tablename__ = "focus_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    face_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    meeting_id: Mapped[str] = mapped_column(ForeignKey("meetings.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, nullable=False)
