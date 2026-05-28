from __future__ import annotations

import secrets
import string
import uuid
from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from .config import get_app_base_url
from .models import Meeting, MeetingHistory, MeetingParticipant, User


JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


@dataclass(frozen=True)
class ServiceResult:
    ok: bool
    message: str
    payload: dict | None = None


def utcnow() -> datetime:
    return datetime.utcnow()


def normalize_join_code(code: str) -> str:
    return "".join(ch for ch in str(code or "").upper() if ch in string.ascii_uppercase + string.digits)


def build_join_link(join_code: str) -> str:
    return f"{get_app_base_url()}/?join={join_code}"


def generate_join_code(session: Session, length: int = 7) -> str:
    for _ in range(40):
        code = "".join(secrets.choice(JOIN_CODE_ALPHABET) for _ in range(length))
        exists = session.scalar(select(Meeting.id).where(Meeting.join_code == code))
        if not exists:
            return code
    raise RuntimeError("Could not generate a unique meeting code.")


def add_history(session: Session, meeting_id: str, user_id: str | None, action: str, details: dict | None = None) -> None:
    session.add(
        MeetingHistory(
            id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            user_id=user_id,
            action=action,
            details=details or {},
        )
    )


def meeting_to_dict(meeting: Meeting, participant_count: int = 0) -> dict:
    return {
        "id": meeting.id,
        "title": meeting.title,
        "join_code": meeting.join_code,
        "join_link": build_join_link(meeting.join_code),
        "host_user_id": meeting.host_user_id,
        "host_username": meeting.host.username if meeting.host else "",
        "host_display_name": meeting.host.display_name if meeting.host else "",
        "status": meeting.status,
        "participant_count": participant_count,
        "created_at": meeting.created_at,
        "started_at": meeting.started_at,
        "ended_at": meeting.ended_at,
    }


def create_meeting(session: Session, *, title: str, host_user_id: str) -> ServiceResult:
    title = str(title or "").strip()
    if len(title) < 3:
        return ServiceResult(False, "Meeting title must be at least 3 characters.")
    if len(title) > 140:
        return ServiceResult(False, "Meeting title must be 140 characters or fewer.")

    host = session.get(User, host_user_id)
    if not host:
        return ServiceResult(False, "Host account was not found. Please log in again.")

    meeting = Meeting(
        id=str(uuid.uuid4()),
        title=title,
        join_code=generate_join_code(session),
        host_user_id=host.id,
        status="scheduled",
    )
    session.add(meeting)
    session.flush()

    session.add(
        MeetingParticipant(
            id=str(uuid.uuid4()),
            meeting_id=meeting.id,
            user_id=host.id,
            role="host",
            status="joined",
            display_name=host.display_name,
            joined_at=utcnow(),
            last_seen_at=utcnow(),
        )
    )
    add_history(session, meeting.id, host.id, "meeting_created", {"join_code": meeting.join_code})
    session.flush()

    return ServiceResult(True, "Meeting created.", {"meeting": meeting_to_dict(meeting, 1)})


def join_meeting_by_code(session: Session, *, join_code: str, user_id: str) -> ServiceResult:
    join_code = normalize_join_code(join_code)
    if not join_code:
        return ServiceResult(False, "Enter a valid join code.")

    meeting = session.scalar(select(Meeting).where(Meeting.join_code == join_code))
    if not meeting:
        return ServiceResult(False, "No meeting found for that join code.")
    if meeting.status == "ended":
        return ServiceResult(False, "This meeting has ended.")

    user = session.get(User, user_id)
    if not user:
        return ServiceResult(False, "Your account was not found. Please log in again.")

    participant = session.scalar(
        select(MeetingParticipant).where(
            MeetingParticipant.meeting_id == meeting.id,
            MeetingParticipant.user_id == user.id,
        )
    )
    now = utcnow()
    if participant:
        participant.status = "joined"
        participant.last_seen_at = now
        if not participant.joined_at:
            participant.joined_at = now
    else:
        participant = MeetingParticipant(
            id=str(uuid.uuid4()),
            meeting_id=meeting.id,
            user_id=user.id,
            role="participant",
            status="joined",
            display_name=user.display_name,
            joined_at=now,
            last_seen_at=now,
        )
        session.add(participant)

    if meeting.status == "scheduled":
        meeting.status = "live"
        meeting.started_at = now

    add_history(session, meeting.id, user.id, "participant_joined", {"join_code": meeting.join_code})
    session.flush()

    count = session.scalar(select(func.count()).select_from(MeetingParticipant).where(MeetingParticipant.meeting_id == meeting.id)) or 0
    return ServiceResult(True, "Joined meeting.", {"meeting": meeting_to_dict(meeting, int(count))})


def get_user_meetings(session: Session, user_id: str) -> list[dict]:
    rows = session.execute(
        select(Meeting, func.count(MeetingParticipant.id))
        .join(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
        .where(Meeting.id.in_(select(MeetingParticipant.meeting_id).where(MeetingParticipant.user_id == user_id)))
        .group_by(Meeting.id)
        .order_by(desc(Meeting.created_at))
    ).all()
    return [meeting_to_dict(meeting, int(count or 0)) for meeting, count in rows]


def get_meeting_for_user(session: Session, meeting_id: str, user_id: str) -> Meeting | None:
    return session.scalar(
        select(Meeting)
        .join(MeetingParticipant, MeetingParticipant.meeting_id == Meeting.id)
        .where(Meeting.id == meeting_id, MeetingParticipant.user_id == user_id)
    )


def get_meeting_details(session: Session, meeting_id: str, user_id: str) -> ServiceResult:
    meeting = get_meeting_for_user(session, meeting_id, user_id)
    if not meeting:
        return ServiceResult(False, "Meeting not found or you have not joined it.")

    participants = session.execute(
        select(MeetingParticipant, User)
        .join(User, User.id == MeetingParticipant.user_id)
        .where(MeetingParticipant.meeting_id == meeting.id)
        .order_by(MeetingParticipant.role.desc(), MeetingParticipant.joined_at.asc())
    ).all()
    participant_payload = [
        {
            "user_id": user.id,
            "username": user.username,
            "display_name": participant.display_name,
            "role": participant.role,
            "status": participant.status,
            "joined_at": participant.joined_at,
        }
        for participant, user in participants
    ]
    return ServiceResult(
        True,
        "Meeting loaded.",
        {"meeting": meeting_to_dict(meeting, len(participant_payload)), "participants": participant_payload},
    )


def get_meeting_history(session: Session, user_id: str, limit: int = 50) -> list[dict]:
    rows = session.execute(
        select(MeetingHistory, Meeting, User)
        .join(Meeting, Meeting.id == MeetingHistory.meeting_id)
        .outerjoin(User, User.id == MeetingHistory.user_id)
        .where(Meeting.id.in_(select(MeetingParticipant.meeting_id).where(MeetingParticipant.user_id == user_id)))
        .order_by(desc(MeetingHistory.created_at))
        .limit(limit)
    ).all()

    return [
        {
            "id": history.id,
            "meeting_title": meeting.title,
            "join_code": meeting.join_code,
            "actor": user.display_name if user else "System",
            "action": history.action,
            "details": history.details or {},
            "created_at": history.created_at,
        }
        for history, meeting, user in rows
    ]
