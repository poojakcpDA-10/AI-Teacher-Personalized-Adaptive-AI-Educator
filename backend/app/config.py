
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"


class Settings(BaseSettings):
    # --- General ---
    APP_NAME: str = "AI Teacher"
    ENV: str = "development"  # "development" | "production"
    SECRET_KEY: str = "change-this-secret-key-in-production"
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # --- Database ---
    DATABASE_URL: str = f"sqlite:///{DATA_DIR / 'ai_teacher.db'}"

    # --- LLM (Qwen 3 via Ollama by default) ---
    LLM_PROVIDER: str = "ollama"  # "ollama" | "openai_compatible" | "mock"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen3:8b"
    OPENAI_COMPATIBLE_BASE_URL: str = ""   # e.g. https://api.groq.com/openai/v1
    OPENAI_COMPATIBLE_API_KEY: str = ""
    OPENAI_COMPATIBLE_MODEL: str = ""

    # --- RAG ---
    CHROMA_DIR: str = str(DATA_DIR / "chroma")
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 150
    RETRIEVAL_TOP_K: int = 5

    # --- Speech ---
    TTS_PROVIDER: str = "pyttsx3"  # "pyttsx3" (offline dev) | "piper" | "xtts"
    STT_PROVIDER: str = "none"     # "whisper" | "none"
    AUDIO_DIR: str = str(DATA_DIR / "audio")

    # --- Avatar / Video ---
    AVATAR_PROVIDER: str = "static"  # "static" (dev placeholder) | "sadtalker" | "wav2lip"
    AVATAR_IMAGE_PATH: str = str(DATA_DIR / "avatars" / "default_teacher.png")
    VIDEO_DIR: str = str(DATA_DIR / "video")

    # --- Uploads ---
    UPLOAD_DIR: str = str(DATA_DIR / "uploads")
    MAX_UPLOAD_MB: int = 50

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()

for p in [settings.CHROMA_DIR, settings.AUDIO_DIR, settings.VIDEO_DIR, settings.UPLOAD_DIR]:
    Path(p).mkdir(parents=True, exist_ok=True)
