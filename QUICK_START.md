# Quick Start

Zoet+ now runs as a Streamlit app.

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

For public deployment, use `app.py` as the Streamlit Community Cloud entrypoint and configure `DATABASE_URL` with a Neon PostgreSQL connection string.
