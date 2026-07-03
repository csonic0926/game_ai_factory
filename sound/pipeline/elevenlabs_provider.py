"""ElevenLabs sound-generation provider (text -> SFX).

Uses only the Python standard library (urllib) so the factory has no pip deps.
Endpoint: POST https://api.elevenlabs.io/v1/sound-generation  -> audio/mpeg (mp3)
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

API_URL = "https://api.elevenlabs.io/v1/sound-generation"


def generate(
    prompt: str,
    out_path: str,
    key: str,
    duration_seconds: float | None = None,
    prompt_influence: float = 0.3,
    loop: bool = False,
    model_id: str | None = None,
    timeout: int = 180,
) -> int:
    """Generate one SFX clip and write raw mp3 bytes to out_path. Returns byte count."""
    body: dict = {"text": prompt, "prompt_influence": float(prompt_influence), "loop": bool(loop)}
    if duration_seconds is not None:
        # EL accepts 0.5..30s; None lets the model choose.
        body["duration_seconds"] = float(duration_seconds)
    if model_id:
        body["model_id"] = model_id

    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={
            "xi-api-key": key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:600]
        raise RuntimeError(f"ElevenLabs sound-generation HTTP {e.code}: {detail}") from None

    if not data:
        raise RuntimeError("ElevenLabs returned empty audio body")
    with open(out_path, "wb") as f:
        f.write(data)
    return len(data)
