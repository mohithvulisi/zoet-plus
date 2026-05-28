# Future Zoet+ Upgrade Prompts

The current production entrypoint is `app.py` and the target deployment is Streamlit Community Cloud.

## Prompt 1: Add durable auth sessions

```text
Upgrade the Streamlit auth flow to durable cookie-backed sessions. Keep bcrypt password hashing and SQLAlchemy users. Add safe logout, session expiration, and a migration-safe session table.
```

## Prompt 2: Add Alembic migrations

```text
Add Alembic to this Streamlit + SQLAlchemy app. Generate an initial migration for users, meetings, meeting_participants, meeting_history, moderation_events, focus_events, and chat_messages. Update README deployment steps.
```

## Prompt 3: Add host controls

```text
Add host/admin controls to Zoet+: end meeting, remove participant, clear chat, export meeting history, and view moderation/focus event summaries. Keep all actions persisted in meeting_history.
```

## Prompt 4: Improve focus detection

```text
Replace the OpenCV Haar face detector with MediaPipe Face Landmarker or a stronger face/focus pipeline. Continue storing only metadata and no raw video, screenshots, images, or biometric templates.
```

## Prompt 5: Add TURN validation

```text
Add a deployment diagnostics page that verifies STUN/TURN configuration for streamlit-webrtc, shows missing secrets, and explains likely WebRTC failures without exposing credentials.
```

## Prompt 6: Production hardening

```text
Add rate limiting, account lockout after repeated login failures, password reset flow, moderation audit export, and database retention settings for focus and moderation events.
```
