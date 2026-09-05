
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.config import settings
from app.database import Base, engine
from app import models  # noqa: F401 (ensures models are registered before create_all)
from app.routers import students, documents, lessons, sessions

Base.metadata.create_all(bind=engine)


def _ensure_column(table: str, column: str, coltype: str = "VARCHAR"):
    """Adds a column to an existing SQLite table if it doesn't already exist.
    create_all() only creates missing tables, not missing columns on tables
    that already exist from an earlier version of the schema."""
    if not settings.DATABASE_URL.startswith("sqlite"):
        return
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text(f"PRAGMA table_info({table})"))]
        if column not in cols:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"))
            conn.commit()


_ensure_column("session_turns", "visual_url")

app = FastAPI(title=settings.APP_NAME, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media/video", StaticFiles(directory=settings.VIDEO_DIR), name="video")
app.mount("/media/audio", StaticFiles(directory=settings.AUDIO_DIR), name="audio")

app.include_router(students.router)
app.include_router(documents.router)
app.include_router(lessons.router)
app.include_router(sessions.router)


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "llm_provider": settings.LLM_PROVIDER,
        "tts_provider": settings.TTS_PROVIDER,
        "avatar_provider": settings.AVATAR_PROVIDER,
        "env": settings.ENV,
    }