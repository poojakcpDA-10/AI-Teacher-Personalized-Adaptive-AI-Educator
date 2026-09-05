
import math
import os
import numpy as np
from PIL import Image, ImageDraw
from app.config import settings

os.makedirs(settings.VIDEO_DIR, exist_ok=True)

FPS = 20
FRAME_W, FRAME_H = 640, 480

# Expression presets, keyed by the same vocabulary the teaching loop uses
# for its turn types, so the caller can just pass the turn's semantic role.
EXPRESSIONS = {
    "neutral": {},
    "explain": {"eyebrow": 4},
    "demonstrate": {"eyebrow": 4},
    "question": {"eyebrow": 9},
    "evaluation_correct": {"smile": True},
    "evaluation_incorrect": {"eyebrow": 2},
    "misconception": {"frown": True},
}


def _audio_envelope(audio_clip, fps: int = FPS):
    """Per-video-frame RMS loudness (0..1), used to drive mouth-openness."""
    if audio_clip is None:
        return None
    try:
        sr = 22050
        arr = audio_clip.to_soundarray(fps=sr)
        if arr.ndim > 1:
            arr = arr.mean(axis=1)
        n_frames = max(1, int(math.ceil(audio_clip.duration * fps)))
        samples_per_frame = max(1, len(arr) // n_frames)
        env = np.zeros(n_frames, dtype=np.float32)
        for i in range(n_frames):
            chunk = arr[i * samples_per_frame:(i + 1) * samples_per_frame]
            if len(chunk):
                env[i] = float(np.sqrt(np.mean(np.square(chunk))))
        peak = env.max()
        if peak > 1e-6:
            env = np.clip(env / peak, 0.0, 1.0)
        # light smoothing so the mouth doesn't flicker frame to frame
        if len(env) > 2:
            kernel = np.array([0.25, 0.5, 0.25])
            env = np.convolve(env, kernel, mode="same")
        return env
    except Exception:
        return None


def _draw_frame(mouth_open: float, blink: bool, expr_key: str) -> np.ndarray:
    expr = EXPRESSIONS.get(expr_key, {})
    img = Image.new("RGB", (FRAME_W, FRAME_H), color="#EEF2FF")
    draw = ImageDraw.Draw(img)
    cx, cy = FRAME_W // 2, FRAME_H // 2 + 6

    # shoulders / body
    draw.pieslice([cx - 180, cy + 110, cx + 180, cy + 360], 180, 360, fill="#3B82F6")

    # face
    draw.ellipse([cx - 100, cy - 135, cx + 100, cy + 110], fill="#F4C9A0")

    # hair
    draw.pieslice([cx - 106, cy - 182, cx + 106, cy - 15], 180, 360, fill="#4B3621")

    # eyebrows (raised for a question, drawn low+flat for a frown/concerned look)
    if expr.get("frown"):
        brow_y = cy - 42
    else:
        brow_y = cy - 58 - expr.get("eyebrow", 0)
    draw.rounded_rectangle([cx - 62, brow_y, cx - 14, brow_y + 8], radius=4, fill="#4B3621")
    draw.rounded_rectangle([cx + 14, brow_y, cx + 62, brow_y + 8], radius=4, fill="#4B3621")

    # eyes (blink = squashed)
    eye_h = 3 if blink else 15
    draw.ellipse([cx - 52, cy - 32 - eye_h / 2, cx - 26, cy - 32 + eye_h / 2], fill="#2B2B2B")
    draw.ellipse([cx + 26, cy - 32 - eye_h / 2, cx + 52, cy - 32 + eye_h / 2], fill="#2B2B2B")

    # mouth: smile arc for positive feedback, otherwise an ellipse that
    # opens with the live audio envelope
    if expr.get("smile"):
        draw.arc([cx - 38, cy + 8, cx + 38, cy + 62], start=15, end=165, fill="#8B4A3B", width=8)
    else:
        mh = 6 + mouth_open * 36
        draw.ellipse([cx - 30, cy + 28 - mh / 2, cx + 30, cy + 28 + mh / 2], fill="#8B4A3B")

    return np.array(img)


def build_avatar_clip(audio_path: str | None, expression: str = "neutral", min_duration: float = 2.2):
    """Returns a moviepy VideoClip (with audio attached, if any) of the
    avatar speaking one segment's text, mouth-synced to that audio."""
    from moviepy.editor import VideoClip, AudioFileClip

    audio_clip = None
    duration = min_duration
    envelope = None
    if audio_path and os.path.exists(audio_path):
        try:
            audio_clip = AudioFileClip(audio_path)
            duration = max(min_duration, audio_clip.duration)
            envelope = _audio_envelope(audio_clip)
        except Exception:
            audio_clip = None

    rng = np.random.default_rng(abs(hash(audio_path or expression)) % (2**32))
    n_blinks = max(1, int(duration // 2.8))
    blink_times = sorted(rng.uniform(0.4, max(0.5, duration - 0.2), n_blinks))

    def make_frame(t):
        if envelope is not None and len(envelope):
            idx = min(int(t * FPS), len(envelope) - 1)
            mouth = float(envelope[idx])
        else:
            # No audio (e.g. TTS unavailable) -> gentle idle talking motion
            # so the segment still reads as "speaking" rather than frozen.
            mouth = 0.15 + 0.35 * abs(math.sin(t * 6.0))
        blink = any(abs(t - bt) < 0.08 for bt in blink_times)
        return _draw_frame(mouth, blink, expression)

    clip = VideoClip(make_frame, duration=duration)
    if audio_clip is not None:
        clip = clip.set_audio(audio_clip)
    return clip