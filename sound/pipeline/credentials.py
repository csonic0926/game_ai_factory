"""Credential resolution for the sound factory.

Order of precedence:
1. ELEVENLABS_API_KEY env var
2. ~/.config/voicein/key   (the existing ElevenLabs key on this machine)
"""
from __future__ import annotations

import os
import pathlib


def get_elevenlabs_key() -> str:
    key = os.environ.get("ELEVENLABS_API_KEY")
    if key and key.strip():
        return key.strip()

    p = pathlib.Path(os.path.expanduser("~/.config/voicein/key"))
    if p.exists():
        val = p.read_text(encoding="utf-8").strip()
        if val:
            return val

    raise RuntimeError(
        "No ElevenLabs key found. Set ELEVENLABS_API_KEY or create ~/.config/voicein/key"
    )
