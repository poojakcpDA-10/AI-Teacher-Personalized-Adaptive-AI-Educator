

import { useEffect, useRef, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useStudent } from "../context/StudentContext";
import { getLesson, startSession, nextTurn, submitAnswer, chatFollowup } from "../api/client";
import LessonRail from "../components/LessonRail";
import TurnBubble from "../components/TurnBubble";
import AvatarStage from "../components/AvatarStage";

export default function TeachingSession() {
  const { lessonId } = useParams();
  const { student } = useStudent();
  const navigate = useNavigate();
  const scrollRef = useRef(null);

  const [lesson, setLesson] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [turns, setTurns] = useState([]);
  const [progress, setProgress] = useState(null);
  const [pendingQuestion, setPendingQuestion] = useState(false);
  const [answerText, setAnswerText] = useState("");
  const [chatText, setChatText] = useState("");
  const [busy, setBusy] = useState(false);
  const [finished, setFinished] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!student) { navigate("/"); return; }
    (async () => {
      try {
        const l = await getLesson(lessonId);
        setLesson(l);
        const { session_id } = await startSession(lessonId);
        setSessionId(session_id);
      } catch {
        setError("Couldn't start the session. Is the backend running?");
      }
    })();
  }, [lessonId, student]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [turns]);

  const advance = async () => {
    if (!sessionId || busy) return;
    setBusy(true);
    setError("");
    try {
      const d = await nextTurn(sessionId);
      setProgress(d.progress);
      if (d.finished) {
        setFinished(true);
      } else {
        setTurns((prev) => [...prev, d.turn]);
        if (d.turn.turn_type === "question" || d.turn.turn_type === "assessment_question"
            || (d.turn.turn_type === "lesson_segment" && d.turn.segments?.some(s => s.label === "Question"))) {
          setPendingQuestion(true);
        }
      }
    } catch {
      setError("Something went wrong generating the next step. Try again.");
    } finally {
      setBusy(false);
    }
  };

  const handleAnswer = async (e) => {
    e.preventDefault();
    if (!answerText.trim() || busy) return;
    setBusy(true);
    setError("");
    try {
      const newTurns = await submitAnswer(sessionId, answerText.trim());
      setTurns((prev) => [...prev, ...newTurns]);
      setAnswerText("");
      setPendingQuestion(false);
    } catch {
      setError("Couldn't submit your answer. Try again.");
    } finally {
      setBusy(false);
    }
  };

  const handleChat = async (e) => {
    e.preventDefault();
    if (!chatText.trim() || busy || pendingQuestion) return;
    setBusy(true);
    try {
      const userTurn = { id: `local-${Date.now()}`, turn_type: "chat", role: "student", content: chatText.trim() };
      setTurns((prev) => [...prev, userTurn]);
      const msg = chatText.trim();
      setChatText("");
      const reply = await chatFollowup(sessionId, msg);
      setTurns((prev) => [...prev, reply]);
    } catch {
      setError("Couldn't send your question.");
    } finally {
      setBusy(false);
    }
  };

  if (!lesson) {
    return <div className="loading-screen">{error || "Preparing your lesson…"}</div>;
  }

  const sections = lesson.plan_json?.sections || [];
  const latestTeacherTurn = [...turns].reverse().find((t) => t.role !== "student") || null;
  // The lesson/evaluation/assessment turns now come back as one baked
  // animated video (avatar + diagram already rendered in). The live
  // client-side avatar is only needed as a fallback for turns with no
  // pre-rendered video, e.g. text-only follow-up chat replies.
  const showLiveAvatar = latestTeacherTurn && !latestTeacherTurn.video_url;

  return (
    <div className="session">
      <div className="session-top">
        <div>
          <div className="hero-eyebrow">{lesson.level} · {lesson.language}</div>
          <h2>{lesson.topic}</h2>
        </div>
        {progress && (
          <div className="progress-figure">{progress.percent_complete}%</div>
        )}
      </div>

      {showLiveAvatar && <AvatarStage turn={latestTeacherTurn} />}

      <div className="card rail-card">
        <LessonRail sections={sections} currentIndex={progress?.current_section_index ?? 0} />
      </div>

      <div className="transcript" ref={scrollRef}>
        {turns.length === 0 && !finished && (
          <div className="empty-hint">
            <p>Your teacher is ready. Click <strong>Begin lesson</strong> to start.</p>
          </div>
        )}
        {turns.map((t) => <TurnBubble key={t.id} turn={t} />)}

        {finished && (
          <div className="finish-card card">
            <h3>🎉 Lesson complete</h3>
            <p>Nice work! Your learning report is ready.</p>
            <button className="btn btn-accent" onClick={() => navigate(`/report/${sessionId}`)}>
              View my report →
            </button>
          </div>
        )}
      </div>

      {error && <p className="session-error">{error}</p>}

      {!finished && !pendingQuestion && (
        <div className="session-controls">
          <button className="btn btn-primary" onClick={advance} disabled={busy}>
            {busy ? "Thinking…" : turns.length === 0 ? "Begin lesson →" : "Continue →"}
          </button>
          <form className="chat-form" onSubmit={handleChat}>
            <input className="field" placeholder="Ask a follow-up question…" value={chatText}
                   onChange={(e) => setChatText(e.target.value)} disabled={busy} />
            <button className="btn btn-ghost" type="submit" disabled={busy || !chatText.trim()}>Ask</button>
          </form>
        </div>
      )}

      {!finished && pendingQuestion && (
        <form className="answer-form" onSubmit={handleAnswer}>
          <input className="field" placeholder="Type your answer…" value={answerText}
                 onChange={(e) => setAnswerText(e.target.value)} autoFocus disabled={busy} />
          <button className="btn btn-accent" type="submit" disabled={busy || !answerText.trim()}>
            {busy ? "Checking…" : "Submit answer"}
          </button>
        </form>
      )}

      <style>{`
        .loading-screen { display: flex; align-items: center; justify-content: center; min-height: 100vh; color: var(--ink-faint); }
        .session { max-width: 820px; margin: 0 auto; padding: 32px 24px 24px; display: flex; flex-direction: column; height: 100vh; }
        .session-top { display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 16px; }
        .hero-eyebrow { font-size: 12px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; color: var(--accent-dark); }
        .session-top h2 { font-size: 24px; margin: 2px 0 0; }
        .progress-figure {
          font-family: var(--font-mono); font-size: 20px; font-weight: 600;
          color: var(--brand-dark-solid); background: var(--brand-tint);
          padding: 8px 14px; border-radius: 12px;
        }
        .rail-card { padding: 8px 16px; margin-bottom: 18px; }
        .transcript { flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 20px; padding: 8px 2px 20px; }
        .empty-hint { text-align: center; padding: 40px 20px; color: var(--ink-faint); }
        .finish-card { padding: 28px; text-align: center; }
        .finish-card h3 { font-size: 22px; }
        .session-error { color: var(--error); font-size: 13px; margin: 8px 0 0; }
        .session-controls { display: flex; gap: 12px; padding-top: 14px; border-top: 1px solid var(--border); flex-wrap: wrap; }
        .chat-form { display: flex; gap: 8px; flex: 1; min-width: 220px; }
        .answer-form { display: flex; gap: 10px; padding-top: 14px; border-top: 1px solid var(--border); }
        .answer-form .field { flex: 1; }
      `}</style>
    </div>
  );
}