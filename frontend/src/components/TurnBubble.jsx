
import { mediaUrl } from "../api/client";

const TYPE_META = {
  lesson_segment: { label: "Lesson", tone: "brand" },
  explain: { label: "Teaching", tone: "brand" },
  question: { label: "Question", tone: "accent" },
  assessment_question: { label: "Assessment", tone: "accent" },
  answer: { label: "Your answer", tone: "student" },
  evaluation: { label: "Feedback", tone: "neutral" },
  adapt: { label: "Let's re-look at this", tone: "warning" },
  misconception: { label: "Let's re-look at this", tone: "warning" },
  chat: { label: "", tone: "neutral" },
};

export default function TurnBubble({ turn }) {
  const isStudent = turn.role === "student";
  const meta = TYPE_META[turn.turn_type] || { label: turn.turn_type, tone: "neutral" };
  const hasVideo = !isStudent && !!turn.video_url;

  return (
    <div className={`turn ${isStudent ? "turn--student" : "turn--teacher"}`}>
      {!isStudent && <div className="turn-avatar">🧑‍🏫</div>}
      <div className="turn-body">
        {meta.label && (
          <div className={`turn-tag turn-tag--${meta.tone}`}>
            {meta.label}
            {turn.is_correct === true && <span className="turn-tag-icon">✓ correct</span>}
            {turn.is_correct === false && turn.turn_type === "answer" && (
              <span className="turn-tag-icon">needs another look</span>
            )}
          </div>
        )}
        <div className="turn-card">
          {hasVideo ? (
            <video
              className="turn-video"
              controls
              autoPlay
              playsInline
              poster={turn.visual_url ? mediaUrl(turn.visual_url) : undefined}
              src={mediaUrl(turn.video_url)}
            />
          ) : (
            <>
              {turn.visual_url && (
                <img className="turn-visual" src={mediaUrl(turn.visual_url)} alt="" loading="lazy" />
              )}
            </>
          )}

          {Array.isArray(turn.segments) && turn.segments.length > 1 ? (
            <div className="turn-segments">
              {turn.segments.map((seg, i) => (
                <div className="turn-segment" key={i}>
                  {seg.label && <span className="turn-segment-label">{seg.label}: </span>}
                  <span>{seg.text}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="turn-text">{turn.content}</p>
          )}
        </div>
      </div>
      {isStudent && <div className="turn-avatar turn-avatar--student">🙋</div>}

      <style>{`
        .turn { display: flex; gap: 12px; align-items: flex-start; max-width: 780px; }
        .turn--teacher { margin-right: auto; }
        .turn--student { margin-left: auto; flex-direction: row-reverse; }
        .turn-avatar {
          width: 36px; height: 36px; border-radius: 50%;
          background: var(--brand-tint);
          display: flex; align-items: center; justify-content: center;
          font-size: 17px; flex-shrink: 0;
        }
        .turn-avatar--student { background: var(--accent-tint); }
        .turn-body { min-width: 0; }
        .turn-tag {
          font-size: 11.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
          margin-bottom: 6px; display: flex; gap: 8px; align-items: center;
        }
        .turn-tag--brand { color: var(--brand-dark-solid); }
        .turn-tag--accent { color: var(--accent-dark); }
        .turn-tag--warning { color: var(--warning); }
        .turn-tag--student { color: var(--ink-faint); }
        .turn-tag--neutral { color: var(--ink-faint); }
        .turn-tag-icon {
          font-size: 10.5px; font-weight: 600; text-transform: none;
          padding: 1px 8px; border-radius: 999px; background: var(--success-tint); color: var(--success);
        }
        .turn-card {
          background: var(--surface);
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          padding: 14px 16px;
          box-shadow: var(--shadow-sm);
        }
        .turn--student .turn-card { background: var(--brand-dark-solid); border-color: var(--brand-dark-solid); }
        .turn--student .turn-text { color: white; }
        .turn-video {
          width: 100%;
          max-width: 480px;
          aspect-ratio: 4 / 3;
          border-radius: var(--radius-sm);
          margin-bottom: 10px;
          background: black;
          display: block;
          animation: visualFadeIn 0.35s ease-out;
        }
        .turn-visual {
          width: 100%;
          max-width: 420px;
          border-radius: var(--radius-sm);
          margin-bottom: 10px;
          display: block;
          border: 1px solid var(--border);
          animation: visualFadeIn 0.35s ease-out;
        }
        @keyframes visualFadeIn {
          from { opacity: 0; transform: translateY(6px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .turn-text { margin: 0; color: var(--ink); line-height: 1.6; font-size: 14.5px; }
        .turn-segments { display: flex; flex-direction: column; gap: 6px; }
        .turn-segment { margin: 0; color: var(--ink); line-height: 1.6; font-size: 14.5px; }
        .turn-segment-label { font-weight: 700; color: var(--ink-faint); }
      `}</style>
    </div>
  );
}