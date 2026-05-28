import fs from "fs";
import path from "path";
import { nanoid } from "nanoid";
import bcrypt from "bcryptjs";

const dataDir = path.join(process.cwd(), "data");
const dbPath = path.join(dataDir, "db.json");
const DEFAULT_PASSWORD = "password";

const seedUsers = [
  {
    id: "u1",
    username: "mahi.dev",
    name: "Mahi",
    role: "host",
    trustScore: 98,
    status: "offline",
    passwordHash: bcrypt.hashSync(DEFAULT_PASSWORD, 10)
  },
  {
    id: "u2",
    username: "arjun.cs",
    name: "Arjun",
    role: "student",
    trustScore: 91,
    status: "offline",
    passwordHash: bcrypt.hashSync(DEFAULT_PASSWORD, 10)
  },
  {
    id: "u3",
    username: "sana.ai",
    name: "Sana",
    role: "student",
    trustScore: 85,
    status: "offline",
    passwordHash: bcrypt.hashSync(DEFAULT_PASSWORD, 10)
  },
  {
    id: "u4",
    username: "ravi.web",
    name: "Ravi",
    role: "student",
    trustScore: 88,
    status: "offline",
    passwordHash: bcrypt.hashSync(DEFAULT_PASSWORD, 10)
  },
  {
    id: "u5",
    username: "nisha.ui",
    name: "Nisha",
    role: "student",
    trustScore: 94,
    status: "offline",
    passwordHash: bcrypt.hashSync(DEFAULT_PASSWORD, 10)
  },
  {
    id: "u6",
    username: "kiran.ml",
    name: "Kiran",
    role: "student",
    trustScore: 79,
    status: "offline",
    passwordHash: bcrypt.hashSync(DEFAULT_PASSWORD, 10)
  }
];

function hashPassword(password) {
  return bcrypt.hashSync(String(password), 10);
}

function verifyPassword(password, hash) {
  return bcrypt.compareSync(String(password), String(hash));
}

function ensureDb() {
  if (!fs.existsSync(dataDir)) fs.mkdirSync(dataDir, { recursive: true });
  if (!fs.existsSync(dbPath)) {
    fs.writeFileSync(
      dbPath,
      JSON.stringify(
        {
          users: seedUsers,
          meetings: [],
          invites: [],
          chatMessages: [],
          focusEvents: [],
          moderationEvents: []
        },
        null,
        2
      )
    );
  }
}

function readDb() {
  ensureDb();
  return JSON.parse(fs.readFileSync(dbPath, "utf-8"));
}

function writeDb(db) {
  fs.writeFileSync(dbPath, JSON.stringify(db, null, 2));
}

export function getDb() {
  return readDb();
}

export function getUsers() {
  return readDb().users;
}

export function getUsersPublic() {
  return readDb().users.map(({ passwordHash, ...user }) => user);
}

export function getUserByUsername(username) {
  return readDb().users.find((item) => item.username === username);
}

export function createUser({ username, password }) {
  const db = readDb();
  if (db.users.some((item) => item.username === username)) return null;
  const user = {
    id: nanoid(),
    username,
    name: username.split(".")[0] || username,
    role: "member",
    trustScore: 90,
    status: "offline",
    passwordHash: hashPassword(password)
  };
  db.users.push(user);
  writeDb(db);
  return user;
}

export function verifyUserPassword(username, password) {
  const user = getUserByUsername(username);
  if (!user || !user.passwordHash) return null;
  return verifyPassword(password, user.passwordHash) ? user : null;
}

export function upsertUser(username) {
  const db = readDb();
  let user = db.users.find((item) => item.username === username);
  if (!user) {
    user = {
      id: nanoid(),
      username,
      name: username.split(".")[0] || username,
      role: "member",
      trustScore: 90,
      status: "offline",
      passwordHash: hashPassword(DEFAULT_PASSWORD)
    };
    db.users.push(user);
    writeDb(db);
  }
  return user;
}

export function setUserStatus(username, status) {
  const db = readDb();
  const user = db.users.find((item) => item.username === username);
  if (user) {
    user.status = status;
    writeDb(db);
  }
}

export function createMeeting({ title, hostUsername, invitedUsernames }) {
  const db = readDb();
  const meeting = {
    id: nanoid(10),
    title,
    hostUsername,
    status: "scheduled",
    createdAt: new Date().toISOString()
  };
  db.meetings.unshift(meeting);

  for (const username of invitedUsernames) {
    db.invites.push({
      id: nanoid(10),
      meetingId: meeting.id,
      username,
      status: "pending",
      createdAt: new Date().toISOString()
    });
  }

  writeDb(db);
  return meeting;
}

export function getMeetingsForUser(username) {
  const db = readDb();
  return db.meetings.filter((meeting) => {
    if (meeting.hostUsername === username) return true;
    return db.invites.some((invite) => invite.meetingId === meeting.id && invite.username === username);
  });
}

export function getMeeting(meetingId) {
  const db = readDb();
  return db.meetings.find((meeting) => meeting.id === meetingId);
}

export function getMeetingMembers(meetingId) {
  const db = readDb();
  const meeting = db.meetings.find((item) => item.id === meetingId);
  if (!meeting) return [];
  const invited = db.invites.filter((invite) => invite.meetingId === meetingId).map((invite) => invite.username);
  return [...new Set([meeting.hostUsername, ...invited])];
}

export function userCanJoin(meetingId, username) {
  return getMeetingMembers(meetingId).includes(username);
}

export function acceptInvite(meetingId, username) {
  const db = readDb();
  const invite = db.invites.find((item) => item.meetingId === meetingId && item.username === username);
  if (invite) invite.status = "accepted";
  const meeting = db.meetings.find((item) => item.id === meetingId);
  if (meeting) meeting.status = "live";
  writeDb(db);
  return invite;
}

export function saveChatMessage({ meetingId, username, text, blocked, toxicityScore }) {
  const db = readDb();
  const item = {
    id: nanoid(10),
    meetingId,
    username,
    text,
    blocked,
    toxicityScore,
    createdAt: new Date().toISOString()
  };
  db.chatMessages.push(item);
  writeDb(db);
  return item;
}

export function getChatMessages(meetingId) {
  const db = readDb();
  return db.chatMessages.filter((item) => item.meetingId === meetingId);
}

export function saveModerationEvent({ meetingId, username, source, content, toxicityScore, action }) {
  const db = readDb();
  const event = {
    id: nanoid(10),
    meetingId,
    username,
    source,
    content,
    toxicityScore,
    action,
    createdAt: new Date().toISOString()
  };
  db.moderationEvents.unshift(event);
  writeDb(db);
  return event;
}

export function getModerationEvents(meetingId) {
  const db = readDb();
  return db.moderationEvents.filter((item) => item.meetingId === meetingId);
}

export function saveFocusEvent({ meetingId, username, focusScore, signal }) {
  const db = readDb();
  const event = {
    id: nanoid(10),
    meetingId,
    username,
    focusScore,
    signal,
    createdAt: new Date().toISOString()
  };
  db.focusEvents.unshift(event);
  writeDb(db);
  return event;
}

export function getLatestFocusByMeeting(meetingId) {
  const db = readDb();
  const map = new Map();
  for (const event of db.focusEvents.filter((item) => item.meetingId === meetingId)) {
    if (!map.has(event.username)) map.set(event.username, event);
  }
  return Array.from(map.values());
}
