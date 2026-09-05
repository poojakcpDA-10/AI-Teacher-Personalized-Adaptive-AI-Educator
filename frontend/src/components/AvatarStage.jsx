
import { useEffect, useRef, useState } from "react";
import { mediaUrl } from "../api/client";

// Small per-turn-type expression tweaks so the avatar visibly reacts to
// what's happening, not just moves its mouth.
const EXPRESSION = {
  question: { eyebrow: 8 },
  assessment_question: { eyebrow: 8 },
  misconception: { frown: true },
  evaluation: { smile: true },
};

export default function AvatarStage({ turn }) {
  const audioRef = useRef(null);
  const audioCtxRef = useRef(null);
  const rafRef = useRef(null);
  const fallbackTimerRef = useRef(null);
  const lastTurnIdRef = useRef(null);

  const [mouthOpen, setMouthOpen] = useState(0);
  const [speaking, setSpeaking] = useState(false);
  const [blinking, setBlinking] = useState(false);

  // Idle blink loop — runs the whole time, independent of speech.
  useEffect(() => {
    let cancelled = false;
    let timeoutId;
    const scheduleBlink = () => {
      const delay = 2400 + Math.random() * 3200;
      timeoutId = setTimeout(() => {
        if (cancelled) return;
        setBlinking(true);
        setTimeout(() => !cancelled && setBlinking(false), 150);
        scheduleBlink();
      }, delay);
    };
    scheduleBlink();
    return () => { cancelled = true; clearTimeout(timeoutId); };
  }, []);

  const cleanupAudio = () => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (fallbackTimerRef.current) clearInterval(fallbackTimerRef.current);
    rafRef.current = null;
    fallbackTimerRef.current = null;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.onended = null;
      audioRef.current = null;
    }
    setSpeaking(false);
    setMouthOpen(0);
  };

  const simulateTalkingForDuration = (durationSec) => {
    setSpeaking(true);
    const start = Date.now();
    fallbackTimerRef.current = setInterval(() => {
      const elapsed = (Date.now() - start) / 1000;
      if (elapsed > durationSec) {
        cleanupAudio();
        return;
      }
      setMouthOpen(Math.random() * 0.75 + 0.1);
    }, 110);
  };

  const playWithAnalyser = (url) => {
    const audio = new Audio(url);
    audio.crossOrigin = "anonymous";
    audioRef.current = audio;
    setSpeaking(true);

    try {
      if (!audioCtxRef.current) {
        const Ctx = window.AudioContext || window.webkitAudioContext;
        audioCtxRef.current = new Ctx();
      }
      const ctx = audioCtxRef.current;
      if (ctx.state === "suspended") ctx.resume();

      const source = ctx.createMediaElementSource(audio);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);
      analyser.connect(ctx.destination);

      const data = new Uint8Array(analyser.frequencyBinCount);
      const tick = () => {
        analyser.getByteTimeDomainData(data);
        let sum = 0;
        for (let i = 0; i < data.length; i++) {
          const v = (data[i] - 128) / 128;
          sum += v * v;
        }
        const rms = Math.sqrt(sum / data.length);
        setMouthOpen(Math.min(1, rms * 6));
        rafRef.current = requestAnimationFrame(tick);
      };
      tick();
    } catch {
      // Web Audio API unavailable/blocked — audio still plays normally,
      // just fall back to a timed mouth animation instead of true amplitude sync.
      simulateTalkingForDuration(4);
    }

    audio.play().catch(() => cleanupAudio());
    audio.onended = () => cleanupAudio();
  };

  useEffect(() => {
    if (!turn || turn.id === lastTurnIdRef.current) return;
    lastTurnIdRef.current = turn.id;
    cleanupAudio();

    const url = turn.audio_url ? mediaUrl(turn.audio_url) : null;
    if (url) {
      playWithAnalyser(url);
    } else if (turn.content) {
      const duration = Math.min(14, Math.max(2, turn.content.length / 14));
      simulateTalkingForDuration(duration);
    }
    return cleanupAudio;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [turn]);

  useEffect(() => cleanupAudio, []); // cleanup on unmount

  const expr = EXPRESSION[turn?.turn_type] || {};
  const browY = expr.frown ? 96 : 88 - (expr.eyebrow || 0);

  return (
    <div className="avatar-stage">
      <div className="avatar-frame">
        <svg viewBox="0 0 240 240" className="avatar-svg">
          <g className="avatar-float">
            <path d="M40 240 Q120 170 200 240 Z" fill="#3B82F6" />
            <ellipse cx="120" cy="118" rx="66" ry="72" fill="#F4C9A0" />
            <path d="M56 100 Q60 42 120 40 Q180 42 184 100 Q150 80 120 80 Q90 80 56 100 Z" fill="#4B3621" />
            <rect x="82" y={browY} width="30" height="7" rx="3.5" fill="#4B3621"
                  transform={expr.eyebrow ? "rotate(-8 97 90)" : ""} />
            <rect x="128" y={browY} width="30" height="7" rx="3.5" fill="#4B3621"
                  transform={expr.eyebrow ? "rotate(8 143 90)" : ""} />
            <ellipse cx="97" cy="112" rx="9" ry={blinking ? 1 : 9} fill="#2B2B2B" />
            <ellipse cx="143" cy="112" rx="9" ry={blinking ? 1 : 9} fill="#2B2B2B" />
            {expr.smile ? (
              <path d="M96 148 Q120 172 144 148" stroke="#8B4A3B" strokeWidth="6" fill="none" strokeLinecap="round" />
            ) : (
              <ellipse cx="120" cy="158" rx="22" ry={4 + mouthOpen * 24} fill="#8B4A3B" />
            )}
          </g>
        </svg>
        {speaking && <div className="avatar-pulse" />}
      </div>

      <style>{`
        .avatar-stage { display: flex; justify-content: center; padding: 4px 0 2px; }
        .avatar-frame { position: relative; width: 128px; height: 128px; }
        .avatar-svg { width: 100%; height: 100%; display: block; }
        .avatar-float { animation: avatarFloat 3s ease-in-out infinite; transform-origin: center; }
        @keyframes avatarFloat {
          0%, 100% { transform: translateY(0); }
          50% { transform: translateY(-3px); }
        }
        .avatar-pulse {
          position: absolute; inset: -6px; border-radius: 50%;
          border: 3px solid var(--brand, #3B82F6); opacity: 0.55;
          animation: avatarPulse 1.1s ease-out infinite;
          pointer-events: none;
        }
        @keyframes avatarPulse {
          0% { transform: scale(0.92); opacity: 0.6; }
          100% { transform: scale(1.18); opacity: 0; }
        }
      `}</style>
    </div>
  );
}