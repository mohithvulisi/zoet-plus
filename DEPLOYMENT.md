# Deployment

Primary target: Streamlit Community Cloud.

Deploy from GitHub with:

```text
Main file path: app.py
```

Required production secret:

```toml
DATABASE_URL = "postgresql://user:password@host/dbname?sslmode=require"
APP_BASE_URL = "https://your-app.streamlit.app"
```

Recommended optional secrets:

```toml
OPENAI_API_KEY = "sk-..."
TURN_URL = "turn:your-turn-host:3478"
TURN_USERNAME = "username"
TURN_CREDENTIAL = "password"
ZOET_ALLOW_SQLITE_FALLBACK = "false"
```

See `README.md` for the full deployment checklist.
