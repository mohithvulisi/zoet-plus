from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any

from openai import OpenAI
from sqlalchemy.orm import Session

from .config import get_setting
from .models import ModerationEvent


@dataclass(frozen=True)
class ModerationResult:
    enabled: bool
    flagged: bool
    action: str
    message: str
    model: str | None = None
    categories: dict | None = None
    category_scores: dict | None = None


def moderation_enabled() -> bool:
    return bool(get_setting("OPENAI_API_KEY", "").strip())


def content_hash(content: str) -> str:
    return hashlib.sha256(str(content or "").encode("utf-8")).hexdigest()


def content_preview(content: str, limit: int = 160) -> str:
    text = " ".join(str(content or "").split())
    return text[:limit]


def _to_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict"):
        return value.dict()
    return {key: item for key, item in vars(value).items() if not key.startswith("_")}


def moderate_text(content: str) -> ModerationResult:
    text = str(content or "").strip()
    if not text:
        return ModerationResult(False, False, "allow", "No content to moderate.")

    api_key = get_setting("OPENAI_API_KEY", "").strip()
    model = get_setting("OPENAI_MODERATION_MODEL", "omni-moderation-latest").strip() or "omni-moderation-latest"
    if not api_key:
        return ModerationResult(False, False, "allow_moderation_disabled", "Moderation is disabled because OPENAI_API_KEY is missing.", model)

    try:
        client = OpenAI(api_key=api_key)
        response = client.moderations.create(model=model, input=text)
        item = response.results[0]
        categories = _to_dict(item.categories)
        category_scores = _to_dict(item.category_scores)
        flagged = bool(item.flagged)
        action = "block" if flagged else "allow"
        message = "Content was flagged by AI moderation." if flagged else "Content passed AI moderation."
        return ModerationResult(True, flagged, action, message, model, categories, category_scores)
    except Exception as exc:
        return ModerationResult(True, False, "allow_moderation_error", f"Moderation failed gracefully: {exc}", model)


def record_moderation_event(
    session: Session,
    *,
    source: str,
    content: str,
    result: ModerationResult,
    meeting_id: str | None = None,
    user_id: str | None = None,
) -> None:
    import uuid

    if not result.enabled:
        return

    session.add(
        ModerationEvent(
            id=str(uuid.uuid4()),
            meeting_id=meeting_id,
            user_id=user_id,
            source=source,
            input_hash=content_hash(content),
            content_preview=content_preview(content),
            flagged=result.flagged,
            action=result.action,
            model=result.model,
            categories=result.categories or {},
            category_scores=result.category_scores or {},
        )
    )


def moderate_and_record(
    session: Session,
    *,
    source: str,
    content: str,
    meeting_id: str | None = None,
    user_id: str | None = None,
) -> ModerationResult:
    result = moderate_text(content)
    record_moderation_event(
        session,
        source=source,
        content=content,
        result=result,
        meeting_id=meeting_id,
        user_id=user_id,
    )
    return result
