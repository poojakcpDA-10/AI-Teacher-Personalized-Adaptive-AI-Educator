
import axios from "axios";

export const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
export const MEDIA_BASE = API_BASE;

export const api = axios.create({ baseURL: API_BASE, timeout: 310000 });

// ---- Students ----
export const createStudent = (data) => api.post("/api/students", data).then(r => r.data);
export const listStudents = () => api.get("/api/students").then(r => r.data);
export const getStudent = (id) => api.get(`/api/students/${id}`).then(r => r.data);
export const getProfile = (id) => api.get(`/api/students/${id}/profile`).then(r => r.data);
export const listStudentDocuments = (id) => api.get(`/api/students/${id}/documents`).then(r => r.data);
export const listStudentLessons = (id) => api.get(`/api/students/${id}/lessons`).then(r => r.data);
export const listStudentAssessments = (id) => api.get(`/api/students/${id}/assessments`).then(r => r.data);

// ---- Documents ----
export const uploadDocument = (studentId, file, onProgress) => {
  const form = new FormData();
  form.append("student_id", studentId);
  form.append("file", file);
  return api.post("/api/documents/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: onProgress,
  }).then(r => r.data);
};
export const getDocument = (id) => api.get(`/api/documents/${id}`).then(r => r.data);

// ---- Lessons ----
export const createLesson = (data) => api.post("/api/lessons", data).then(r => r.data);
export const getLesson = (id) => api.get(`/api/lessons/${id}`).then(r => r.data);
export const createLearningPath = (data) => api.post("/api/lessons/learning-path", data).then(r => r.data);

// ---- Sessions ----
export const startSession = (lessonId) => api.post("/api/sessions/start", { lesson_id: lessonId }).then(r => r.data);
export const nextTurn = (sessionId) => api.post(`/api/sessions/${sessionId}/next`).then(r => r.data);
export const submitAnswer = (sessionId, answerText) =>
  api.post("/api/sessions/answer", { session_id: sessionId, answer_text: answerText }).then(r => r.data);
export const getTurns = (sessionId) => api.get(`/api/sessions/${sessionId}/turns`).then(r => r.data);
export const getAssessment = (sessionId) => api.get(`/api/sessions/${sessionId}/assessment`).then(r => r.data);
export const chatFollowup = (sessionId, message) =>
  api.post("/api/sessions/chat", { session_id: sessionId, message }).then(r => r.data);

export const mediaUrl = (path) => (path ? `${MEDIA_BASE}${path}` : null);