const TYPE_LABEL = {
  introduction: "Intro",
  concept: "Concept",
  example: "Example",
  question: "Question",
  assessment: "Assessment",
};

export default function LessonRail({ sections, currentIndex }) {
  return (
    <div className="lesson-rail">
      <div className="rail-track">
        {sections.map((s, i) => {
          const state = i < currentIndex ? "done" : i === currentIndex ? "current" : "todo";
          return (
            <div className="rail-stop" key={i}>
              <div className={`rail-dot rail-dot--${state}`}>
                {state === "done" ? "✓" : i + 1}
              </div>
              <div className="rail-tick" />
              <div className="rail-caption">
                <div className="rail-caption-type">{TYPE_LABEL[s.type] || s.type}</div>
                <div className="rail-caption-title">{s.title}</div>
              </div>
            </div>
          );
        })}
      </div>

      <style>{`
        .lesson-rail {
          overflow-x: auto;
          padding: 6px 4px 14px 4px;
        }
        .rail-track {
          display: flex;
          align-items: flex-start;
          gap: 0;
          min-width: max-content;
        }
        .rail-stop {
          display: flex;
          flex-direction: column;
          align-items: center;
          width: 108px;
          position: relative;
        }
        .rail-stop:not(:last-child)::after {
          content: "";
          position: absolute;
          top: 15px;
          left: 50%;
          width: 100%;
          height: 2px;
          background: var(--border-strong);
          z-index: 0;
        }
        .rail-dot {
          width: 30px; height: 30px;
          border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          font-family: var(--font-mono);
          font-size: 12.5px;
          font-weight: 600;
          z-index: 1;
          border: 2px solid var(--border-strong);
          background: var(--surface);
          color: var(--ink-faint);
          transition: all 0.2s ease;
        }
        .rail-dot--done { background: var(--brand); border-color: var(--brand); color: white; }
        .rail-dot--current {
          background: var(--accent);
          border-color: var(--accent);
          color: white;
          box-shadow: 0 0 0 4px var(--accent-tint);
          animation: pulse 1.8s ease-in-out infinite;
        }
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 0 4px var(--accent-tint); }
          50% { box-shadow: 0 0 0 7px var(--accent-tint); }
        }
        .rail-caption { text-align: center; margin-top: 8px; padding: 0 4px; }
        .rail-caption-type {
          font-size: 10.5px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: var(--ink-faint);
          font-weight: 600;
        }
        .rail-caption-title {
          font-size: 12px;
          color: var(--ink-soft);
          margin-top: 2px;
          line-height: 1.3;
        }
      `}</style>
    </div>
  );
}
