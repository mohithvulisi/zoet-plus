from __future__ import annotations

import uuid

from sqlalchemy import asc, select
from sqlalchemy.orm import Session

from .models import ChatMessage, User


def save_chat_message(session: Session, *, meeting_id: str, user_id: str, body: str) -> ChatMessage:
    message = ChatMessage(
        id=str(uuid.uuid4()),
        meeting_id=meeting_id,
        user_id=user_id,
        body=str(body or "").strip(),
        blocked=False,
    )
    session.add(message)
    session.flush()
    return message


def get_chat_messages(session: Session, meeting_id: str, limit: int = 50) -> list[dict]:
    rows = session.execute(
        select(ChatMessage, User)
        .join(User, User.id == ChatMessage.user_id)
        .where(ChatMessage.meeting_id == meeting_id, ChatMessage.blocked.is_(False))
        .order_by(asc(ChatMessage.created_at))
        .limit(limit)
    ).all()
    return [
        {
            "id": message.id,
            "body": message.body,
            "created_at": message.created_at,
            "display_name": user.display_name,
            "username": user.username,
        }
        for message, user in rows
    ]
