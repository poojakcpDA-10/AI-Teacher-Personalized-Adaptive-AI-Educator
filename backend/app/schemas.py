

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import datetime as dt


# ---------- Student ----------
class StudentCreate(BaseModel):
    name: str
    email: Optional[str] = None
    preferred_language: str = "English"
    current_level: str = "Beginner"
    learning_goals: str = ""


class StudentOut(BaseModel):
    id: str
    name: str
    email: Optional[str]
    preferred_language: str
    current_level: str
    learning_goals: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


class LearnerProfileOut(BaseModel):
    topics_studied: List[str]
    concepts_mastered: List[str]
    weak_concepts: List[str]
    current_learning_path: Dict[str, Any]

    class Config:
        from_attributes = True


# ---------- Documents ----------
class DocumentOut(BaseModel):
    id: str
    filename: str
    filetype: str
    language: str
    num_chunks: int
    status: str
    created_at: dt.datetime

    class Config:
        from_attributes = True


# ---------- Lesson planning ----------
class LessonRequest(BaseModel):
    student_id: str
    topic: str
    document_id: Optional[str] = None
    level: str = "Beginner"
    language: str = "English"
    time_minutes: int = 20
    instructions: Optional[str] = ""   # free text like "explain with cricket examples"


class LessonSection(BaseModel):
    title: str
    duration_minutes: int
    type: str  # introduction/concept/example/question/assessment


class LessonPlanOut(BaseModel):
    id: str
    topic: str
    level: str
    language: str
    time_minutes: int
    plan_json: Dict[str, Any]
    status: str

    class Config:
        from_attributes = True


# ---------- Teaching session ----------
class SessionStart(BaseModel):
    lesson_id: str


class SessionTurnOut(BaseModel):
    id: str
    turn_type: str
    role: str
    content: str
    visual_spec: Optional[Dict[str, Any]] = None
    segments: Optional[List[Dict[str, Any]]] = None
    video_url: Optional[str] = None
    audio_url: Optional[str] = None
    visual_url: Optional[str] = None
    is_correct: Optional[bool] = None
    misconception: Optional[str] = None
    created_at: dt.datetime

    class Config:
        from_attributes = True


class StudentAnswerIn(BaseModel):
    session_id: str
    answer_text: str


class NextStepOut(BaseModel):
    session_id: str
    finished: bool
    turn: Optional[SessionTurnOut] = None
    progress: Dict[str, Any] = {}


# ---------- Chat / follow-up Q&A ----------
class ChatIn(BaseModel):
    session_id: str
    message: str


# ---------- Assessment ----------
class AssessmentOut(BaseModel):
    id: str
    topic: str
    score_percent: float
    strong_areas: List[str]
    weak_areas: List[str]
    misconceptions: List[str]
    recommended_revision: List[str]
    next_topic: str
    raw_questions: List[Dict[str, Any]]

    class Config:
        from_attributes = True


# ---------- Learning path ----------
class LearningPathRequest(BaseModel):
    student_id: str
    topic: str


class LearningPathOut(BaseModel):
    topic: str
    steps: List[Dict[str, Any]]
    current_step: int