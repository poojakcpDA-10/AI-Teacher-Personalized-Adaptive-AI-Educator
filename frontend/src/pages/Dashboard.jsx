import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useStudent } from "../context/StudentContext";
import { getProfile, listStudentLessons, listStudentAssessments } from "../api/client";

export default function Dashboard() {
  const { student } = useStudent();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [lessons, setLessons] = useState([]);
  const [assessments, setAssessments] = useState([]);

  useEffect(() => {
    if (!student) { navigate("/"); return; }
    getProfile(student.id).then(setProfile).catch(() => {});
    listStudentLessons(student.id).then(setLessons).catch(() => {});
    listStudentAssessments(student.id).then(setAssessments).catch(() => {});
  }, [student]);

  if (!student) return null;

  return (
    <div className="dash">
      <div className="dash-header">
        <div>
          <div className="hero-eyebrow">Welcome back</div>
          <h1>{student.name}'s learning space</h1>
        </div>
        <Link to="/new-lesson" className="btn btn-accent">+ New lesson</Link>
      </div>

      <div className="dash-grid">
        <div className="card panel">
          <h3>Learner profile</h3>
          <div className="profile-row">
            <span className="label">Level</span>
            <span className="pill pill-brand">{student.current_level}</span>
          </div>
          <div className="profile-row">
            <span className="label">Language</span>
            <span className="pill pill-neutral">{student.preferred_language}</span>
          </div>

          <div className="concept-block">
            <div className="label">Strong concepts</div>
            {profile?.concepts_mastered?.length ? (
              <div className="tag-cloud">
                {profile.concepts_mastered.map((c) => (
                  <span key={c} className="tag tag-success">{c}</span>
                ))}
              </div>
            ) : <p className="muted">Nothing recorded yet — complete a lesson assessment.</p>}
          </div>

          <div className="concept-block">
            <div className="label">Needs revision</div>
            {profile?.weak_concepts?.length ? (
              <div className="tag-cloud">
                {profile.weak_concepts.map((c) => (
                  <span key={c} className="tag tag-warning">{c}</span>
                ))}
              </div>
            ) : <p className="muted">No weak areas flagged yet.</p>}
          </div>
        </div>

        <div className="card panel">
          <h3>Lesson history</h3>
          {lessons.length === 0 && <p className="muted">No lessons yet. Start your first one!</p>}
          <div className="list">
            {lessons.map((l) => (
              <div key={l.id} className="list-row">
                <div>
                  <div className="list-row-title">{l.topic}</div>
                  <div className="list-row-meta">{l.level} · {l.language} · {l.time_minutes} min</div>
                </div>
                <span className={`pill pill-status pill-status--${l.status}`}>{l.status.replace("_", " ")}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card panel">
          <h3>Past assessments</h3>
          {assessments.length === 0 && <p className="muted">Complete a lesson to see your first report here.</p>}
          <div className="list">
            {assessments.map((a) => (
              <div key={a.id} className="list-row">
                <div>
                  <div className="list-row-title">{a.topic}</div>
                  <div className="list-row-meta">Next: {a.next_topic || "—"}</div>
                </div>
                <span className="score-badge">{a.score_percent}%</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <style>{`
        .dash { max-width: 980px; margin: 0 auto; padding: 40px 32px 60px; }
        .dash-header { display: flex; align-items: flex-end; justify-content: space-between; margin-bottom: 28px; flex-wrap: wrap; gap: 16px; }
        .hero-eyebrow { font-size: 12.5px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent-dark); margin-bottom: 4px; }
        .dash-header h1 { font-size: 30px; margin: 0; }
        .dash-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .dash-grid .panel:first-child { grid-row: span 2; }
        .panel { padding: 24px; }
        .profile-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--border); }
        .pill-brand { background: var(--brand-tint); color: var(--brand-dark-solid); }
        .pill-neutral { background: var(--paper-alt); color: var(--ink-soft); }
        .concept-block { margin-top: 18px; }
        .tag-cloud { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
        .tag { padding: 5px 12px; border-radius: 999px; font-size: 12.5px; font-weight: 500; }
        .tag-success { background: var(--success-tint); color: var(--success); }
        .tag-warning { background: var(--warning-tint); color: var(--warning); }
        .muted { color: var(--ink-faint); font-size: 13.5px; margin-top: 6px; }
        .list { display: flex; flex-direction: column; gap: 4px; margin-top: 10px; }
        .list-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 4px; border-bottom: 1px solid var(--border); }
        .list-row:last-child { border-bottom: none; }
        .list-row-title { font-weight: 600; font-size: 14px; }
        .list-row-meta { font-size: 12px; color: var(--ink-faint); margin-top: 2px; }
        .pill-status { text-transform: capitalize; }
        .pill-status--completed { background: var(--success-tint); color: var(--success); }
        .pill-status--in_progress { background: var(--accent-tint); color: var(--accent-dark); }
        .pill-status--planned { background: var(--paper-alt); color: var(--ink-faint); }
        .score-badge {
          font-family: var(--font-mono); font-weight: 600; font-size: 15px;
          color: var(--brand-dark-solid); background: var(--brand-tint);
          padding: 4px 10px; border-radius: 8px;
        }
        @media (max-width: 780px) {
          .dash-grid { grid-template-columns: 1fr; }
          .dash-grid .panel:first-child { grid-row: auto; }
        }
      `}</style>
    </div>
  );
}
