import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useStudent } from "../context/StudentContext";
import { createLesson, uploadDocument, getDocument } from "../api/client";

const TIME_PRESETS = [
  { label: "5 min", value: 5 },
  { label: "20 min", value: 20 },
  { label: "60 min", value: 60 },
  { label: "7 days", value: 10080 },
];
const LEVELS = ["Beginner", "Intermediate", "Advanced"];

export default function NewLesson() {
  const { student } = useStudent();
  const navigate = useNavigate();
  const fileRef = useRef(null);

  const [topic, setTopic] = useState("");
  const [level, setLevel] = useState(student?.current_level || "Beginner");
  const [language, setLanguage] = useState(student?.preferred_language || "English");
  const [minutes, setMinutes] = useState(20);
  const [instructions, setInstructions] = useState("");
  const [file, setFile] = useState(null);
  const [docId, setDocId] = useState(null);
  const [docStatus, setDocStatus] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!student) navigate("/");
  }, [student]);

  const handleFile = async (e) => {
    const f = e.target.files?.[0];
    if (!f) return;
    setFile(f);
    setUploading(true);
    setError("");
    try {
      const doc = await uploadDocument(student.id, f);
      setDocId(doc.id);
      setDocStatus(doc.status);
      poll(doc.id);
    } catch {
      setError("Upload failed. Check the file type (PDF, DOCX, PPTX, TXT).");
    } finally {
      setUploading(false);
    }
  };

  const poll = (id) => {
    const iv = setInterval(async () => {
      try {
        const d = await getDocument(id);
        setDocStatus(d.status);
        if (d.status !== "processing") clearInterval(iv);
      } catch {
        clearInterval(iv);
      }
    }, 1200);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    setCreating(true);
    setError("");
    try {
      const lesson = await createLesson({
        student_id: student.id, topic: topic.trim(), level, language,
        time_minutes: Number(minutes), document_id: docId, instructions,
      });
      navigate(`/session/${lesson.id}`);
    } catch (err) {
      if (err.code === "ECONNABORTED") {
        setError("The lesson plan is taking longer than expected (this can happen the first time a local model loads). Try again in a minute, or check the backend terminal for progress.");
      } else if (err.response) {
        setError(`Backend error (${err.response.status}): ${err.response.data?.detail || "couldn't build the lesson plan."}`);
      } else if (err.request) {
        setError("Couldn't reach the backend. Is it running on http://localhost:8000?");
      } else {
        setError("Couldn't build the lesson plan.");
      }
    } finally {
      setCreating(false);
    }
  };

  if (!student) return null;

  return (
    <div className="new-lesson">
      <div className="nl-header">
        <div className="hero-eyebrow">Plan a session for {student.name}</div>
        <h1>What should we teach today?</h1>
      </div>

      <form className="card panel" onSubmit={handleSubmit}>
        <label className="label">Topic</label>
        <input className="field" value={topic} onChange={(e) => setTopic(e.target.value)}
               placeholder="e.g. Ohm's Law, or React for a technical interview"
               required style={{marginTop: 6, marginBottom: 20, fontSize: 16, padding: "14px 16px"}} />

        <div className="row-2">
          <div>
            <label className="label">Level</label>
            <div className="chip-row" style={{marginTop: 6}}>
              {LEVELS.map((l) => (
                <button type="button" key={l} className={`chip ${level === l ? "chip--active" : ""}`}
                        onClick={() => setLevel(l)}>{l}</button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Language</label>
            <select className="field" value={language} onChange={(e) => setLanguage(e.target.value)} style={{marginTop: 6}}>
              {["English", "Hindi", "Hinglish", "Tamil", "Telugu", "Bengali", "Marathi"].map((l) => (
                <option key={l} value={l}>{l}</option>
              ))}
            </select>
          </div>
        </div>

        <label className="label" style={{marginTop: 20, display: "block"}}>Time available</label>
        <div className="chip-row" style={{marginTop: 6}}>
          {TIME_PRESETS.map((t) => (
            <button type="button" key={t.value} className={`chip ${minutes === t.value ? "chip--active" : ""}`}
                    onClick={() => setMinutes(t.value)}>{t.label}</button>
          ))}
        </div>

        <label className="label" style={{marginTop: 20, display: "block"}}>
          Anything specific? <span className="label-optional">(optional)</span>
        </label>
        <textarea className="field" rows={2} value={instructions} onChange={(e) => setInstructions(e.target.value)}
                  placeholder="e.g. use cricket analogies, focus on exam questions"
                  style={{marginTop: 6, resize: "vertical"}} />

        <label className="label" style={{marginTop: 20, display: "block"}}>
          Upload material <span className="label-optional">(optional — PDF, DOCX, PPTX, TXT)</span>
        </label>
        <div className="upload-box" onClick={() => fileRef.current?.click()}>
          <input type="file" ref={fileRef} hidden accept=".pdf,.docx,.pptx,.txt" onChange={handleFile} />
          {!file && <span>📄 Click to upload a textbook, notes, or slides</span>}
          {file && (
            <span>
              {file.name}{" "}
              {uploading && "· uploading…"}
              {!uploading && docStatus === "processing" && "· processing…"}
              {!uploading && docStatus === "ready" && "· ready ✓"}
              {!uploading && docStatus === "failed" && "· failed, will teach from general knowledge"}
            </span>
          )}
        </div>

        {error && <p style={{color: "var(--error)", fontSize: 13, marginTop: 10}}>{error}</p>}

        <button className="btn btn-primary" type="submit" disabled={creating || uploading}
                style={{marginTop: 24, width: "100%", padding: "14px"}}>
          {creating ? "Planning your lesson…" : "Build my lesson →"}
        </button>
      </form>

      <style>{`
        .new-lesson { max-width: 620px; margin: 0 auto; padding: 48px 24px 60px; }
        .nl-header { margin-bottom: 24px; }
        .hero-eyebrow { font-size: 12.5px; font-weight: 600; letter-spacing: 0.08em; text-transform: uppercase; color: var(--accent-dark); margin-bottom: 4px; }
        .nl-header h1 { font-size: 30px; }
        .panel { padding: 30px; }
        .row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 4px; }
        .chip-row { display: flex; gap: 8px; flex-wrap: wrap; }
        .chip {
          padding: 8px 15px; border-radius: 999px; border: 1.5px solid var(--border);
          background: var(--surface-sunken); font-size: 13.5px; font-weight: 500; color: var(--ink-soft);
        }
        .chip--active { background: var(--brand); border-color: var(--brand); color: white; }
        .label-optional { text-transform: none; font-weight: 400; letter-spacing: 0; color: var(--ink-faint); }
        .upload-box {
          margin-top: 8px; padding: 20px; border: 1.5px dashed var(--border-strong);
          border-radius: var(--radius-md); text-align: center; font-size: 13.5px; color: var(--ink-soft);
          cursor: pointer; background: var(--surface-sunken); transition: border-color 0.12s ease;
        }
        .upload-box:hover { border-color: var(--brand); }
        @media (max-width: 560px) { .row-2 { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
}