import { Bell, CalendarPlus, Check, Lock, Users, Video } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";

export default function Dashboard({ currentUser, users, meetings, onRefresh, socket, onJoinMeeting }) {
  const [title, setTitle] = useState("AI Class: Secure Video Meeting");
  const [selected, setSelected] = useState([]);
  const [notice, setNotice] = useState("");

  const otherUsers = useMemo(
    () => users.filter((u) => u.username !== currentUser.username),
    [users, currentUser]
  );

  useEffect(() => {
    const handleInvite = ({ meeting }) => {
      setNotice(`New app-to-app invite: ${meeting.title}`);
      onRefresh();
    };
    socket.on("invite:new", handleInvite);
    return () => socket.off("invite:new", handleInvite);
  }, [socket, onRefresh]);

  async function createMeeting(e) {
    e.preventDefault();
    const data = await api("/api/meetings", {
      method: "POST",
      body: JSON.stringify({
        title,
        invitedUsernames: selected
      })
    });
    setNotice(`Meeting created: ${data.meeting.title}`);
    await onRefresh();
  }

  async function acceptAndJoin(meetingId) {
    await api(`/api/meetings/${meetingId}/accept`, {
      method: "POST"
    });
    onJoinMeeting(meetingId);
  }

  return (
    <div className="page-grid">
      <section className="panel hero">
        <div>
          <div className="eyebrow"><Lock size={16} /> No public links</div>
          <h1>Secure app-to-app video meetings</h1>
          <p>
            Invite people by username, detect focus drops, block abusive chat, and keep unknown users outside the room.
          </p>
        </div>
        <div className="hero-actions">
          <button onClick={() => document.getElementById("create-meeting")?.scrollIntoView({ behavior: "smooth" })}>
            <CalendarPlus size={18} /> Create meeting
          </button>
        </div>
      </section>

      <div className="stats">
        <div className="stat"><Users /><span>{users.length}</span><p>Users</p></div>
        <div className="stat"><Video /><span>{meetings.length}</span><p>Your meetings</p></div>
        <div className="stat"><Bell /><span>{meetings.filter(m => m.hostUsername !== currentUser.username).length}</span><p>Invites</p></div>
      </div>

      {notice ? <div className="notice">{notice}</div> : null}

      <section id="create-meeting" className="panel">
        <h2>Create secure meeting</h2>
        <p className="muted">Only selected usernames receive the meeting. No shareable link is generated.</p>
        <form className="meeting-form" onSubmit={createMeeting}>
          <input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Meeting title" />
          <div className="user-select-grid">
            {otherUsers.map((user) => {
              const active = selected.includes(user.username);
              return (
                <button
                  type="button"
                  className={active ? "user-chip active" : "user-chip"}
                  key={user.username}
                  onClick={() =>
                    setSelected((prev) =>
                      prev.includes(user.username)
                        ? prev.filter((item) => item !== user.username)
                        : [...prev, user.username]
                    )
                  }
                >
                  <span>@{user.username}</span>
                  <small>{user.status}</small>
                  {active ? <Check size={16} /> : null}
                </button>
              );
            })}
          </div>
          <button disabled={!selected.length}>Create and notify invited users</button>
        </form>
      </section>

      <section className="panel">
        <h2>Your meetings</h2>
        <div className="meeting-list">
          {meetings.map((meeting) => (
            <div className="meeting-card" key={meeting.id}>
              <div>
                <h3>{meeting.title}</h3>
                <p>Host: @{meeting.hostUsername}</p>
                <small>Status: {meeting.status}</small>
              </div>
              <button onClick={() => acceptAndJoin(meeting.id)}>
                <Video size={17} /> Join
              </button>
            </div>
          ))}
          {!meetings.length ? <p className="muted">No meetings yet. Create one or wait for an invite.</p> : null}
        </div>
      </section>
    </div>
  );
}
