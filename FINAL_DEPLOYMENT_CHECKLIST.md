# Zoet+ Deployment Checklist

- Push this folder to GitHub.
- Deploy `app.py` on Streamlit Community Cloud.
- Add `DATABASE_URL` from Neon PostgreSQL.
- Set `APP_BASE_URL` to the deployed Streamlit URL.
- Add `OPENAI_API_KEY` if AI moderation should be active.
- Add TURN secrets for reliable WebRTC across restrictive networks.
- Test signup, login, meeting creation, joining, webcam access, focus metadata, chat, and moderation.

The older `client/` and `server/` folders are retained as reference only. The public Streamlit app is `app.py`.
