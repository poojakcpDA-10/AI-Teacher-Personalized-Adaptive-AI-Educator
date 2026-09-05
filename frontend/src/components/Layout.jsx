import { NavLink, useNavigate } from "react-router-dom";
import { useStudent } from "../context/StudentContext";

export default function Layout({ children }) {
  const { student, setStudent } = useStudent();
  const navigate = useNavigate();

  const switchStudent = () => {
    setStudent(null);
    navigate("/");
  };

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand-mark">
          <span className="brand-glyph">✎</span>
          <span className="brand-word">AI Teacher</span>
        </div>

        {student && (
          <nav className="nav">
            <NavLink to="/dashboard" className={({isActive}) => `nav-link ${isActive ? "active" : ""}`}>
              Dashboard
            </NavLink>
            <NavLink to="/new-lesson" className={({isActive}) => `nav-link ${isActive ? "active" : ""}`}>
              New Lesson
            </NavLink>
          </nav>
        )}

        <div className="sidebar-footer">
          {student && (
            <div className="student-chip">
              <div className="student-avatar">{student.name?.[0]?.toUpperCase() || "?"}</div>
              <div className="student-chip-info">
                <div className="student-chip-name">{student.name}</div>
                <button className="link-btn" onClick={switchStudent}>Switch learner</button>
              </div>
            </div>
          )}
        </div>
      </aside>
      <main className="main-area">{children}</main>

      <style>{`
        .shell {
          display: grid;
          grid-template-columns: 240px 1fr;
          min-height: 100vh;
        }
        .sidebar {
          background: var(--surface);
          border-right: 1px solid var(--border);
          padding: 28px 20px;
          display: flex;
          flex-direction: column;
          position: sticky;
          top: 0;
          height: 100vh;
        }
        .brand-mark {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 40px;
        }
        .brand-glyph {
          font-size: 22px;
          color: var(--accent);
          font-family: var(--font-display);
        }
        .brand-word {
          font-family: var(--font-display);
          font-weight: 600;
          font-size: 19px;
          letter-spacing: -0.01em;
        }
        .nav {
          display: flex;
          flex-direction: column;
          gap: 4px;
          flex: 1;
        }
        .nav-link {
          padding: 10px 14px;
          border-radius: var(--radius-sm);
          color: var(--ink-soft);
          text-decoration: none;
          font-weight: 500;
          font-size: 14.5px;
          transition: background 0.12s ease, color 0.12s ease;
        }
        .nav-link:hover { background: var(--paper-alt); color: var(--ink); }
        .nav-link.active { background: var(--brand-tint); color: var(--brand-dark-solid); font-weight: 600; }
        .sidebar-footer { margin-top: auto; padding-top: 20px; }
        .student-chip {
          display: flex;
          align-items: center;
          gap: 10px;
          padding: 10px;
          border-radius: var(--radius-md);
          background: var(--paper-alt);
        }
        .student-avatar {
          width: 34px; height: 34px;
          border-radius: 50%;
          background: var(--brand);
          color: white;
          display: flex; align-items: center; justify-content: center;
          font-weight: 600;
          font-family: var(--font-display);
          flex-shrink: 0;
        }
        .student-chip-name { font-weight: 600; font-size: 13.5px; }
        .link-btn {
          background: none; border: none; padding: 0;
          color: var(--brand); font-size: 12px; text-decoration: underline;
        }
        .main-area { min-width: 0; }
        @media (max-width: 780px) {
          .shell { grid-template-columns: 1fr; }
          .sidebar { position: relative; height: auto; flex-direction: row; align-items: center; padding: 16px; }
          .brand-mark { margin-bottom: 0; }
          .nav { display: none; }
          .sidebar-footer { margin-top: 0; margin-left: auto; padding-top: 0; }
        }
      `}</style>
    </div>
  );
}
