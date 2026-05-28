import { useEffect, useRef, useState } from "react";

export function useFocusReporter({ socket, meetingId, username, enabled }) {
  const [focusScore, setFocusScore] = useState(100);
  const [signal, setSignal] = useState("normal_attention");
  const lastActivityRef = useRef(Date.now());

  useEffect(() => {
    const markActivity = () => {
      lastActivityRef.current = Date.now();
    };

    window.addEventListener("mousemove", markActivity);
    window.addEventListener("keydown", markActivity);
    window.addEventListener("click", markActivity);

    return () => {
      window.removeEventListener("mousemove", markActivity);
      window.removeEventListener("keydown", markActivity);
      window.removeEventListener("click", markActivity);
    };
  }, []);

  useEffect(() => {
    if (!enabled || !socket || !meetingId || !username) return;

    const interval = setInterval(() => {
      const inactiveMs = Date.now() - lastActivityRef.current;
      const hidden = document.hidden;

      let nextScore = 92;
      let nextSignal = "normal_attention";

      if (hidden) {
        nextScore = 20;
        nextSignal = "tab_not_visible";
      } else if (inactiveMs > 30000) {
        nextScore = 35;
        nextSignal = "inactive_30s";
      } else if (inactiveMs > 15000) {
        nextScore = 55;
        nextSignal = "low_activity";
      }

      // Browser FaceDetector is not universally supported.
      // Codex can upgrade this hook with MediaPipe Face Landmarker.
      setFocusScore(nextScore);
      setSignal(nextSignal);

      socket.emit("focus:report", {
        meetingId,
        username,
        focusScore: nextScore,
        signal: nextSignal
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [socket, meetingId, username, enabled]);

  return { focusScore, signal };
}
