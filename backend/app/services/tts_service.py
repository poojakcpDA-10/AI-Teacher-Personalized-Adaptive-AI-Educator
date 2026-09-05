
import os
import uuid
from app.config import settings

os.makedirs(settings.AUDIO_DIR, exist_ok=True)


def _synthesize_pyttsx3(text: str, out_path: str):
    import pyttsx3
    engine = pyttsx3.init()
    engine.save_to_file(text, out_path)
    engine.runAndWait()


def _synthesize_piper(text: str, out_path: str):
    raise NotImplementedError(
        "Wire this up to your local Piper TTS binary/server. "
        "See README 'Production Upgrades' for instructions."
    )


def _synthesize_xtts(text: str, out_path: str):
    raise NotImplementedError(
        "Wire this up to a local Coqui XTTS-v2 server for expressive, "
        "voice-cloned multilingual speech. See README 'Production Upgrades'."
    )


def synthesize(text: str, language: str = "English") -> str | None:
    """Returns a filesystem path to a generated audio file, or None on failure."""
    filename = f"{uuid.uuid4().hex}.wav"
    out_path = os.path.join(settings.AUDIO_DIR, filename)
    try:
        if settings.TTS_PROVIDER == "pyttsx3":
            _synthesize_pyttsx3(text, out_path)
        elif settings.TTS_PROVIDER == "piper":
            _synthesize_piper(text, out_path)
        elif settings.TTS_PROVIDER == "xtts":
            _synthesize_xtts(text, out_path)
        else:
            return None
        return out_path if os.path.exists(out_path) else None
    except Exception:
        # TTS engine unavailable in this environment (e.g. headless sandbox
        # with no audio subsystem) -> degrade gracefully, text still shown.
        return None
