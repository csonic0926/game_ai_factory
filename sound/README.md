# game_sound_factory

Game **SFX factory**: text prompt -> generated sound -> **de-silenced + peak-fit**
deliverable. One of the three factories under the `game_ai_factory` umbrella
(alongside `game_asset_factory` and `game_story_factory`), and callable the same
way: a spec JSON + a CLI + run artifacts.

## Why the trim stage exists

ElevenLabs `sound-generation` returns clips padded with leading/trailing silence
and not peak-normalized — they never "just fit". The factory's **trim stage**
(ffmpeg `silenceremove` + peak-normalize) is what turns a raw generation into a
drop-in game asset. This is the sound factory's analog of the asset factory's
prop-cleanup step.

## Use

```bash
python3 sfx.py run --spec examples/door_open.spec.json          # generate + trim
python3 sfx.py run --spec examples/door_open.spec.json --provider mock   # offline smoke
python3 sfx.py trim --in raw.mp3 --out clean.wav                # trim an existing file
```

Start reading a run at `<output_root>/<run_id>/artifact_status.json`, then
`deliverables/`.

## Layout

```
sfx.py                       CLI (public order contract)
pipeline/
  credentials.py             ElevenLabs key (env or ~/.config/voicein/key)
  elevenlabs_provider.py     POST /v1/sound-generation (stdlib urllib)
  trim.py                    ffmpeg silenceremove + peak-normalize
  run.py                     generate -> trim -> deliverables + artifacts
examples/door_open.spec.json
docs/AI_CALLER_LANDING.md     start here if you are an AI caller
```

## Runtime

- Python 3.9+ (stdlib only; no pip deps)
- ffmpeg + ffprobe on PATH
- ElevenLabs key via `ELEVENLABS_API_KEY` or `~/.config/voicein/key`

## Providers

- `elevenlabs` (default) — the only real provider today; provider field is
  abstracted so more can be added without changing callers.
- `mock` — offline; synthesizes a silence-padded tone so the trim pipeline can
  be smoke-tested with no credits.
