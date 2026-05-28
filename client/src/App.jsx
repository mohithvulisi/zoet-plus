import { useCallback, useEffect, useState } from "react";
import Login from "./components/Login";
import Dashboard from "./components/Dashboard";
import MeetingRoom from "./components/MeetingRoom";
import { api } from "./lib/api";
import { socket } from "./lib/socket";
import "./styles.css";

export default function App() {
  const [usernameInput, setUsernameInput] = useState(localStorage.getItem("zoet_username") || "");
  const [passwordInput, setPasswordInput] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [users, setUsers] = useState([]);
  const [meetings, setMeetings] = useState([]);
  const [activeMeetingId, setActiveMeetingId] = useState("");
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    if (!currentUser?.username) return;
    const data = await api("/api/state");
    setUsers(data.users);
    setMeetings(data.meetings);
  }, [currentUser]);

  async function login(e) {
    e?.preventDefault();
    try {
      const endpoint = isSignup ? "/api/signup" : "/api/login";
      const data = await api(endpoint, {
        method: "POST",
        body: JSON.stringify({ username: usernameInput, password: passwordInput })
      });
      localStorage.setItem("zoet_username", data.user.username);
      localStorage.setItem("zoet_token", data.token);
      socket.auth = { token: data.token };
      setCurrentUser(data.user);
      setPasswordInput("");
      setError("");
    } catch (err) {
      setError(err.message);
    }
  }

  function logout() {
    localStorage.removeItem("zoet_username");
    localStorage.removeItem("zoet_token");
    socket.disconnect();
    setCurrentUser(null);
    setActiveMeetingId("");
  }

  useEffect(() => {
    const token = localStorage.getItem("zoet_token");
    if (!token || currentUser) return;
    api("/api/me")
      .then((data) => {
        setCurrentUser(data.user);
        socket.auth = { token };
      })
      .catch(() => {
        localStorage.removeItem("zoet_token");
        localStorage.removeItem("zoet_username");
      });
  }, [currentUser]);

  useEffect(() => {
    if (!currentUser) return;

    socket.auth = { token: localStorage.getItem("zoet_token") };
    if (!socket.connected) socket.connect();

    const usersUpdate = (nextUsers) => setUsers(nextUsers);
    socket.on("users:update", usersUpdate);

    refresh();

    return () => socket.off("users:update", usersUpdate);
  }, [currentUser, refresh]);

  if (!currentUser) {
    return (
      <Login
        username={usernameInput}
        password={passwordInput}
        setUsername={setUsernameInput}
        setPassword={setPasswordInput}
        onLogin={login}
        onToggleMode={() => setIsSignup((prev) => !prev)}
        error={error}
        isSignup={isSignup}
      />
    );
  }

  return (
    <div className="app">
      <header className="topbar">
        <div>
          <strong>Zoet+</strong>
          <span>Logged in as @{currentUser.username}</span>
        </div>
        <button className="ghost" onClick={logout}>Logout</button>
      </header>

      {activeMeetingId ? (
        <MeetingRoom
          meetingId={activeMeetingId}
          currentUser={currentUser}
          socket={socket}
          onLeave={() => {
            setActiveMeetingId("");
            refresh();
          }}
        />
      ) : (
        <Dashboard
          currentUser={currentUser}
          users={users}
          meetings={meetings}
          socket={socket}
          onRefresh={refresh}
          onJoinMeeting={setActiveMeetingId}
        />
      )}
    </div>
  );
}
