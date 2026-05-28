import dotenv from "dotenv";
import express from "express";
import cors from "cors";
import http from "http";
import { Server } from "socket.io";
import jwt from "jsonwebtoken";
import {
  acceptInvite,
  createMeeting,
  getChatMessages,
  getDb,
  getLatestFocusByMeeting,
  getMeeting,
  getMeetingMembers,
  getMeetingsForUser,
  getModerationEvents,
  getUsersPublic,
  getUserByUsername,
  saveChatMessage,
  saveFocusEvent,
  saveModerationEvent,
  setUserStatus,
  upsertUser,
  userCanJoin,
  createUser,
  verifyUserPassword
} from "./store.js";
import { moderateText } from "./moderation.js";

dotenv.config();

const PORT = process.env.PORT || 4000;
const CLIENT_ORIGIN = process.env.CLIENT_ORIGIN || "http://localhost:5173";
const JWT_SECRET = process.env.JWT_SECRET || "change-me-to-a-strong-secret";

const app = express();
app.use(cors({ origin: CLIENT_ORIGIN, credentials: true }));
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, {
  cors: { origin: CLIENT_ORIGIN, methods: ["GET", "POST"], credentials: true }
});

const onlineUsers = new Map();
const roomParticipants = new Map();

function createToken(user) {
  return jwt.sign({ username: user.username }, JWT_SECRET, {
    expiresIn: "7d"
  });
}

function authenticateToken(req, res, next) {
  const header = String(req.headers.authorization || "").split(" ");
  const token = header[0] === "Bearer" ? header[1] : null;
  if (!token) return res.status(401).json({ error: "Authentication required." });

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    req.user = { username: String(payload.username).toLowerCase() };
    next();
  } catch (error) {
    return res.status(401).json({ error: "Invalid or expired token." });
  }
}

function emitUsers() {
  io.emit("users:update", getUsersPublic());
}

function getRoomSockets(meetingId) {
  return roomParticipants.get(meetingId) || [];
}

app.get("/api/health", (req, res) => {
  res.json({ ok: true, app: "Zoet+" });
});

app.post("/api/signup", (req, res) => {
  const username = String(req.body.username || "").trim().toLowerCase();
  const password = String(req.body.password || "");

  if (!username || username.length < 3) {
    return res.status(400).json({ error: "Username must be at least 3 characters." });
  }

  if (!password || password.length < 6) {
    return res.status(400).json({ error: "Password must be at least 6 characters." });
  }

  if (getUserByUsername(username)) {
    return res.status(409).json({ error: "Username already exists." });
  }

  const user = createUser({ username, password });
  const token = createToken(user);
  res.json({ user: getUsersPublic().find((item) => item.username === user.username), token });
});

app.post("/api/login", (req, res) => {
  const username = String(req.body.username || "").trim().toLowerCase();
  const password = String(req.body.password || "");

  if (!username || username.length < 3 || !password) {
    return res.status(400).json({ error: "Valid username and password are required." });
  }

  const user = verifyUserPassword(username, password);
  if (!user) {
    return res.status(401).json({ error: "Invalid username or password." });
  }

  const token = createToken(user);
  res.json({ user: getUsersPublic().find((item) => item.username === user.username), token });
});

app.get("/api/me", authenticateToken, (req, res) => {
  const user = getUserByUsername(req.user.username);
  if (!user) return res.status(404).json({ error: "User not found." });
  res.json({ user: getUsersPublic().find((item) => item.username === user.username) });
});

app.get("/api/users", authenticateToken, (req, res) => {
  res.json({ users: getUsersPublic() });
});

app.get("/api/state", authenticateToken, (req, res) => {
  res.json({
    users: getUsersPublic(),
    meetings: getMeetingsForUser(req.user.username)
  });
});

app.post("/api/meetings", authenticateToken, (req, res) => {
  const title = String(req.body.title || "").trim();
  const hostUsername = req.user.username;
  const invitedUsernames = Array.from(new Set((req.body.invitedUsernames || []).map((item) => String(item).trim().toLowerCase())));

  if (!title) {
    return res.status(400).json({ error: "Title is required." });
  }

  const meeting = createMeeting({ title, hostUsername, invitedUsernames });
  for (const username of invitedUsernames) {
    const socketId = onlineUsers.get(username);
    if (socketId) {
      io.to(socketId).emit("invite:new", { meeting });
    }
  }

  res.json({ meeting });
});

app.get("/api/meetings/:meetingId", authenticateToken, (req, res) => {
  const meeting = getMeeting(req.params.meetingId);
  if (!meeting) return res.status(404).json({ error: "Meeting not found." });
  if (!userCanJoin(req.params.meetingId, req.user.username)) {
    return res.status(403).json({ error: "Access denied." });
  }

  res.json({
    meeting,
    members: getMeetingMembers(req.params.meetingId),
    chatMessages: getChatMessages(req.params.meetingId),
    moderationEvents: getModerationEvents(req.params.meetingId),
    focusEvents: getLatestFocusByMeeting(req.params.meetingId)
  });
});

app.post("/api/meetings/:meetingId/accept", authenticateToken, (req, res) => {
  const username = req.user.username;
  const meeting = getMeeting(req.params.meetingId);
  if (!meeting) return res.status(404).json({ error: "Meeting not found." });

  if (meeting.hostUsername === username) {
    return res.json({ invite: null, message: "Host may join the meeting without accepting an invite." });
  }

  const invite = acceptInvite(req.params.meetingId, username);
  if (!invite) return res.status(404).json({ error: "Invite not found." });
  res.json({ invite });
});

io.use((socket, next) => {
  const token = socket.handshake.auth?.token || socket.handshake.query?.token;
  if (!token) {
    return next(new Error("Authentication required."));
  }

  try {
    const payload = jwt.verify(token, JWT_SECRET);
    socket.data.username = String(payload.username).toLowerCase();
    next();
  } catch (error) {
    next(new Error("Authentication failed."));
  }
});

io.on("connection", (socket) => {
  const username = socket.data.username;
  if (username) {
    onlineUsers.set(username, socket.id);
    setUserStatus(username, "online");
    emitUsers();
  }

  socket.on("user:online", () => {
    if (!socket.data.username) return;
    onlineUsers.set(socket.data.username, socket.id);
    setUserStatus(socket.data.username, "online");
    emitUsers();
  });

  socket.on("meeting:join", ({ meetingId }, ack) => {
    const username = socket.data.username;
    if (!userCanJoin(meetingId, username)) {
      ack?.({ ok: false, error: "You are not invited to this meeting." });
      return;
    }

    socket.join(meetingId);
    socket.data.meetingId = meetingId;

    const current = roomParticipants.get(meetingId) || [];
    const already = current.some((item) => item.socketId === socket.id);
    if (!already) current.push({ socketId: socket.id, username });
    roomParticipants.set(meetingId, current);

    const otherParticipants = current.filter((item) => item.socketId !== socket.id);
    ack?.({ ok: true, participants: otherParticipants, members: getMeetingMembers(meetingId) });

    socket.to(meetingId).emit("participant:joined", { socketId: socket.id, username });
    io.to(meetingId).emit("focus:update", getLatestFocusByMeeting(meetingId));
  });

  socket.on("webrtc:offer", ({ to, offer }) => {
    io.to(to).emit("webrtc:offer", { from: socket.id, username: socket.data.username, offer });
  });

  socket.on("webrtc:answer", ({ to, answer }) => {
    io.to(to).emit("webrtc:answer", { from: socket.id, answer });
  });

  socket.on("webrtc:ice-candidate", ({ to, candidate }) => {
    io.to(to).emit("webrtc:ice-candidate", { from: socket.id, candidate });
  });

  socket.on("chat:send", ({ meetingId, text }, ack) => {
    const username = socket.data.username;
    if (!userCanJoin(meetingId, username)) {
      ack?.({ ok: false, error: "Not allowed." });
      return;
    }

    const result = moderateText(text);
    const message = saveChatMessage({
      meetingId,
      username,
      text,
      blocked: result.blocked,
      toxicityScore: result.toxicityScore
    });

    if (result.blocked) {
      const event = saveModerationEvent({
        meetingId,
        username,
        source: "chat",
        content: text,
        toxicityScore: result.toxicityScore,
        action: result.action
      });
      io.to(meetingId).emit("moderation:new", event);
      ack?.({ ok: true, blocked: true, result });
      return;
    }

    io.to(meetingId).emit("chat:new", message);
    ack?.({ ok: true, blocked: false, result });
  });

  socket.on("focus:report", ({ meetingId, focusScore, signal }) => {
    const username = socket.data.username;
    if (!meetingId || !username || !userCanJoin(meetingId, username)) return;

    const event = saveFocusEvent({
      meetingId,
      username,
      focusScore: Number(focusScore),
      signal: String(signal || "unknown")
    });

    const latest = getLatestFocusByMeeting(meetingId);
    io.to(meetingId).emit("focus:update", latest);

    const unfocused = latest.filter((item) => item.focusScore < 50);
    const percent = latest.length ? Math.round((unfocused.length / latest.length) * 100) : 0;
    if (percent > 50) {
      io.to(meetingId).emit("host:attention-alert", {
        meetingId,
        percent,
        message: `${percent}% of participants appear unfocused. Change pace, ask a question, or switch activity.`
      });
    }
  });

  socket.on("disconnect", () => {
    const username = socket.data.username;
    if (username && onlineUsers.get(username) === socket.id) {
      onlineUsers.delete(username);
      setUserStatus(username, "offline");
      emitUsers();
    }

    const meetingId = socket.data.meetingId;
    if (meetingId) {
      const current = roomParticipants.get(meetingId) || [];
      const next = current.filter((item) => item.socketId !== socket.id);
      roomParticipants.set(meetingId, next);
      socket.to(meetingId).emit("participant:left", { socketId: socket.id, username });
    }
  });
});

server.listen(PORT, () => {
  console.log(`Zoet+ server running on http://localhost:${PORT}`);
});
