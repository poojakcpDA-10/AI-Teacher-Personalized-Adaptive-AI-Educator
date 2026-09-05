import { useEffect, useState } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { useStudent } from "../context/StudentContext";
import { getAssessment } from "../api/client";

export default function Report() {
  const { sessionId } = useParams();
  const { student } = useStudent();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!student) { navigate("/"); return; }
    getAssessment(sessionId).then(setReport).catch(() => setError("Report not ready yet."));
  }, [sessionId, student]);

  if (error) return <div className="loading-screen">{error}</div>;
  if (!report) return <div className="loading-screen">Loading your report…</div>;

  const scoreColor = report.score_percent >= 70 ? "var(--success)" : report.score_percent >= 40 ? "var(--warning)" : "var(--error)";

  return (
    <div className="report">
      <div className="report-header">
        <div className="hero-eyebrow">Learning report</div>
        <h1>{report.topic}</h1>
      </div>

      <div className="score-hero card">
        <div className="score-ring" style={{ "--score-color": scoreColor }}>
          <span>{report.score_percent}%</span>
        </div>
        <div>
          <div className="score-label">Overall score</div>
          <p>Based on your answers during the lesson and final assessment questions.</p>
        </div>
      </div>

      <div className="report-grid">
        <div className="card panel">
          <h3>✓ Strong areas</h3>
          {report.strong_areas.length ? (
            <ul className="area-list">
              {report.strong_areas.map((a) => <li key={a} className="area-item area-item--good">{a}</li>)}
            </ul>
          ) : <p className="muted">Keep practicing — no strong areas confirmed yet.</p>}
        </div>

        <div className="card panel">
          <h3>⚠ Needs improvement</h3>
          {report.weak_areas.length ? (
            <ul className="area-list">
              {report.weak_areas.map((a) => <li key={a} className="area-item area-item--warn">{a}</li>)}
            </ul>
          ) : <p className="muted">No weak areas flagged this lesson.</p>}
        </div>

        {report.misconceptions.length > 0 && (
          <div className="card panel full-span">
            <h3>Misconceptions identified</h3>
            <ul className="area-list">
              {report.misconceptions.map((m, i) => <li key={i} className="area-item">{m}</li>)}
            </ul>
          </div>
        )}

        <div className="card panel full-span">
          <h3>Recommended next steps</h3>
          <ul className="area-list">
            {report.recommended_revision.map((r, i) => <li key={i} className="area-item area-item--action">{r}</li>)}
          </ul>
          {report.next_topic && (
            <div className="next-topic">
              <span className="label">Suggested next topic</span>
              <div className="next-topic-name">{report.next_topic}</div>
            </div>
          )}
        </div>
      </div>

      <div className="report-actions">
        <Link to="/new-lesson" className="btn btn-primary">Start another lesson</Link>
        <Link to="/dashboard" className="btn btn-ghost">Back to dashboard</Link>
      </div>

      <style>{`
        .loading-screen { display: flex; align-items: center; justify-content: center; min-height: 100vh; color: var(--ink-faint); }
        .report { max-width: 820px; margin: 0 auto; padding: 44px 24px 60px; }
        .report-header { margin-bottom: 24px; }
        .hero-eyebrow { font-size: 12.5px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent-dark); }
        .report-header h1 { font-size: 30px; margin-top: 4px; }
        .score-hero { display: flex; align-items: center; gap: 22px; padding: 26px; margin-bottom: 22px; }
        .score-ring {
          width: 84px; height: 84px; border-radius: 50%;
          border: 6px solid var(--score-color);
          display: flex; align-items: center; justify-content: center;
          font-family: var(--font-mono); font-weight: 700; font-size: 18px;
          color: var(--score-color); flex-shrink: 0;
        }
        .score-label { font-weight: 600; font-size: 15px; margin-bottom: 4px; }
        .report-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
        .full-span { grid-column: 1 / -1; }
        .panel { padding: 24px; }
        .area-list { list-style: none; padding: 0; margin: 12px 0 0; display: flex; flex-direction: column; gap: 8px; }
        .area-item { padding: 10px 14px; border-radius: var(--radius-sm); font-size: 14px; background: var(--paper-alt); }
        .area-item--good { background: var(--success-tint); color: var(--success); font-weight: 500; }
        .area-item--warn { background: var(--warning-tint); color: var(--warning); font-weight: 500; }
        .area-item--action { background: var(--brand-tint); color: var(--brand-dark-solid); }
        .muted { color: var(--ink-faint); font-size: 13.5px; }
        .next-topic { margin-top: 18px; padding-top: 16px; border-top: 1px solid var(--border); }
        .next-topic-name { font-family: var(--font-display); font-size: 19px; font-weight: 600; margin-top: 4px; }
        .report-actions { display: flex; gap: 12px; margin-top: 28px; }
        @media (max-width: 700px) { .report-grid { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
}
