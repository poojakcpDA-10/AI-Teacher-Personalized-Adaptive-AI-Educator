import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useStudent } from "../context/StudentContext";
import { createStudent, listStudents } from "../api/client";

const LANGS = ["English", "Hindi", "Hinglish", "Tamil", "Telugu", "Bengali", "Marathi"];
const LEVELS = ["Beginner", "Intermediate", "Advanced"];

export default function Onboarding() {
  const { setStudent } = useStudent();
  const navigate = useNavigate();
  const [existing, setExisting] = useState([]);
  const [mode, setMode] = useState("choose");
  const [name, setName] = useState("");
  const [language, setLanguage] = useState("English");
  const [level, setLevel] = useState("Beginner");
  const [goals, setGoals] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    listStudents().then(setExisting).catch(() => {});
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    setLoading(true);
    setError("");
    try {
      const student = await createStudent({
        name: name.trim(), preferred_language: language, current_level: level, learning_goals: goals,
      });
      setStudent(student);
      navigate("/new-lesson");
    } catch (err) {
      setError("Couldn't create the profile. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const pick = (s) => {
    setStudent(s);
    navigate("/dashboard");
  };

  return (
    <div className="onboard">
      <div className="onboard-hero">
        <div className="hero-eyebrow">Welcome to</div>
        <h1>The AI Teacher</h1>
        <p className="hero-sub">
          A patient, adaptive teacher that plans your lesson, explains it in
          your language, checks your understanding, and adjusts when you're stuck.
        </p>
      </div>

      <div className="onboard-panels">
        {existing.length > 0 && mode === "choose" && (
          <div className="card panel">
            <h3>Continue as</h3>
            <div className="student-list">
              {existing.map((s) => (
                <button key={s.id} className="student-row" onClick={() => pick(s)}>
                  <span className="student-row-avatar">{s.name[0]?.toUpperCase()}</span>
                  <span>
                    <div className="student-row-name">{s.name}</div>
                    <div className="student-row-meta">{s.current_level} · {s.preferred_language}</div>
                  </span>
                </button>
              ))}
            </div>
            <button className="btn btn-ghost" style={{marginTop: 14}} onClick={() => setMode("new")}>
              + New learner profile
            </button>
          </div>
        )}

        {(mode === "new" || existing.length === 0) && (
          <form className="card panel" onSubmit={handleCreate}>
            <h3>{existing.length > 0 ? "New learner profile" : "Create your learner profile"}</h3>
            <label className="label">Name</label>
            <input className="field" value={name} onChange={(e) => setName(e.target.value)}
                   placeholder="e.g. Aarav" required style={{marginTop: 6, marginBottom: 16}} />

            <label className="label">Current level</label>
            <div className="chip-row">
              {LEVELS.map((l) => (
                <button type="button" key={l} className={`chip ${level === l ? "chip--active" : ""}`}
                        onClick={() => setLevel(l)}>{l}</button>
              ))}
            </div>

            <label className="label" style={{marginTop: 16, display: "block"}}>Preferred language</label>
            <select className="field" value={language} onChange={(e) => setLanguage(e.target.value)} style={{marginTop: 6}}>
              {LANGS.map((l) => <option key={l} value={l}>{l}</option>)}
            </select>

            <label className="label" style={{marginTop: 16, display: "block"}}>Learning goals (optional)</label>
            <textarea className="field" rows={2} value={goals} onChange={(e) => setGoals(e.target.value)}
                      placeholder="e.g. Preparing for Class 10 board exams"
                      style={{marginTop: 6, resize: "vertical"}} />

            {error && <p style={{color: "var(--error)", fontSize: 13}}>{error}</p>}

            <button className="btn btn-primary" type="submit" disabled={loading} style={{marginTop: 18, width: "100%"}}>
              {loading ? "Creating…" : "Start learning →"}
            </button>
            {existing.length > 0 && (
              <button type="button" className="btn btn-ghost" style={{marginTop: 8, width: "100%"}}
                      onClick={() => setMode("choose")}>
                ← Back to profiles
              </button>
            )}
          </form>
        )}
      </div>

      <style>{`
        .onboard {
          min-height: 100vh;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          padding: 60px 20px;
          background: radial-gradient(circle at 20% 15%, var(--brand-tint) 0%, var(--paper) 45%);
        }
        .onboard-hero { max-width: 560px; text-align: center; margin-bottom: 40px; }
        .hero-eyebrow {
          font-size: 13px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase;
          color: var(--accent-dark); margin-bottom: 6px;
        }
        .onboard-hero h1 { font-size: 44px; margin-bottom: 14px; }
        .hero-sub { font-size: 16px; color: var(--ink-soft); }
        .onboard-panels { width: 100%; max-width: 420px; }
        .panel { padding: 28px; }
        .student-list { display: flex; flex-direction: column; gap: 8px; margin-top: 14px; }
        .student-row {
          display: flex; align-items: center; gap: 12px;
          padding: 10px 12px; border-radius: var(--radius-sm);
          border: 1px solid var(--border); background: var(--surface-sunken);
          text-align: left; transition: border-color 0.12s ease;
        }
        .student-row:hover { border-color: var(--brand); }
        .student-row-avatar {
          width: 36px; height: 36px; border-radius: 50%; background: var(--brand);
          color: white; display: flex; align-items: center; justify-content: center;
          font-weight: 600; font-family: var(--font-display); flex-shrink: 0;
        }
        .student-row-name { font-weight: 600; font-size: 14px; }
        .student-row-meta { font-size: 12px; color: var(--ink-faint); }
        .chip-row { display: flex; gap: 8px; margin-top: 6px; }
        .chip {
          padding: 7px 14px; border-radius: 999px; border: 1.5px solid var(--border);
          background: var(--surface-sunken); font-size: 13px; font-weight: 500; color: var(--ink-soft);
        }
        .chip--active { background: var(--brand); border-color: var(--brand); color: white; }
      `}</style>
    </div>
  );
}
