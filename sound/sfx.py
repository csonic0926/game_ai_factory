#!/usr/bin/env python3
"""game_sound_factory CLI — the public order contract (mirrors game_asset_factory/itf.py).

Commands:
  run       generate + trim + deliverables from a spec         (the one AI usually calls)
  generate  generate raw SFX only (provider -> step_1_raw)
  trim      de-silence + peak-normalize a file                 (in/out, no provider)

Examples:
  python3 sfx.py run --spec examples/door_open.spec.json
  python3 sfx.py run --spec examples/door_open.spec.json --provider mock   # offline smoke
  python3 sfx.py trim --in raw.mp3 --out clean.wav
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import credentials, elevenlabs_provider, run as run_mod, trim  # noqa: E402


def cmd_run(args: argparse.Namespace) -> int:
    status = run_mod.run(args.spec, provider_override=args.provider)
    print(json.dumps(status, indent=2, ensure_ascii=False))
    return 0 if status.get("ok") else 1


def cmd_generate(args: argparse.Namespace) -> int:
    with open(args.spec, "r", encoding="utf-8") as f:
        spec = json.load(f)
    out = args.out or f"{spec['run_id']}.mp3"
    key = credentials.get_elevenlabs_key()
    n = elevenlabs_provider.generate(
        spec["prompt"], out, key,
        duration_seconds=spec.get("duration_seconds"),
        prompt_influence=spec.get("prompt_influence", 0.3),
        loop=spec.get("loop", False),
        model_id=spec.get("provider", {}).get("model"),
    )
    print(f"wrote {out} ({n} bytes)")
    return 0


def cmd_trim(args: argparse.Namespace) -> int:
    report = trim.trim_and_normalize(
        args.__dict__["in"], args.out,
        threshold_db=args.threshold_db,
        min_silence_ms=args.min_silence_ms,
        peak_dbfs=args.peak_dbfs,
    )
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(prog="sfx.py", description="game_sound_factory CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="generate + trim + deliverables from a spec")
    r.add_argument("--spec", required=True)
    r.add_argument("--provider", default=None, help="override provider (e.g. mock)")
    r.set_defaults(fn=cmd_run)

    g = sub.add_parser("generate", help="generate raw SFX only")
    g.add_argument("--spec", required=True)
    g.add_argument("--out", default=None)
    g.set_defaults(fn=cmd_generate)

    t = sub.add_parser("trim", help="de-silence + peak-normalize a file")
    t.add_argument("--in", required=True, dest="in")
    t.add_argument("--out", required=True)
    t.add_argument("--threshold-db", type=float, default=-50.0, dest="threshold_db")
    t.add_argument("--min-silence-ms", type=int, default=60, dest="min_silence_ms")
    t.add_argument("--peak-dbfs", type=float, default=-1.0, dest="peak_dbfs")
    t.set_defaults(fn=cmd_trim)

    args = ap.parse_args()
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
