# Zoet+

Zoet+ is now a deployable Streamlit web app for secure meeting rooms with login, PostgreSQL persistence, webcam access, focus metadata, chat, and optional OpenAI moderation.

The public deployment entrypoint is:

```bash
streamlit run app.py
```

Streamlit Community Cloud should deploy `app.py` from the repository root.

## Current Stack

- Streamlit
- streamlit-webrtc
- SQLAlchemy
- PostgreSQL for production, Neon recommended
- bcrypt password hashing
- OpenCV face/focus detection
- OpenAI Moderation API when `OPENAI_API_KEY` is configured

## Local Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
streamlit run app.py
```

Open:

```text
http://localhost:8501
```

For local development only, the app can use `data/zoet_local.db` when `DATABASE_URL` is missing and `ZOET_ALLOW_SQLITE_FALLBACK=true`. Do not use that fallback for public production data.

## Required Environment Variables

Production should set these in Streamlit Cloud secrets:

```toml
DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"
APP_BASE_URL = "https://your-app.streamlit.app"
STUN_URLS = "stun:stun.l.google.com:19302"
```

Optional:

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODERATION_MODEL = "omni-moderation-latest"
TURN_URL = "turn:your-turn-host:3478"
TURN_USERNAME = "your-turn-username"
TURN_CREDENTIAL = "your-turn-password"
ZOET_ALLOW_SQLITE_FALLBACK = "false"
```

## Neon PostgreSQL Setup

1. Create a Neon project.
2. Create or use the default database.
3. Copy the PostgreSQL connection string.
4. Ensure it includes SSL, usually `?sslmode=require`.
5. Add it to Streamlit secrets as `DATABASE_URL`.

Zoet+ uses SQLAlchemy `create_all()` on startup, so the required tables are created automatically:

- `users`
- `meetings`
- `meeting_participants`
- `meeting_history`
- `moderation_events`
- `focus_events`
- `chat_messages`

## GitHub Setup

From this project root:

```bash
git init
git add .
git commit -m "Deploy Zoet Plus Streamlit app"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

Do not commit:

- `.env`
- `.streamlit/secrets.toml`
- `.venv/`
- `data/`

These are already covered by `.gitignore`.

## Streamlit Community Cloud Deployment

1. Push the repo to GitHub.
2. Go to Streamlit Community Cloud.
3. Create a new app from your GitHub repo.
4. Set the main file path to `app.py`.
5. In Advanced settings, paste your secrets from `.streamlit/secrets.toml`.
6. Choose Python 3.12 if prompted.
7. Deploy.
8. After deployment, set `APP_BASE_URL` to the final Streamlit app URL and redeploy/reboot.

## TURN and WebRTC Setup

Zoet+ includes a default Google STUN server:

```toml
STUN_URLS = "stun:stun.l.google.com:19302"
```

For public use across restrictive networks, add TURN credentials from a provider such as Twilio Network Traversal, Metered.ca, or your own coturn server:

```toml
TURN_URL = "turn:your-turn-host:3478"
TURN_USERNAME = "username"
TURN_CREDENTIAL = "password"
```

Without TURN, webcam access may work for many users but can fail on stricter corporate/mobile networks.

## Privacy Notes

Focus detection uses OpenCV on live webcam frames, but Zoet+ does not store raw video, screenshots, face images, or biometric templates.

Stored focus metadata is limited to:

- `user_id`
- `meeting_id`
- `event_type`
- `confidence`
- `face_count`
- timestamp
- small numeric detector details

Chat text is stored for allowed messages. Blocked or checked moderation inputs are stored in `moderation_events` as a hash, short preview, categories, scores, action, and timestamp.

## Testing Checklist

Local smoke checks:

```bash
source .venv/bin/activate
python -m py_compile app.py zoet_plus/*.py
streamlit run app.py
```

Manual app flow:

1. Signup with a username, display name, and 8+ character password.
2. Logout and login again.
3. Create a meeting.
4. Copy the join code and join link.
5. Open another browser/incognito session and create a second user.
6. Join the meeting by code or link.
7. Click START in the room and allow camera/microphone permissions.
8. Confirm focus events appear after webcam frames are processed.
9. Send chat messages.
10. If `OPENAI_API_KEY` is set, try a clearly unsafe title/message and confirm it is blocked or logged.
11. Check the History page for meeting events.

## Known Limitations

- Streamlit sessions are not cookie/JWT auth. Users remain logged in only within Streamlit session state.
- `streamlit-webrtc` provides browser media capture in the room, but this is not a full SFU-backed Zoom-style multi-party video conference.
- Reliable production WebRTC usually needs TURN.
- Database migrations are not managed by Alembic yet; tables are created on startup.
- No admin console, password reset emails, rate limiting, or email verification yet.
- OpenCV focus detection is an approximation, not biometric identification and not a medical or behavioral truth source.

## Useful References

- Streamlit Community Cloud deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Streamlit secrets management: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- Streamlit app dependencies: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies
- OpenAI moderation guide: https://platform.openai.com/docs/guides/moderation/overview
- OpenAI moderation API reference: https://platform.openai.com/docs/api-reference/moderations
- OpenAI `omni-moderation-latest` model: https://platform.openai.com/docs/models/omni-moderation-latest
