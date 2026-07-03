"""De-silence + normalize stage.

ElevenLabs SFX come back padded with leading/trailing silence and are not peak-
fit. This stage strips both ends and peak-normalizes, then writes the final
format (inferred from the output extension: wav / ogg / mp3).

All work is done through ffmpeg (silenceremove + volumedetect + volume).
"""
from __future__ import annotations

import os
import re
import subprocess


def _run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError("ffmpeg failed: " + " ".join(cmd) + "\n" + p.stderr[-800:])
    return p.stderr


def _trim_silence(src: str, dst: str, threshold_db: float, min_silence_ms: int) -> None:
    thr = f"{threshold_db}dB"
    dur = max(min_silence_ms, 0) / 1000.0
    # reverse-trim-reverse trims the trailing end too (silenceremove only trims
    # from the front).
    af = (
        f"silenceremove=start_periods=1:start_duration={dur}:start_threshold={thr},"
        "areverse,"
        f"silenceremove=start_periods=1:start_duration={dur}:start_threshold={thr},"
        "areverse"
    )
    _run(["ffmpeg", "-y", "-i", src, "-af", af, dst])


def _max_volume_dbfs(path: str) -> float:
    err = _run(["ffmpeg", "-i", path, "-af", "volumedetect", "-f", "null", "-"])
    m = re.search(r"max_volume:\s*(-?\d+(?:\.\d+)?)\s*dB", err)
    return float(m.group(1)) if m else 0.0


def _apply_gain(src: str, dst: str, gain_db: float) -> None:
    _run(["ffmpeg", "-y", "-i", src, "-af", f"volume={gain_db}dB", dst])


def _duration_seconds(path: str) -> float:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except ValueError:
        return 0.0


def trim_and_normalize(
    src: str,
    dst: str,
    threshold_db: float = -50.0,
    min_silence_ms: int = 60,
    peak_dbfs: float = -1.0,
) -> dict:
    """Trim leading/trailing silence and peak-normalize src -> dst. Returns a report."""
    tmp = dst + ".trim.wav"
    _trim_silence(src, tmp, threshold_db, min_silence_ms)
    peak_before = _max_volume_dbfs(tmp)
    gain = round(peak_dbfs - peak_before, 3)
    _apply_gain(tmp, dst, gain)
    if os.path.exists(tmp):
        os.remove(tmp)

    return {
        "source": src,
        "threshold_db": threshold_db,
        "min_silence_ms": min_silence_ms,
        "peak_before_dbfs": peak_before,
        "gain_applied_db": gain,
        "peak_target_dbfs": peak_dbfs,
        "src_duration_s": round(_duration_seconds(src), 3),
        "out_duration_s": round(_duration_seconds(dst), 3),
    }
