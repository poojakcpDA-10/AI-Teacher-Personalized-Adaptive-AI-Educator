
import os
import uuid
from app.config import settings
from app.services import tts_service, visual_service, avatar_service

os.makedirs(settings.VIDEO_DIR, exist_ok=True)


def _to_url(path: str | None) -> str | None:
    if not path or not os.path.exists(path):
        return None
    # Use relpath (not basename) so files in subfolders, e.g. video/visuals/x.png,
    # resolve to the correct nested URL instead of a flattened, wrong one.
    video_dir = os.path.abspath(settings.VIDEO_DIR)
    audio_dir = os.path.abspath(settings.AUDIO_DIR)
    abspath = os.path.abspath(path)
    if os.path.commonpath([abspath, video_dir]) == video_dir:
        rel = os.path.relpath(abspath, video_dir).replace(os.sep, "/")
        return f"/media/video/{rel}"
    if os.path.commonpath([abspath, audio_dir]) == audio_dir:
        rel = os.path.relpath(abspath, audio_dir).replace(os.sep, "/")
        return f"/media/audio/{rel}"
    return None


def build_combined_video(segments: list[dict], language: str) -> dict:
    """
    segments: ordered list of dicts, each:
        {"label": str, "text": str, "expression": str, "visual_spec": dict|None}
    "expression" should be one of app.services.avatar_service.EXPRESSIONS
    (falls back to "neutral" if omitted/unknown).

    Synthesizes speech per segment, renders any planned diagram, animates
    the avatar for that segment mouth-synced to its own audio, overlays the
    diagram (if any) on top while it talks, then concatenates every segment
    into ONE mp4 for this lesson step.

    Returns {"video_url", "audio_url", "visual_url", "segments"}.
    "audio_url"/"visual_url" point at the first segment's raw audio/diagram
    (kept for any code still reading those individually); the video itself
    contains all segments' narration and diagrams.
    """
    clean_segments = [s for s in segments if (s.get("text") or "").strip()]
    if not clean_segments:
        return {"video_url": None, "audio_url": None, "visual_url": None, "segments": []}

    audio_paths: list[str | None] = []
    visual_paths: list[str | None] = []
    clips = []

    try:
        from moviepy.editor import concatenate_videoclips, CompositeVideoClip, ImageClip
    except Exception:
        concatenate_videoclips = None

    for seg in clean_segments:
        text = seg["text"].strip()
        expression = seg.get("expression") or "neutral"

        audio_path = tts_service.synthesize(text, language=language)
        audio_paths.append(audio_path)

        visual_path = None
        visual_spec = seg.get("visual_spec")
        if visual_spec:
            try:
                visual_path = visual_service.render_visual(visual_spec)
            except Exception:
                visual_path = None
        visual_paths.append(visual_path)

        if concatenate_videoclips is None:
            continue  # moviepy unavailable -> no video, but audio/visual URLs still work below

        try:
            clip = avatar_service.build_avatar_clip(audio_path, expression=expression)
            if visual_path and os.path.exists(visual_path):
                img_clip = (
                    ImageClip(visual_path)
                    .set_duration(clip.duration)
                    .resize(height=int(clip.h * 0.6))
                    .set_position(("center", 6))
                    .fadein(0.4)
                    .fadeout(0.3)
                )
                clip = CompositeVideoClip([clip, img_clip])
            clips.append(clip)
        except Exception:
            continue

    video_path = None
    final = None
    if clips:
        try:
            final = concatenate_videoclips(clips, method="compose")
            video_path = os.path.join(settings.VIDEO_DIR, f"{uuid.uuid4().hex}.mp4")
            final.write_videofile(
                video_path, fps=avatar_service.FPS, codec="libx264", audio_codec="aac",
                verbose=False, logger=None,
            )
        except Exception:
            video_path = None
        finally:
            for c in clips:
                try:
                    c.close()
                except Exception:
                    pass
            if final is not None:
                try:
                    final.close()
                except Exception:
                    pass

    first_audio = next((p for p in audio_paths if p), None)
    first_visual = next((p for p in visual_paths if p), None)

    return {
        "video_url": _to_url(video_path),
        "audio_url": _to_url(first_audio),
        "visual_url": _to_url(first_visual),
        "segments": [{"label": s.get("label", ""), "text": s["text"]} for s in clean_segments],
    }


def build_turn_video(script_text: str, language: str, visual_spec: dict | None, expression: str = "neutral") -> dict:
    """Back-compat single-segment convenience wrapper around
    build_combined_video, for any single standalone teacher line."""
    result = build_combined_video(
        [{"label": "", "text": script_text, "expression": expression, "visual_spec": visual_spec}],
        language,
    )
    return {
        "video_url": result["video_url"],
        "audio_url": result["audio_url"],
        "visual_url": result["visual_url"],
    }