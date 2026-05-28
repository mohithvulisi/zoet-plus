# Zoet+ Integration Status

Zoet+ has been converted from the older React/Node MVP into a deployable Streamlit app.

## Integrated

- Streamlit entrypoint at `app.py`
- Signup, login, logout, bcrypt password hashing, and protected dashboard
- SQLAlchemy models for users, meetings, participants, history, moderation events, focus events, and chat
- PostgreSQL support through `DATABASE_URL`, with Neon recommended
- Local SQLite fallback for development only
- Meeting creation, unique join codes, join links, participants, and history
- `streamlit-webrtc` camera/microphone room
- STUN config and optional TURN secrets
- OpenCV webcam focus detection
- Privacy-preserving focus metadata storage only
- Chat messages
- OpenAI moderation for meeting titles, chat messages, and display names when `OPENAI_API_KEY` exists
- Graceful moderation-disabled path when no OpenAI key exists
- Streamlit Community Cloud deployment docs and secrets examples

## Still MVP-Level

- Streamlit session state is used for login sessions, not persistent browser cookies or JWT.
- The WebRTC room captures media but is not an SFU-backed multi-party conferencing stack.
- Focus detection is approximate OpenCV metadata, not gaze tracking.
- Database migrations are handled by SQLAlchemy `create_all()` rather than Alembic.
- Password reset, email verification, admin controls, rate limiting, and audit exports are not implemented yet.
