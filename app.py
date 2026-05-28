from __future__ import annotations

import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from zoet_plus.auth import authenticate_user, create_user, update_display_name
from zoet_plus.chat import get_chat_messages, save_chat_message
from zoet_plus.config import get_database_url
from zoet_plus.db import init_db, session_scope
from zoet_plus.focus import FocusVideoProcessor, get_recent_focus_events
from zoet_plus.meetings import (
    create_meeting,
    get_meeting_details,
    get_meeting_history,
    get_user_meetings,
    join_meeting_by_code,
    normalize_join_code,
)
from zoet_plus.moderation import moderate_and_record, moderation_enabled
from zoet_plus.ui import apply_theme, brand_row, empty_state, format_dt, pill
from zoet_plus.webrtc import get_rtc_configuration


st.set_page_config(
    page_title="Zoet+",
    page_icon="Z+",
    layout="wide",
    initial_sidebar_state="expanded",
)


def boot() -> None:
    apply_theme()
    init_db()
    st.session_state.setdefault("user_id", None)
    st.session_state.setdefault("username", None)
    st.session_state.setdefault("display_name", None)
    st.session_state.setdefault("page", "Dashboard")
    st.session_state.setdefault("active_meeting_id", None)

    join_code = normalize_join_code(st.query_params.get("join", ""))
    if join_code:
        st.session_state.pending_join_code = join_code
        st.session_state.page = "Join"


def login_user(user) -> None:
    st.session_state.user_id = user.id
    st.session_state.username = user.username
    st.session_state.display_name = user.display_name
    st.rerun()


def logout_user() -> None:
    for key in ("user_id", "username", "display_name"):
        st.session_state[key] = None
    st.rerun()


def render_auth() -> None:
    left, right = st.columns([1.05, 0.95], vertical_alignment="center")

    with left:
        brand_row("Public Streamlit room app")
        st.title("Secure video rooms for live classes")
        st.caption("Login or create an account to open your Zoet+ dashboard.")
        pill("PostgreSQL ready")
        pill("WebRTC")
        pill("AI moderation")
        pill("Focus metadata")

    with right:
        with st.container(border=True):
            signup_tab, login_tab = st.tabs(["Signup", "Login"])

            with signup_tab:
                with st.form("signup_form"):
                    display_name = st.text_input("Display name", placeholder="Mahi")
                    username = st.text_input("Choose username", placeholder="your.name", autocomplete="username")
                    password = st.text_input("Choose password", type="password", autocomplete="new-password")
                    submitted = st.form_submit_button("Create account", use_container_width=True)

                if submitted:
                    with session_scope() as session:
                        moderation = moderate_and_record(
                            session,
                            source="display_name",
                            content=display_name,
                        )
                        if moderation.flagged:
                            st.error("This display name was blocked by AI moderation.")
                            return
                        result = create_user(session, username, display_name, password)
                        if result.ok and result.user:
                            st.success("Account created. Opening your dashboard...")
                            login_user(result.user)
                        else:
                            st.error(result.message)

            with login_tab:
                with st.form("login_form"):
                    username = st.text_input("Username", placeholder="your.name", autocomplete="username")
                    password = st.text_input("Password", type="password", autocomplete="current-password")
                    submitted = st.form_submit_button("Login", use_container_width=True)

                if submitted:
                    with session_scope() as session:
                        result = authenticate_user(session, username, password)
                        if result.ok and result.user:
                            login_user(result.user)
                        else:
                            st.error(result.message)


def render_dashboard() -> None:
    database_url, using_sqlite = get_database_url()
    del database_url

    with st.sidebar:
        brand_row("Workspace")
        st.caption(f"Signed in as @{st.session_state.username}")
        pages = ["Dashboard", "Create", "Join", "History", "Profile"]
        st.session_state.page = st.radio(
            "Navigation",
            pages,
            index=pages.index(st.session_state.page)
            if st.session_state.page in pages
            else 0,
            label_visibility="collapsed",
        )
        if st.button("Logout", use_container_width=True):
            logout_user()

    if using_sqlite:
        st.warning("Local SQLite fallback is active for development. Add DATABASE_URL before deploying publicly.")

    if st.session_state.page == "Create":
        render_create_meeting()
    elif st.session_state.page == "Join":
        render_join_meeting()
    elif st.session_state.page == "History":
        render_history()
    elif st.session_state.page == "Profile":
        render_profile()
    else:
        render_dashboard_home()


def render_dashboard_home() -> None:
    st.title("Dashboard")
    st.caption("Protected Zoet+ workspace")

    with session_scope() as session:
        meetings = get_user_meetings(session, st.session_state.user_id)
        history = get_meeting_history(session, st.session_state.user_id, limit=5)

    col1, col2, col3 = st.columns(3)
    col1.metric("Your meetings", len(meetings))
    col2.metric("Recent events", len(history))
    col3.metric("Moderation", "On" if moderation_enabled() else "Off")

    st.subheader("Your meetings")
    if not meetings:
        empty_state("No meetings yet. Create a meeting or join with a code.")
        if st.button("Create first meeting"):
            st.session_state.page = "Create"
            st.rerun()
        return

    for meeting in meetings:
        with st.container(border=True):
            cols = st.columns([3, 1, 1])
            cols[0].markdown(f"**{meeting['title']}**")
            cols[0].markdown(f"<span class='zoet-room-code'>{meeting['join_code']}</span>", unsafe_allow_html=True)
            cols[0].caption(f"Host @{meeting['host_username']} | {meeting['status']} | Created {format_dt(meeting['created_at'])}")
            cols[1].metric("Participants", meeting["participant_count"])
            if cols[2].button("Open", key=f"open-{meeting['id']}", use_container_width=True):
                st.session_state.active_meeting_id = meeting["id"]
                st.session_state.page = "Room"
                st.rerun()


def render_create_meeting() -> None:
    st.title("Create meeting")
    st.caption("Generate a persistent Zoet+ meeting code and shareable join link.")

    with st.form("create_meeting_form"):
        title = st.text_input("Meeting title", value="AI Class: Secure Video Meeting", max_chars=140)
        submitted = st.form_submit_button("Create meeting", use_container_width=True)

    if submitted:
        with st.spinner("Creating meeting..."):
            with session_scope() as session:
                moderation = moderate_and_record(
                    session,
                    source="meeting_title",
                    content=title,
                    user_id=st.session_state.user_id,
                )
                if moderation.flagged:
                    st.error("This meeting title was blocked by AI moderation. Please choose a safer title.")
                    return

                result = create_meeting(session, title=title, host_user_id=st.session_state.user_id)
                if result.ok:
                    st.session_state.last_created_meeting = result.payload["meeting"]
                    st.success(result.message)
                else:
                    st.error(result.message)

    meeting = st.session_state.get("last_created_meeting")
    if meeting:
        with st.container(border=True):
            st.subheader(meeting["title"])
            st.markdown(f"<div class='zoet-room-code'>{meeting['join_code']}</div>", unsafe_allow_html=True)
            st.text_input("Join link", value=meeting["join_link"], disabled=True)
            if st.button("Open room", use_container_width=True):
                st.session_state.active_meeting_id = meeting["id"]
                st.session_state.page = "Room"
                st.rerun()


def render_join_meeting() -> None:
    st.title("Join meeting")
    st.caption("Use a Zoet+ join code or a generated link.")

    default_code = st.session_state.get("pending_join_code", "")
    with st.form("join_meeting_form"):
        join_code = st.text_input("Join code", value=default_code, placeholder="A1B2C3D")
        submitted = st.form_submit_button("Join meeting", use_container_width=True)

    if submitted:
        with st.spinner("Joining meeting..."):
            with session_scope() as session:
                result = join_meeting_by_code(session, join_code=join_code, user_id=st.session_state.user_id)
                if result.ok:
                    meeting = result.payload["meeting"]
                    st.session_state.active_meeting_id = meeting["id"]
                    st.session_state.pending_join_code = ""
                    st.success(f"Joined {meeting['title']}.")
                    st.session_state.page = "Room"
                    st.rerun()
                else:
                    st.error(result.message)


def render_history() -> None:
    st.title("Meeting history")
    st.caption("A persistent event trail for your Zoet+ meetings.")

    with session_scope() as session:
        history = get_meeting_history(session, st.session_state.user_id, limit=100)

    if not history:
        empty_state("No history yet.")
        return

    for item in history:
        with st.container(border=True):
            st.markdown(f"**{item['meeting_title']}**")
            st.caption(f"{format_dt(item['created_at'])} | {item['actor']} | {item['action']}")
            if item["details"]:
                st.json(item["details"], expanded=False)


def render_profile() -> None:
    st.title("Profile")
    st.caption("Update the participant display name shown in Zoet+ rooms.")

    if moderation_enabled():
        st.success("OpenAI moderation is enabled for display names, meeting titles, and chat.")
    else:
        st.warning("OpenAI moderation is disabled because OPENAI_API_KEY is missing.")

    with st.form("profile_form"):
        display_name = st.text_input("Display name", value=st.session_state.display_name or "", max_chars=80)
        submitted = st.form_submit_button("Save display name", use_container_width=True)

    if submitted:
        with session_scope() as session:
            moderation = moderate_and_record(
                session,
                source="display_name",
                content=display_name,
                user_id=st.session_state.user_id,
            )
            if moderation.flagged:
                st.error("This display name was blocked by AI moderation.")
                return
            result = update_display_name(session, st.session_state.user_id, display_name)
            if result.ok and result.user:
                st.session_state.display_name = result.user.display_name
                st.success(result.message)
            else:
                st.error(result.message)


def render_room_placeholder() -> None:
    meeting_id = st.session_state.get("active_meeting_id")
    if not meeting_id:
        st.session_state.page = "Dashboard"
        st.rerun()

    with session_scope() as session:
        result = get_meeting_details(session, meeting_id, st.session_state.user_id)

    if not result.ok:
        st.error(result.message)
        if st.button("Back to dashboard"):
            st.session_state.page = "Dashboard"
            st.rerun()
        return

    meeting = result.payload["meeting"]
    participants = result.payload["participants"]
    render_meeting_room(meeting, participants)


def render_meeting_room(meeting: dict, participants: list[dict]) -> None:
    with st.sidebar:
        brand_row("Live room")
        st.caption(f"Room code {meeting['join_code']}")
        if st.button("Dashboard", use_container_width=True):
            st.session_state.page = "Dashboard"
            st.session_state.active_meeting_id = None
            st.rerun()
        if st.button("Logout", use_container_width=True):
            logout_user()

    st.title(meeting["title"])
    st.markdown(f"<span class='zoet-room-code'>{meeting['join_code']}</span>", unsafe_allow_html=True)
    st.caption(f"{meeting['status']} | {meeting['participant_count']} participant(s)")

    main_col, side_col = st.columns([2.2, 1])
    with main_col:
        st.subheader("Live camera and microphone")
        try:
            ctx = webrtc_streamer(
                key=f"zoet-room-{meeting['id']}-{st.session_state.user_id}",
                mode=WebRtcMode.SENDRECV,
                rtc_configuration=get_rtc_configuration(),
                media_stream_constraints={"video": True, "audio": True},
                video_processor_factory=lambda: FocusVideoProcessor(
                    meeting_id=meeting["id"],
                    user_id=st.session_state.user_id,
                ),
                async_processing=True,
            )
            if not ctx.state.playing:
                st.info("Click START and allow camera/microphone access in your browser.")
            elif ctx.video_processor:
                event = ctx.video_processor.get_latest_event()
                st.success(
                    f"Focus signal: {event['event_type'].replace('_', ' ')} "
                    f"({event['confidence']:.0%} confidence)"
                )
                if ctx.video_processor.last_error:
                    st.warning("Focus metadata could not be saved. Check database connectivity.")
        except Exception as exc:
            st.error("WebRTC could not start. Check camera/microphone permissions and TURN settings.")
            st.caption(str(exc))

        render_chat(meeting["id"])

    with side_col:
        st.subheader("Participants")
        for participant in participants:
            with st.container(border=True):
                st.markdown(f"**{participant['display_name']}**")
                st.caption(f"@{participant['username']} | {participant['role']} | {participant['status']}")

        st.subheader("Connection")
        st.caption("STUN is enabled by default. Add TURN secrets for restrictive networks.")

        st.subheader("Focus events")
        st.caption("Only metadata is stored. No images, screenshots, video, or biometric templates are saved.")
        with session_scope() as session:
            focus_events = get_recent_focus_events(session, meeting["id"], limit=8)
        if not focus_events:
            empty_state("Start camera to create focus metadata.")
        for event in focus_events:
            with st.container(border=True):
                st.markdown(f"**{event['event_type'].replace('_', ' ')}**")
                st.caption(
                    f"{event['display_name']} | {event['confidence']:.0%} | "
                    f"{event['face_count']} face(s) | {event['created_at']}"
                )


def render_chat(meeting_id: str) -> None:
    st.subheader("Room chat")
    with session_scope() as session:
        messages = get_chat_messages(session, meeting_id, limit=60)

    if not messages:
        empty_state("No chat messages yet.")
    for message in messages:
        with st.chat_message("user"):
            st.markdown(f"**{message['display_name']}**  \n{message['body']}")

    with st.form(f"chat_form_{meeting_id}", clear_on_submit=True):
        text = st.text_input("Message", placeholder="Type a message...")
        submitted = st.form_submit_button("Send", use_container_width=True)

    if submitted:
        text = str(text or "").strip()
        if not text:
            st.warning("Write a message before sending.")
            return
        with session_scope() as session:
            moderation = moderate_and_record(
                session,
                source="chat_message",
                content=text,
                meeting_id=meeting_id,
                user_id=st.session_state.user_id,
            )
            if moderation.flagged:
                st.error("Your message was blocked by AI moderation.")
                return
            save_chat_message(session, meeting_id=meeting_id, user_id=st.session_state.user_id, body=text)
        st.rerun()


def main() -> None:
    boot()
    if st.session_state.user_id:
        if st.session_state.page == "Room":
            render_room_placeholder()
        else:
            render_dashboard()
    else:
        render_auth()


if __name__ == "__main__":
    main()
