"""FFmpeg-based video assembly for Aether Archive."""
from __future__ import annotations
import json
import subprocess
from pathlib import Path
from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger("editor_engine")


def build_slideshow_command(
    image_paths: list[Path],
    audio_path: Path,
    output_path: Path,
    duration_per_image: float | None = None,
    resolution: str = "1920x1080",
    fps: int = 30,
) -> list[str]:
    """
    Build FFmpeg command: Ken-Burns-ish stills + narration audio.
    Simple hard cuts first; can upgrade to xfade later.
    """
    settings = get_settings()
    w, h = resolution.split("x")
    # probe audio duration
    probe = subprocess.run(
        [settings.ffprobe_path, "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
        capture_output=True, text=True, check=False,
    )
    audio_dur = float(probe.stdout.strip() or "60")
    n = max(1, len(image_paths))
    if duration_per_image is None:
        duration_per_image = audio_dur / n

    # concat demuxer list
    list_file = output_path.with_suffix(".txt")
    lines = []
    for img in image_paths:
        lines.append(f"file '{img.resolve()}'")
        lines.append(f"duration {duration_per_image}")
    if image_paths:
        lines.append(f"file '{image_paths[-1].resolve()}'")  # last frame hold
    list_file.write_text("\n".join(lines), encoding="utf-8")

    cmd = [
        settings.ffmpeg_path, "-y",
        "-f", "concat", "-safe", "0", "-i", str(list_file),
        "-i", str(audio_path),
        "-vf", f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},setsar=1,fps={fps},format=yuv420p",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_path),
    ]
    return cmd


def run_ffmpeg(cmd: list[str], timeout: int = 600) -> None:
    log.info("ffmpeg_start", cmd=" ".join(cmd[:8]) + "...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if result.returncode != 0:
        log.error("ffmpeg_failed", stderr=result.stderr[-2000:])
        raise RuntimeError(f"FFmpeg failed: {result.stderr[-500:]}")
    log.info("ffmpeg_ok")


def generate_srt_from_sections(sections: list[dict], out_path: Path, wpm: float = 140) -> Path:
    """Rough SRT from section texts for captions."""
    lines = []
    t = 0.0
    idx = 1
    for sec in sections:
        text = sec.get("text", "").strip()
        if not text:
            continue
        words = text.split()
        # chunk every ~12 words
        for i in range(0, len(words), 12):
            chunk = " ".join(words[i:i+12])
            dur = len(chunk.split()) / wpm * 60
            start = _ts(t)
            end = _ts(t + dur)
            lines.append(f"{idx}\n{start} --> {end}\n{chunk}\n")
            t += dur
            idx += 1
    out_path.write_text("\n".join(lines), encoding="utf-8")
    return out_path


def _ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds - int(seconds)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
