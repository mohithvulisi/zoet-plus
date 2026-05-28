import { AlertTriangle, Ban, Eye, Mic, MicOff, Send, Video, VideoOff } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { useFocusReporter } from "../hooks/useFocusReporter";

const rtcConfig = createRtcConfig();

function createRtcConfig() {
  const stunUrls = (import.meta.env.VITE_STUN_URL || "stun:stun.l.google.com:19302")
    .split(",")
    .map((url) => url.trim())
    .filter(Boolean);

  const iceServers = stunUrls.map((urls) => ({ urls }));

  const turnUrls = (import.meta.env.VITE_TURN_URL || "")
    .split(",")
    .map((url) => url.trim())
    .filter(Boolean);
  const turnUsername = import.meta.env.VITE_TURN_USERNAME;
  const turnCredential = import.meta.env.VITE_TURN_CREDENTIAL;

  if (turnUrls.length && turnUsername && turnCredential) {
    iceServers.push({
      urls: turnUrls,
      username: turnUsername,
      credential: turnCredential
    });
  }

  return { iceServers };
}

export default function MeetingRoom({ meetingId, currentUser, socket, onLeave }) {
  const [meeting, setMeeting] = useState(null);
  const [members, setMembers] = useState([]);
  const [chat, setChat] = useState([]);
  const [text, setText] = useState("");
  const [moderationEvents, setModerationEvents] = useState([]);
  const [focusEvents, setFocusEvents] = useState([]);
  const [alert, setAlert] = useState("");
  const [muted, setMuted] = useState(false);
  const [cameraOff, setCameraOff] = useState(false);
  const [remoteStreams, setRemoteStreams] = useState([]);
  const [joinError, setJoinError] = useState("");

  const localVideoRef = useRef(null);
  const localStreamRef = useRef(null);
  const peersRef = useRef(new Map());

  const { focusScore, signal } = useFocusReporter({
    socket,
    meetingId,
    username: currentUser.username,
    enabled: Boolean(meetingId)
  });

  useEffect(() => {
    let mounted = true;
    api(`/api/meetings/${meetingId}`).then((data) => {
      if (!mounted) return;
      setMeeting(data.meeting);
      setMembers(data.members);
      setChat(data.chatMessages.filter((m) => !m.blocked));
      setModerationEvents(data.moderationEvents);
      setFocusEvents(data.focusEvents);
    });
    return () => { mounted = false; };
  }, [meetingId]);

  useEffect(() => {
    async function startMediaAndJoin() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
        localStreamRef.current = stream;
        if (localVideoRef.current) localVideoRef.current.srcObject = stream;
      } catch (error) {
        setJoinError("Camera/microphone permission failed. You can still test chat and focus simulation.");
      }

      socket.emit("meeting:join", { meetingId }, async (response) => {
        if (!response?.ok) {
          setJoinError(response?.error || "Could not join meeting.");
          return;
        }

        for (const participant of response.participants || []) {
          await createPeer(participant.socketId, true);
        }
      });
    }

    startMediaAndJoin();

    const onParticipantJoined = async ({ socketId }) => {
      await createPeer(socketId, false);
    };

    const onParticipantLeft = ({ socketId }) => {
      const peer = peersRef.current.get(socketId);
      if (peer) peer.close();
      peersRef.current.delete(socketId);
      setRemoteStreams((prev) => prev.filter((item) => item.socketId !== socketId));
    };

    const onOffer = async ({ from, offer }) => {
      const peer = await createPeer(from, false);
      await peer.setRemoteDescription(new RTCSessionDescription(offer));
      const answer = await peer.createAnswer();
      await peer.setLocalDescription(answer);
      socket.emit("webrtc:answer", { to: from, answer });
    };

    const onAnswer = async ({ from, answer }) => {
      const peer = peersRef.current.get(from);
      if (peer) await peer.setRemoteDescription(new RTCSessionDescription(answer));
    };

    const onIce = async ({ from, candidate }) => {
      const peer = peersRef.current.get(from);
      if (peer && candidate) await peer.addIceCandidate(new RTCIceCandidate(candidate));
    };

    const onChat = (message) => setChat((prev) => [...prev, message]);
    const onModeration = (event) => setModerationEvents((prev) => [event, ...prev]);
    const onFocus = (events) => setFocusEvents(events);
    const onHostAlert = (payload) => setAlert(payload.message);

    socket.on("participant:joined", onParticipantJoined);
    socket.on("participant:left", onParticipantLeft);
    socket.on("webrtc:offer", onOffer);
    socket.on("webrtc:answer", onAnswer);
    socket.on("webrtc:ice-candidate", onIce);
    socket.on("chat:new", onChat);
    socket.on("moderation:new", onModeration);
    socket.on("focus:update", onFocus);
    socket.on("host:attention-alert", onHostAlert);

    return () => {
      socket.off("participant:joined", onParticipantJoined);
      socket.off("participant:left", onParticipantLeft);
      socket.off("webrtc:offer", onOffer);
      socket.off("webrtc:answer", onAnswer);
      socket.off("webrtc:ice-candidate", onIce);
      socket.off("chat:new", onChat);
      socket.off("moderation:new", onModeration);
      socket.off("focus:update", onFocus);
      socket.off("host:attention-alert", onHostAlert);

      for (const peer of peersRef.current.values()) peer.close();
      peersRef.current.clear();

      if (localStreamRef.current) {
        for (const track of localStreamRef.current.getTracks()) track.stop();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [meetingId, currentUser.username, socket]);

  async function createPeer(socketId, initiator) {
    if (peersRef.current.has(socketId)) return peersRef.current.get(socketId);

    const peer = new RTCPeerConnection(rtcConfig);
    peersRef.current.set(socketId, peer);

    if (localStreamRef.current) {
      for (const track of localStreamRef.current.getTracks()) {
        peer.addTrack(track, localStreamRef.current);
      }
    }

    peer.onicecandidate = (event) => {
      if (event.candidate) {
        socket.emit("webrtc:ice-candidate", { to: socketId, candidate: event.candidate });
      }
    };

    peer.ontrack = (event) => {
      const [stream] = event.streams;
      setRemoteStreams((prev) => {
        if (prev.some((item) => item.socketId === socketId)) return prev;
        return [...prev, { socketId, stream }];
      });
    };

    if (initiator) {
      const offer = await peer.createOffer();
      await peer.setLocalDescription(offer);
      socket.emit("webrtc:offer", { to: socketId, offer });
    }

    return peer;
  }

  function toggleMute() {
    const next = !muted;
    setMuted(next);
    localStreamRef.current?.getAudioTracks().forEach((track) => {
      track.enabled = !next;
    });
  }

  function toggleCamera() {
    const next = !cameraOff;
    setCameraOff(next);
    localStreamRef.current?.getVideoTracks().forEach((track) => {
      track.enabled = !next;
    });
  }

  function sendChat(e) {
    e.preventDefault();
    if (!text.trim()) return;

    socket.emit("chat:send", {
      meetingId,
      username: currentUser.username,
      text
    }, (response) => {
      if (response?.blocked) {
        setAlert(`Your message was blocked. Action: ${response.result.action}`);
      }
      setText("");
    });
  }

  return (
    <div className="room-layout">
      <main className="room-main">
        <div className="room-header">
          <div>
            <button className="ghost" onClick={onLeave}>← Dashboard</button>
            <h1>{meeting?.title || "Meeting room"}</h1>
            <p>Only invited users can join: {members.map((m) => `@${m}`).join(", ")}</p>
          </div>
          <div className="focus-pill">
            <Eye size={17} /> Your focus: {focusScore}% · {signal}
          </div>
        </div>

        {joinError ? <div className="notice warning">{joinError}</div> : null}
        {alert ? <div className="notice danger"><AlertTriangle size={18} /> {alert}</div> : null}

        <div className="video-grid">
          <div className="video-tile">
            <video ref={localVideoRef} autoPlay muted playsInline />
            <span>@{currentUser.username} — you</span>
          </div>
          {remoteStreams.map((item) => (
            <RemoteVideo key={item.socketId} stream={item.stream} label={item.socketId.slice(0, 6)} />
          ))}
        </div>

        <div className="call-controls">
          <button onClick={toggleMute}>{muted ? <MicOff /> : <Mic />} {muted ? "Unmute" : "Mute"}</button>
          <button onClick={toggleCamera}>{cameraOff ? <VideoOff /> : <Video />} {cameraOff ? "Camera on" : "Camera off"}</button>
        </div>

        <section className="panel">
          <h2>Focus dashboard</h2>
          <div className="focus-grid">
            {focusEvents.map((event) => (
              <div className="focus-card" key={event.username}>
                <strong>@{event.username}</strong>
                <div className="bar"><span style={{ width: `${event.focusScore}%` }} /></div>
                <small>{event.focusScore}% · {event.signal}</small>
              </div>
            ))}
          </div>
        </section>
      </main>

      <aside className="room-sidebar">
        <section className="panel chat-panel">
          <h2>Meeting chat</h2>
          <div className="chat-list">
            {chat.map((item) => (
              <div className="chat-bubble" key={item.id}>
                <b>@{item.username}</b>
                <p>{item.text}</p>
              </div>
            ))}
          </div>
          <form className="chat-form" onSubmit={sendChat}>
            <input value={text} onChange={(e) => setText(e.target.value)} placeholder="Type message..." />
            <button><Send size={17} /></button>
          </form>
        </section>

        <section className="panel">
          <h2><Ban size={18} /> Moderation</h2>
          <div className="moderation-list">
            {moderationEvents.map((event) => (
              <div className="moderation-item" key={event.id}>
                <b>@{event.username}</b>
                <p>{event.content}</p>
                <small>{event.toxicityScore}% · {event.action}</small>
              </div>
            ))}
            {!moderationEvents.length ? <p className="muted">No blocked content yet.</p> : null}
          </div>
        </section>
      </aside>
    </div>
  );
}

function RemoteVideo({ stream, label }) {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) ref.current.srcObject = stream;
  }, [stream]);

  return (
    <div className="video-tile">
      <video ref={ref} autoPlay playsInline />
      <span>Remote {label}</span>
    </div>
  );
}
