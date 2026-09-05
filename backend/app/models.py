


import uuid
import datetime as dt
from sqlalchemy import (
    Column, String, Integer, Float, Text, ForeignKey, DateTime, JSON, Boolean
)
from sqlalchemy.orm import relationship
from app.database import Base


def gen_id() -> str:
    return str(uuid.uuid4())


def now() -> dt.datetime:
    return dt.datetime.utcnow()


class Student(Base):
    __tablename__ = "students"

    id = Column(String, primary_key=True, default=gen_id)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=True)
    preferred_language = Column(String, default="English")
    current_level = Column(String, default="Beginner")  # Beginner/Intermediate/Advanced
    learning_goals = Column(Text, default="")
    created_at = Column(DateTime, default=now)

    documents = relationship("Document", back_populates="student", cascade="all, delete-orphan")
    lessons = relationship("LessonPlan", back_populates="student", cascade="all, delete-orphan")
    profile = relationship("LearnerProfile", back_populates="student", uselist=False, cascade="all, delete-orphan")


class LearnerProfile(Base):
    """Aggregated, continuously-updated picture of what a student knows."""
    __tablename__ = "learner_profiles"

    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("students.id"), unique=True)
    topics_studied = Column(JSON, default=list)      # ["Electricity", ...]
    concepts_mastered = Column(JSON, default=list)    # ["Ohm's Law", ...]
    weak_concepts = Column(JSON, default=list)        # ["Resistance", ...]
    current_learning_path = Column(JSON, default=dict)  # {"topic": ..., "steps": [...], "current_step": 0}
    updated_at = Column(DateTime, default=now, onupdate=now)

    student = relationship("Student", back_populates="profile")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("students.id"))
    filename = Column(String, nullable=False)
    filetype = Column(String, nullable=False)   # pdf/docx/pptx/txt
    language = Column(String, default="unknown")
    num_chunks = Column(Integer, default=0)
    status = Column(String, default="processing")  # processing/ready/failed
    created_at = Column(DateTime, default=now)

    student = relationship("Student", back_populates="documents")


class LessonPlan(Base):
    __tablename__ = "lesson_plans"

    id = Column(String, primary_key=True, default=gen_id)
    student_id = Column(String, ForeignKey("students.id"))
    document_id = Column(String, ForeignKey("documents.id"), nullable=True)
    topic = Column(String, nullable=False)
    level = Column(String, default="Beginner")
    language = Column(String, default="English")
    time_minutes = Column(Integer, default=20)
    plan_json = Column(JSON, default=dict)   # structured plan: sections with durations
    status = Column(String, default="planned")  # planned/in_progress/completed
    created_at = Column(DateTime, default=now)

    student = relationship("Student", back_populates="lessons")
    sessions = relationship("TeachingSession", back_populates="lesson", cascade="all, delete-orphan")


class TeachingSession(Base):
    """One live run-through of a lesson plan: the interaction log."""
    __tablename__ = "teaching_sessions"

    id = Column(String, primary_key=True, default=gen_id)
    lesson_id = Column(String, ForeignKey("lesson_plans.id"))
    current_section_index = Column(Integer, default=0)
    status = Column(String, default="active")  # active/paused/completed
    state = Column(JSON, default=dict)  # scratch state: pending question, qa_log, etc.
    started_at = Column(DateTime, default=now)
    completed_at = Column(DateTime, nullable=True)

    lesson = relationship("LessonPlan", back_populates="sessions")
    turns = relationship("SessionTurn", back_populates="session", cascade="all, delete-orphan")
    assessment = relationship("Assessment", back_populates="session", uselist=False, cascade="all, delete-orphan")


class SessionTurn(Base):
    """A single exchange: teacher explains/asks, student responds, evaluation."""
    __tablename__ = "session_turns"

    id = Column(String, primary_key=True, default=gen_id)
    session_id = Column(String, ForeignKey("teaching_sessions.id"))
    turn_type = Column(String)  # lesson_segment/question/assessment_question/answer/evaluation/adapt/chat
    role = Column(String)       # teacher/student
    content = Column(Text)
    visual_spec = Column(JSON, nullable=True)   # {"visual_type": "graph", ...}
    segments = Column(JSON, nullable=True)      # [{"label": "Explain", "text": "..."}, ...] for combined videos
    video_url = Column(String, nullable=True)   # combined animated-avatar video for this turn/step
    audio_url = Column(String, nullable=True)
    visual_url = Column(String, nullable=True)  # rendered diagram/graph image (first one, for thumbnails)
    is_correct = Column(Boolean, nullable=True)  # for student answers
    misconception = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now)

    session = relationship("TeachingSession", back_populates="turns")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(String, primary_key=True, default=gen_id)
    session_id = Column(String, ForeignKey("teaching_sessions.id"), unique=True)
    topic = Column(String)
    score_percent = Column(Float, default=0.0)
    strong_areas = Column(JSON, default=list)
    weak_areas = Column(JSON, default=list)
    misconceptions = Column(JSON, default=list)
    recommended_revision = Column(JSON, default=list)
    next_topic = Column(String, default="")
    raw_questions = Column(JSON, default=list)  # [{question, student_answer, correct, ...}]
    created_at = Column(DateTime, default=now)

    session = relationship("TeachingSession", back_populates="assessment")