from __future__ import annotations

from datetime import datetime

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --zoet-ink: #111827;
            --zoet-strong: #0f172a;
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
                radial-gradient(circle at 12% 8%, rgba(15, 159, 110, 0.12), transparent 28%),
                radial-gradient(circle at 84% 14%, rgba(37, 99, 235, 0.10), transparent 25%),
                linear-gradient(180deg, #f8fcfb 0%, #eef7f3 48%, #f8fafc 100%);
            color: var(--zoet-ink);
        }
        .main .block-container {
            max-width: 1180px;
            padding-top: 3rem;
            padding-bottom: 4rem;
        }
        h1, h2, h3, p, label, span {
            letter-spacing: 0;
        }
        h1 {
            color: var(--zoet-strong);
            font-weight: 850;
            line-height: 1.08;
        }
        h2, h3 {
            color: var(--zoet-strong);
        }
        div[data-testid="stCaptionContainer"] {
            color: var(--zoet-muted);
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
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.96);
            border: 1px solid var(--zoet-line);
            border-radius: 12px;
            padding: 22px;
            box-shadow: 0 18px 46px rgba(15, 23, 42, 0.08);
        }
        [data-testid="stWidgetLabel"] p,
        [data-testid="stTextInputRootElement"] label,
        .stTextInput label,
        .stTextArea label {
            color: #334155 !important;
            font-weight: 700 !important;
        }
        .stTextInput input,
        .stTextArea textarea {
            background: #ffffff !important;
            color: var(--zoet-strong) !important;
            border: 1px solid #c8d4e4 !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            caret-color: var(--zoet-green) !important;
        }
        .stTextInput input:focus,
        .stTextArea textarea:focus {
            border-color: var(--zoet-green) !important;
            box-shadow: 0 0 0 3px rgba(15, 159, 110, 0.14) !important;
        }
        .stTextInput input::placeholder,
        .stTextArea textarea::placeholder {
            color: #94a3b8 !important;
            opacity: 1 !important;
        }
        button[title="View fullscreen"],
        [data-testid="InputInstructions"] {
            color: var(--zoet-muted) !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            border-bottom: 1px solid var(--zoet-line);
        }
        .stTabs [data-baseweb="tab"] {
            color: #52637a !important;
            font-weight: 800;
            padding-left: 0;
            padding-right: 16px;
        }
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: var(--zoet-green) !important;
        }
        .stTabs [data-baseweb="tab-highlight"] {
            background-color: var(--zoet-green);
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 8px;
            border: 1px solid var(--zoet-strong);
            background: var(--zoet-strong);
            color: #ffffff;
            font-weight: 700;
            min-height: 42px;
        }
        .stButton > button:hover, .stFormSubmitButton > button:hover {
            border-color: var(--zoet-green);
            color: #ffffff;
            background: var(--zoet-green);
        }
        .stAlert {
            border-radius: 8px;
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
        @media (max-width: 760px) {
            .main .block-container {
                padding-top: 1.5rem;
            }
            [data-testid="stForm"] {
                padding: 16px;
            }
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
