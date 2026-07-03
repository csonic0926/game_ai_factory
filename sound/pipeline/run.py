"""Run orchestration: generate -> trim -> deliverables, with asset-factory-style
run artifacts so an AI caller inspects the same way it does for game_asset_factory.

Run layout (under <output_root>/<run_id>/):
  request/el_request.json        provider request snapshot (real providers)
  step_1_raw/<run_id>.<ext>      raw provider output (mp3 for EL, wav for mock)
  deliverables/<run_id>.<fmt>    trimmed + peak-normalized final asset
  deliverables/manifest.json     asset metadata
  deliverables/validation_summary.json
  artifact_status.json           top-level status the caller reads first
"""
from __future__ import annotations

import json
import os
import subprocess

from . import credentials, elevenlabs_provider, trim


def _load_spec(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _mkdirs(*paths: str) -> None:
    for p in paths:
        os.makedirs(p, exist_ok=True)


def _write_json(path: str, obj: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def _mock_raw(out_path: str, duration_seconds: float | None) -> int:
    """Offline smoke: synth a clip PADDED with silence so trim has work to do.
    0.3s silence + <dur> 440Hz tone + 0.3s silence.
    """
    dur = duration_seconds or 0.4
    filt = (
        f"aevalsrc=0:d=0.3[a];"
        f"sine=frequency=440:duration={dur}[b];"
        f"aevalsrc=0:d=0.3[c];"
        f"[a][b][c]concat=n=3:v=0:a=1[out]"
    )
    subprocess.run(
        ["ffmpeg", "-y", "-filter_complex", filt, "-map", "[out]", out_path],
        capture_output=True, text=True, check=True,
    )
    return os.path.getsize(out_path)


def run(spec_path: str, provider_override: str | None = None) -> dict:
    spec = _load_spec(spec_path)
    run_id = spec["run_id"]
    root = os.path.join(spec["output_root"], run_id)
    req_dir = os.path.join(root, "request")
    raw_dir = os.path.join(root, "step_1_raw")
    deliver_dir = os.path.join(root, "deliverables")
    _mkdirs(root, req_dir, raw_dir, deliver_dir)

    provider = provider_override or spec.get("provider", {}).get("name", "elevenlabs")
    fmt = spec.get("output_format", "wav")

    status: dict = {"run_id": run_id, "provider": provider, "ok": False, "stage": "start"}

    # ---- generate ----
    if provider == "mock":
        raw = os.path.join(raw_dir, f"{run_id}.wav")
        raw_bytes = _mock_raw(raw, spec.get("duration_seconds"))
    else:
        raw = os.path.join(raw_dir, f"{run_id}.mp3")
        request_snapshot = {
            "endpoint": elevenlabs_provider.API_URL,
            "text": spec["prompt"],
            "duration_seconds": spec.get("duration_seconds"),
            "prompt_influence": spec.get("prompt_influence", 0.3),
            "loop": spec.get("loop", False),
            "model_id": spec.get("provider", {}).get("model"),
        }
        _write_json(os.path.join(req_dir, "el_request.json"), request_snapshot)
        key = credentials.get_elevenlabs_key()
        raw_bytes = elevenlabs_provider.generate(
            spec["prompt"], raw, key,
            duration_seconds=spec.get("duration_seconds"),
            prompt_influence=spec.get("prompt_influence", 0.3),
            loop=spec.get("loop", False),
            model_id=spec.get("provider", {}).get("model"),
        )
    status["stage"] = "generated"
    status["raw_bytes"] = raw_bytes
    status["raw_path"] = raw

    # ---- trim + normalize ----
    tcfg = spec.get("trim", {})
    deliver = os.path.join(deliver_dir, f"{run_id}.{fmt}")
    report = trim.trim_and_normalize(
        raw, deliver,
        threshold_db=tcfg.get("threshold_db", -50.0),
        min_silence_ms=tcfg.get("min_silence_ms", 60),
        peak_dbfs=tcfg.get("peak_dbfs", -1.0),
    )
    status["stage"] = "trimmed"

    # ---- deliverable artifacts ----
    manifest = {
        "run_id": run_id,
        "asset": os.path.basename(deliver),
        "format": fmt,
        "prompt": spec["prompt"],
        "provider": provider,
        "duration_s": report["out_duration_s"],
    }
    _write_json(os.path.join(deliver_dir, "manifest.json"), manifest)

    validation = {
        "trim_report": report,
        "silence_trimmed_s": round(report["src_duration_s"] - report["out_duration_s"], 3),
        "non_empty": report["out_duration_s"] > 0.0,
        "peak_normalized_to_dbfs": report["peak_target_dbfs"],
    }
    _write_json(os.path.join(deliver_dir, "validation_summary.json"), validation)

    status.update({"ok": validation["non_empty"], "stage": "done", "deliverable": deliver})
    _write_json(os.path.join(root, "artifact_status.json"), status)
    return status
