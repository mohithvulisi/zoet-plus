from __future__ import annotations

from datetime import datetime

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --zoet-ink: #111827;
            --zoet-muted: #64748b;
            --zoet-line: #dbe3ee;
            --zoet-bg: #f7f9fc;
            --zoet-green: #0f9f6e;
            --zoet-blue: #2563eb;
            --zoet-amber: #d97706;
            --zoet-red: #dc2626;
        }
        .stApp {
            background:
                linear-gradient(180deg, #f7f9fc 0%, #eef6f3 42%, #f8fafc 100%);
            color: var(--zoet-ink);
        }
        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--zoet-line);
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--zoet-line);
            border-radius: 8px;
            padding: 16px 18px;
            box-shadow: 0 10px 28px rgba(17, 24, 39, 0.05);
        }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--zoet-line);
            box-shadow: 0 10px 30px rgba(17, 24, 39, 0.04);
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 8px;
            border: 1px solid #0f172a;
            background: #0f172a;
            color: #ffffff;
            font-weight: 700;
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover {
            border-color: var(--zoet-green);
            color: #ffffff;
            background: var(--zoet-green);
        }
        .zoet-brand-row {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        .zoet-mark {
            width: 44px;
            height: 44px;
            border-radius: 8px;
            display: grid;
            place-items: center;
            background: #0f172a;
            color: white;
            font-weight: 900;
            letter-spacing: 0;
        }
        .zoet-title {
            font-size: 1.5rem;
            font-weight: 850;
            line-height: 1;
        }
        .zoet-kicker {
            color: var(--zoet-muted);
            font-size: 0.92rem;
            margin-top: 2px;
        }
        .zoet-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            border: 1px solid var(--zoet-line);
            background: #ffffff;
            color: var(--zoet-muted);
            border-radius: 999px;
            padding: 6px 10px;
            font-size: 0.86rem;
            font-weight: 700;
            margin: 3px 6px 3px 0;
        }
        .zoet-empty {
            border: 1px dashed #b8c7d9;
            border-radius: 8px;
            padding: 22px;
            background: rgba(255,255,255,0.72);
            color: var(--zoet-muted);
        }
        .zoet-room-code {
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace;
            font-weight: 800;
            letter-spacing: 0.08em;
            color: #0f172a;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def brand_row(kicker: str = "Secure rooms") -> None:
    st.markdown(
        f"""
        <div class="zoet-brand-row">
            <div class="zoet-mark">Z+</div>
            <div>
                <div class="zoet-title">Zoet+</div>
                <div class="zoet-kicker">{kicker}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def pill(label: str) -> None:
    st.markdown(f'<span class="zoet-pill">{label}</span>', unsafe_allow_html=True)


def empty_state(message: str) -> None:
    st.markdown(f'<div class="zoet-empty">{message}</div>', unsafe_allow_html=True)


def format_dt(value: datetime | None) -> str:
    if not value:
        return "Not started"
    return value.strftime("%Y-%m-%d %H:%M")
