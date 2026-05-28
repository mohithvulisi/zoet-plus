from __future__ import annotations

import threading
import time
from datetime import datetime
from typing import Any

import av
import cv2
import numpy as np
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from .db import session_scope
from .models import FocusEvent, User


def save_focus_event(
    *,
    meeting_id: str,
    user_id: str,
    event_type: str,
    confidence: float,
    face_count: int,
    details: dict | None = None,
) -> None:
    import uuid

    with session_scope() as session:
        session.add(
            FocusEvent(
                id=str(uuid.uuid4()),
                meeting_id=meeting_id,
                user_id=user_id,
                event_type=event_type,
                confidence=float(confidence),
                face_count=int(face_count),
                details=details or {},
            )
        )


def get_recent_focus_events(session: Session, meeting_id: str, limit: int = 12) -> list[dict]:
    rows = session.execute(
        select(FocusEvent, User)
        .join(User, User.id == FocusEvent.user_id)
        .where(FocusEvent.meeting_id == meeting_id)
        .order_by(desc(FocusEvent.created_at))
        .limit(limit)
    ).all()
    return [
        {
            "event_type": event.event_type,
            "confidence": event.confidence,
            "face_count": event.face_count,
            "details": event.details or {},
            "created_at": event.created_at,
            "display_name": user.display_name,
            "username": user.username,
        }
        for event, user in rows
    ]


class FocusVideoProcessor:
    def __init__(self, meeting_id: str, user_id: str):
        self.meeting_id = meeting_id
        self.user_id = user_id
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.lock = threading.Lock()
        self.latest_event: dict[str, Any] = {
            "event_type": "camera_starting",
            "confidence": 0.0,
            "face_count": 0,
            "details": {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.last_saved_at = 0.0
        self.last_saved_type = ""
        self.last_error = ""

    def get_latest_event(self) -> dict[str, Any]:
        with self.lock:
            return dict(self.latest_event)

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        image = frame.to_ndarray(format="bgr24")
        event, faces = self._detect_focus(image)
        self._draw_overlay(image, event, faces)
        self._set_latest_event(event)
        self._maybe_persist(event)
        return av.VideoFrame.from_ndarray(image, format="bgr24")

    def _detect_focus(self, image: np.ndarray) -> tuple[dict[str, Any], list[tuple[int, int, int, int]]]:
        height, width = image.shape[:2]
        if self.face_cascade.empty():
            return (
                {
                    "event_type": "focus_detection_unavailable",
                    "confidence": 0.0,
                    "face_count": 0,
                    "details": {"detector": "opencv_haar"},
                    "timestamp": datetime.utcnow().isoformat(),
                },
                [],
            )

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        detected = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(55, 55))
        faces = sorted([tuple(map(int, face)) for face in detected], key=lambda face: face[2] * face[3], reverse=True)
        face_count = len(faces)

        if face_count == 0:
            return (
                {
                    "event_type": "face_missing",
                    "confidence": 0.95,
                    "face_count": 0,
                    "details": {"detector": "opencv_haar"},
                    "timestamp": datetime.utcnow().isoformat(),
                },
                faces,
            )

        if face_count > 1:
            return (
                {
                    "event_type": "multiple_faces",
                    "confidence": 0.9,
                    "face_count": face_count,
                    "details": {"detector": "opencv_haar"},
                    "timestamp": datetime.utcnow().isoformat(),
                },
                faces,
            )

        x, y, w, h = faces[0]
        face_center_x = x + w / 2
        face_center_y = y + h / 2
        horizontal_offset = abs(face_center_x - width / 2) / max(width, 1)
        vertical_offset = abs(face_center_y - height / 2) / max(height, 1)
        area_ratio = (w * h) / max(width * height, 1)
        low_focus = horizontal_offset > 0.24 or vertical_offset > 0.24 or area_ratio < 0.035

        event_type = "looking_away_low_focus" if low_focus else "face_present"
        confidence = 0.72 if low_focus else 0.88
        return (
            {
                "event_type": event_type,
                "confidence": confidence,
                "face_count": face_count,
                "details": {
                    "detector": "opencv_haar",
                    "horizontal_offset": round(horizontal_offset, 3),
                    "vertical_offset": round(vertical_offset, 3),
                    "face_area_ratio": round(area_ratio, 3),
                },
                "timestamp": datetime.utcnow().isoformat(),
            },
            faces,
        )

    def _draw_overlay(self, image: np.ndarray, event: dict[str, Any], faces: list[tuple[int, int, int, int]]) -> None:
        color = (34, 197, 94) if event["event_type"] == "face_present" else (0, 165, 255)
        if event["event_type"] in {"face_missing", "multiple_faces"}:
            color = (48, 64, 255)

        for x, y, w, h in faces:
            cv2.rectangle(image, (x, y), (x + w, y + h), color, 2)

        label = event["event_type"].replace("_", " ")
        cv2.rectangle(image, (12, 12), (min(440, image.shape[1] - 12), 58), (15, 23, 42), -1)
        cv2.putText(image, label, (24, 43), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)

    def _set_latest_event(self, event: dict[str, Any]) -> None:
        with self.lock:
            self.latest_event = event

    def _maybe_persist(self, event: dict[str, Any]) -> None:
        now = time.time()
        event_type = str(event["event_type"])
        should_save = event_type != self.last_saved_type or now - self.last_saved_at >= 10
        if not should_save:
            return

        try:
            save_focus_event(
                meeting_id=self.meeting_id,
                user_id=self.user_id,
                event_type=event_type,
                confidence=float(event["confidence"]),
                face_count=int(event["face_count"]),
                details=event.get("details") or {},
            )
            self.last_saved_at = now
            self.last_saved_type = event_type
            self.last_error = ""
        except Exception as exc:
            self.last_error = str(exc)
