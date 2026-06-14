#!/usr/bin/env python3
"""Tile re-skin workflow (tile_reskin_workflow_v1).

Re-skin an EXISTING, geometrically-correct tile set (autotile variants whose
shapes/edges already connect) into a new material look, WITHOUT regenerating
geometry. Each source tile's pixel regions are classified by color and remapped
to new seamless materials, modulated by the original luma so painted edges,
curbs, foam, and 3D shading survive. Because geometry is never touched, seamless
tiling and autotile connectivity are preserved by construction.

This handles the "already have correct geometry, now re-skin" half of tile work.
Generating geometrically-correct tile sets from scratch is out of scope here.

Pipeline:
  step_1_field      one flat-lit material FIELD per material (generated or supplied)
  step_2_material   one seamless tile cut from each field (toroidal seal)
  step_3_reskin     every source variant re-skinned via region classification
  deliverables      final re-skinned PNGs ready to copy into a game repo

Pure Pillow (no numpy); tiles are small so per-pixel Python is fine.
"""

from __future__ import annotations

import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Sequence

from PIL import Image

from pipeline.reference_pair_workflow import (
    generate_with_provider,
    update_step_status_summary,
)


class TileReskinWorkflowError(RuntimeError):
    pass


SCHEMA_VERSION = "tile_reskin_workflow_v1"
DEFAULT_TILE_SIZE = 64
DEFAULT_FIELD_SIZE = "1024x1024"
GPT_IMAGE_DEFAULT_MODEL = "gpt-image-2"


# ----------------------------------------------------------------------------
# small io helpers (kept local so this module stays self-contained)
# ----------------------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def require_non_empty_string(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise TileReskinWorkflowError(f"{label} must be a non-empty string.")
    return value.strip()


# ----------------------------------------------------------------------------
# pixel classifiers — operate on (r, g, b) 0..255, return soft weight 0..1
# ----------------------------------------------------------------------------

def _w_green(r: int, g: int, b: int) -> float:
    return max(0.0, min(1.0, (min(g - r, g - b) - 2) / 12.0))


def _w_foam(r: int, g: int, b: int) -> float:
    return 1.0 if (r > 185 and g > 195 and b > 195) else 0.0


def _w_sandy(r: int, g: int, b: int) -> float:
    return 1.0 if (r > 150 and g > 120 and b < 165 and r >= b and _w_green(r, g, b) < 0.5) else 0.0


def _w_blue(r: int, g: int, b: int) -> float:
    return 1.0 if (b >= r and b > 90 and _w_foam(r, g, b) < 0.5) else 0.0


def _w_brown(r: int, g: int, b: int) -> float:
    return 1.0 if (r > g and g > b and r < 170) else 0.0


def _w_gray(r: int, g: int, b: int) -> float:
    return 1.0 if (abs(r - g) < 18 and abs(g - b) < 18 and _w_foam(r, g, b) < 0.5) else 0.0


def _w_dark(r: int, g: int, b: int) -> float:
    return 1.0 if max(r, g, b) < 60 else 0.0


def _w_cream(r: int, g: int, b: int) -> float:
    # warm light low-saturation surface (plaster / parchment)
    mx = max(r, g, b)
    mn = min(r, g, b)
    sat = (mx - mn) / mx if mx else 0.0
    return 1.0 if (mx > 150 and r >= b and sat < 0.42 and _w_dark(r, g, b) < 0.5) else 0.0


def _w_light(r: int, g: int, b: int) -> float:
    return 1.0 if max(r, g, b) > 175 else 0.0


_CLASSIFIERS: dict[str, Callable[[int, int, int], float]] = {
    "green": _w_green,
    "foam": _w_foam,
    "sandy": _w_sandy,
    "blue": _w_blue,
    "brown": _w_brown,
    "gray": _w_gray,
    "dark": _w_dark,
    "cream": _w_cream,
    "light": _w_light,
}


def _rgb_to_hsv(r: int, g: int, b: int) -> tuple[float, float, float]:
    rf, gf, bf = r / 255.0, g / 255.0, b / 255.0
    mx, mn = max(rf, gf, bf), min(rf, gf, bf)
    d = mx - mn
    if d == 0:
        h = 0.0
    elif mx == rf:
        h = ((gf - bf) / d) % 6
    elif mx == gf:
        h = (bf - rf) / d + 2
    else:
        h = (rf - gf) / d + 4
    h *= 60.0
    if h < 0:
        h += 360.0
    return h, (d / mx if mx else 0.0), mx


def _make_hsv_classifier(spec: dict[str, Any]) -> Callable[[int, int, int], float]:
    """Build a classifier from an HSV-range object:
    {"hue": [min,max], "sat": [min,max], "val": [min,max]} (any subset).
    hue range may wrap (min>max). Returns a hard 0/1 weight."""
    hue = spec.get("hue")
    sat = spec.get("sat")
    val = spec.get("val")

    def classify(r: int, g: int, b: int) -> float:
        h, s, v = _rgb_to_hsv(r, g, b)
        if hue is not None:
            lo, hi = float(hue[0]), float(hue[1])
            inside = (lo <= h <= hi) if lo <= hi else (h >= lo or h <= hi)
            if not inside:
                return 0.0
        if sat is not None and not (float(sat[0]) <= s <= float(sat[1])):
            return 0.0
        if val is not None and not (float(val[0]) <= v <= float(val[1])):
            return 0.0
        return 1.0

    return classify


def _luma(r: int, g: int, b: int) -> float:
    return 0.299 * r + 0.587 * g + 0.114 * b


# ----------------------------------------------------------------------------
# spec normalization
# ----------------------------------------------------------------------------

def _normalize_provider(raw: Any) -> tuple[str, str, str]:
    if not isinstance(raw, dict):
        raise TileReskinWorkflowError("spec.provider must be an object with a name.")
    name = require_non_empty_string(raw.get("name"), "spec.provider.name").lower()
    mode = str(raw.get("mode") or "direct").strip().lower()
    if name == "mock":
        return "mock", "mock", "mock"
    if name in {"gpt_image", "cliproxyapi", "imagegen", "gpt_image_2"}:
        return "cliproxyapi", "direct", GPT_IMAGE_DEFAULT_MODEL
    if name in {"gemini_cli", "nano_banana", "nano_banana_pro"}:
        model = "nano-banana-pro" if name == "nano_banana_pro" else "nano-banana-2"
        return "gemini_cli", "direct", model
    return name, mode, ""


def _normalize_model(raw: Any, backend: str, default_model: str) -> str:
    if isinstance(raw, dict) and raw.get("name"):
        return str(raw["name"]).strip()
    return default_model or ("mock" if backend == "mock" else GPT_IMAGE_DEFAULT_MODEL)


def _resolve_source_variants(spec: dict[str, Any], spec_dir: Path) -> tuple[Path, list[str]]:
    src = spec.get("source_tiles")
    if not isinstance(src, dict):
        raise TileReskinWorkflowError("spec.source_tiles must be an object with a dir.")
    raw_dir = require_non_empty_string(src.get("dir"), "spec.source_tiles.dir")
    tiles_dir = Path(raw_dir).expanduser()
    if not tiles_dir.is_absolute():
        tiles_dir = (spec_dir / tiles_dir).resolve()
    if not tiles_dir.is_dir():
        raise TileReskinWorkflowError(f"source_tiles.dir does not exist: {tiles_dir}")
    variants = src.get("variants")
    if isinstance(variants, list) and variants:
        names = [require_non_empty_string(v, "source_tiles.variants[]") for v in variants]
    else:
        prefix = src.get("prefix")
        if not isinstance(prefix, str) or not prefix:
            raise TileReskinWorkflowError("source_tiles needs either 'variants' (list) or 'prefix' (string).")
        names = sorted(
            p.stem for p in tiles_dir.glob("*.png")
            if p.stem == prefix or p.stem.startswith(prefix + "_")
        )
        if not names:
            raise TileReskinWorkflowError(f"no PNG tiles matched prefix '{prefix}' in {tiles_dir}")
    for name in names:
        if not (tiles_dir / f"{name}.png").exists():
            raise TileReskinWorkflowError(f"source tile missing: {tiles_dir / (name + '.png')}")
    return tiles_dir, names


def _normalize_materials(spec: dict[str, Any], spec_dir: Path) -> list[dict[str, Any]]:
    raw = spec.get("materials")
    if not isinstance(raw, list) or not raw:
        raise TileReskinWorkflowError("spec.materials must be a non-empty list.")
    materials: list[dict[str, Any]] = []
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise TileReskinWorkflowError(f"spec.materials[{index}] must be an object.")
        mat_id = require_non_empty_string(item.get("id"), f"materials[{index}].id")
        entry: dict[str, Any] = {"id": mat_id}
        if item.get("field"):
            field_path = Path(str(item["field"])).expanduser()
            if not field_path.is_absolute():
                field_path = (spec_dir / field_path).resolve()
            entry["field"] = field_path
        elif item.get("tile"):
            tile_path = Path(str(item["tile"])).expanduser()
            if not tile_path.is_absolute():
                tile_path = (spec_dir / tile_path).resolve()
            entry["tile"] = tile_path
        elif isinstance(item.get("generate"), dict):
            gen = item["generate"]
            entry["generate"] = {
                "prompt": require_non_empty_string(gen.get("prompt"), f"materials[{index}].generate.prompt"),
                "size": str(gen.get("size") or DEFAULT_FIELD_SIZE),
            }
            if gen.get("color_ref"):
                ref = Path(str(gen["color_ref"])).expanduser()
                if not ref.is_absolute():
                    ref = (spec_dir / ref).resolve()
                entry["generate"]["color_ref"] = ref
            if gen.get("mock_color"):
                entry["generate"]["mock_color"] = str(gen["mock_color"])
        else:
            raise TileReskinWorkflowError(
                f"materials[{index}] needs one of: 'field', 'tile', or 'generate'."
            )
        materials.append(entry)
    return materials


def _normalize_regions(spec: dict[str, Any], material_ids: set[str]) -> list[dict[str, Any]]:
    raw = spec.get("reskin")
    if not isinstance(raw, dict):
        raise TileReskinWorkflowError("spec.reskin must be an object with a 'regions' list.")
    regions_raw = raw.get("regions")
    if not isinstance(regions_raw, list) or not regions_raw:
        raise TileReskinWorkflowError("spec.reskin.regions must be a non-empty list.")
    regions: list[dict[str, Any]] = []
    saw_else = False
    for index, item in enumerate(regions_raw):
        if not isinstance(item, dict):
            raise TileReskinWorkflowError(f"reskin.regions[{index}] must be an object.")
        raw_match = item.get("match")
        is_hsv = isinstance(raw_match, dict)
        if is_hsv:
            match_key = "green"  # placeholder, never used; hsv classifier attached below
            region: dict[str, Any] = {"match": "_hsv", "hsv": raw_match}
        else:
            match = require_non_empty_string(raw_match, f"reskin.regions[{index}].match").lower()
            if match != "else" and match not in _CLASSIFIERS:
                raise TileReskinWorkflowError(
                    f"reskin.regions[{index}].match '{match}' unknown. "
                    f"Use 'else', an HSV-range object, or one of: {', '.join(sorted(_CLASSIFIERS))}."
                )
            match_key = match
            region = {"match": match}
        if item.get("keep"):
            region["keep"] = True
        else:
            material = require_non_empty_string(item.get("material"), f"reskin.regions[{index}].material")
            if material not in material_ids:
                raise TileReskinWorkflowError(
                    f"reskin.regions[{index}].material '{material}' is not a declared material id."
                )
            region["material"] = material
            region["modulate_luma"] = bool(item.get("modulate_luma", False))
            region["soft"] = bool(item.get("soft", match_key == "green"))
        if (not is_hsv) and match_key == "else":
            saw_else = True
        regions.append(region)
    if not saw_else:
        raise TileReskinWorkflowError("reskin.regions must include a final {\"match\": \"else\", ...} region.")
    return regions


def load_and_validate_tile_reskin_spec(spec_path: Path) -> dict[str, Any]:
    raw = load_json(spec_path)
    if str(raw.get("schema_version")) != SCHEMA_VERSION:
        raise TileReskinWorkflowError(
            f"spec.schema_version must be '{SCHEMA_VERSION}', got '{raw.get('schema_version')}'."
        )
    spec_dir = spec_path.parent
    run_id = require_non_empty_string(raw.get("run_id"), "spec.run_id")
    output_root = require_non_empty_string(raw.get("output_root"), "spec.output_root")
    output_root_path = Path(output_root).expanduser()
    if not output_root_path.is_absolute():
        output_root_path = (spec_dir / output_root_path).resolve()
    backend, mode, default_model = _normalize_provider(raw.get("provider"))
    model = _normalize_model(raw.get("model"), backend, default_model)
    tiles_dir, variants = _resolve_source_variants(raw, spec_dir)
    materials = _normalize_materials(raw, spec_dir)
    material_ids = {m["id"] for m in materials}
    regions = _normalize_regions(raw, material_ids)
    tile_size = int(raw.get("tile_size") or DEFAULT_TILE_SIZE)
    seal_band = float(raw.get("seal_band") or 0.25)
    crop_frac = float(raw.get("crop_frac") or 0.2)
    return {
        "run_id": run_id,
        "run_root": output_root_path / run_id,
        "backend": backend,
        "provider_mode": mode,
        "model": model,
        "tiles_dir": tiles_dir,
        "variants": variants,
        "materials": materials,
        "regions": regions,
        "tile_size": tile_size,
        "seal_band": seal_band,
        "crop_frac": crop_frac,
    }


# ----------------------------------------------------------------------------
# image ops
# ----------------------------------------------------------------------------

def _smoothstep(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


def _seamless_tile_from_field(field: Image.Image, *, tile_size: int, crop_frac: float, seal_band: float) -> Image.Image:
    """Cut one seamless square tile from a flat material field via toroidal
    offset + narrow edge feather, then resize to tile_size."""
    field = field.convert("RGBA")
    W, H = field.size
    crop = max(8, int(min(W, H) * crop_frac))
    cx = (W - crop) // 2
    cy = (H - crop) // 2
    region = field.crop((cx, cy, cx + crop, cy + crop))
    N = crop
    px = region.load()
    half = N // 2
    band = max(1, int(half * seal_band))
    out = Image.new("RGBA", (N, N))
    op = out.load()
    for y in range(N):
        dy = min(y, N - 1 - y)
        ay = _smoothstep(dy / band)
        oy = (y + half) % N
        for x in range(N):
            dx = min(x, N - 1 - x)
            a = _smoothstep(dx / band) * ay
            ox = (x + half) % N
            c1 = px[x, y]
            c2 = px[ox, oy]
            op[x, y] = tuple(int(round(c1[k] * a + c2[k] * (1 - a))) for k in range(4))
    if N != tile_size:
        out = out.resize((tile_size, tile_size), Image.LANCZOS)
    return out


def _proof_sheet(tile: Image.Image, out_path: Path) -> None:
    n = tile.width
    sheet = Image.new("RGBA", (n * 3, n * 3))
    for r in range(3):
        for c in range(3):
            sheet.paste(tile, (c * n, r * n))
    sheet.save(out_path)


def _mean_luma_where(src: Image.Image, predicate: Callable[[int, int, int], bool]) -> float:
    px = src.load()
    total = 0.0
    count = 0
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = px[x, y]
            if a < 200:
                continue
            if predicate(r, g, b):
                total += _luma(r, g, b)
                count += 1
    return (total / count) if count else 128.0


def _reskin_variant(
    *,
    original: Image.Image,
    regions: Sequence[dict[str, Any]],
    material_tiles: dict[str, Image.Image],
    tile_size: int,
) -> Image.Image:
    src = original.convert("RGBA").resize((tile_size, tile_size), Image.NEAREST)
    sp = src.load()
    mats = {mid: tile.load() for mid, tile in material_tiles.items()}
    out = Image.new("RGBA", (tile_size, tile_size))
    op = out.load()

    def classifier_for(region: dict[str, Any]) -> Callable[[int, int, int], float]:
        if region["match"] == "_hsv":
            return _make_hsv_classifier(region["hsv"])
        return _CLASSIFIERS[region["match"]]

    clfs = {ri: (None if region["match"] == "else" else classifier_for(region)) for ri, region in enumerate(regions)}

    # per-region mean luma over its own classified pixels (for modulate_luma)
    region_mean: dict[int, float] = {}
    for ri, region in enumerate(regions):
        if region.get("modulate_luma"):
            clf = clfs[ri]
            if clf is None:
                pred = lambda r, g, b: True  # noqa: E731
            else:
                pred = lambda r, g, b, _c=clf: _c(r, g, b) >= 0.5  # noqa: E731
            region_mean[ri] = _mean_luma_where(src, pred)

    for y in range(tile_size):
        for x in range(tile_size):
            r, g, b, a = sp[x, y]
            # base = the 'else' region
            cur = None
            for ri, region in enumerate(regions):
                if region["match"] == "else":
                    cur = _region_pixel(region, ri, x, y, r, g, b, mats, region_mean)
                    break
            if cur is None:
                cur = (r, g, b)
            # overlay earlier regions in order (skip else)
            for ri, region in enumerate(regions):
                if region["match"] == "else":
                    continue
                clf = clfs[ri]
                w = clf(r, g, b)
                if region.get("soft"):
                    if w <= 0:
                        continue
                else:
                    w = 1.0 if w >= 0.5 else 0.0
                    if w <= 0:
                        continue
                if region.get("keep"):
                    repl = (r, g, b)
                else:
                    repl = _region_pixel(region, ri, x, y, r, g, b, mats, region_mean)
                cur = tuple(int(round(repl[k] * w + cur[k] * (1 - w))) for k in range(3))
            op[x, y] = (cur[0], cur[1], cur[2], a)
    return out


def _region_pixel(region, ri, x, y, r, g, b, mats, region_mean):
    if region.get("keep"):
        return (r, g, b)
    mat = mats[region["material"]]
    mr, mg, mb, _ = mat[x, y]
    if region.get("modulate_luma"):
        mean = region_mean.get(ri, 128.0) or 128.0
        fac = max(0.45, min(1.5, _luma(r, g, b) / mean))
        return (min(255, int(mr * fac)), min(255, int(mg * fac)), min(255, int(mb * fac)))
    return (mr, mg, mb)


def _mock_field(size_text: str, color_hex: str | None) -> Image.Image:
    try:
        w_text, h_text = size_text.lower().split("x")
        w, h = int(w_text), int(h_text)
    except Exception:
        w, h = 1024, 1024
    color = (120, 150, 110)
    if color_hex and color_hex.startswith("#") and len(color_hex) == 7:
        color = tuple(int(color_hex[i : i + 2], 16) for i in (1, 3, 5))
    img = Image.new("RGBA", (w, h), (*color, 255))
    # faint checker so the seamless seal has something to work on
    px = img.load()
    for y in range(0, h, 8):
        for x in range(0, w, 8):
            if ((x // 8) + (y // 8)) % 2 == 0:
                for dy in range(8):
                    for dx in range(8):
                        if x + dx < w and y + dy < h:
                            cr, cg, cb, ca = px[x + dx, y + dy]
                            px[x + dx, y + dy] = (max(0, cr - 12), max(0, cg - 12), max(0, cb - 12), ca)
    return img


# ----------------------------------------------------------------------------
# run directories
# ----------------------------------------------------------------------------

def build_run_directories(run_root: Path) -> dict[str, Path]:
    dirs = {
        "run_root": run_root,
        "step_1_field": run_root / "step_1_field",
        "step_2_material": run_root / "step_2_material",
        "step_3_reskin": run_root / "step_3_reskin",
        "deliverables": run_root / "deliverables",
        "logs": run_root / "logs",
        "request": run_root / "request",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


# ----------------------------------------------------------------------------
# public entry points
# ----------------------------------------------------------------------------

def prepare_tile_reskin_run(spec_path: Path) -> dict[str, Any]:
    spec = load_and_validate_tile_reskin_spec(spec_path)
    dirs = build_run_directories(spec["run_root"])
    write_json(dirs["request"] / "request.json", {
        "schema_version": SCHEMA_VERSION,
        "run_id": spec["run_id"],
        "backend": spec["backend"],
        "model": spec["model"],
        "tiles_dir": str(spec["tiles_dir"]),
        "variants": spec["variants"],
        "materials": [m["id"] for m in spec["materials"]],
        "regions": spec["regions"],
        "tile_size": spec["tile_size"],
        "prepared_at": now_iso(),
    })
    return {
        "run_root": str(spec["run_root"]),
        "variants": spec["variants"],
        "materials": [m["id"] for m in spec["materials"]],
    }


def generate_tile_reskin(spec_path: Path) -> dict[str, Any]:
    spec = load_and_validate_tile_reskin_spec(spec_path)
    dirs = build_run_directories(spec["run_root"])
    run_root = spec["run_root"]
    tile_size = spec["tile_size"]

    # --- materials: obtain a seamless tile per material id ---
    material_tiles: dict[str, Image.Image] = {}
    material_logs: dict[str, Any] = {}
    for material in spec["materials"]:
        mid = material["id"]
        if "tile" in material:
            tile_img = Image.open(material["tile"]).convert("RGBA").resize((tile_size, tile_size), Image.LANCZOS)
            material_tiles[mid] = tile_img
            tile_img.save(dirs["step_2_material"] / f"{mid}_tile.png")
            material_logs[mid] = {"source": "supplied_tile", "path": str(material["tile"])}
            continue
        if "field" in material:
            field_path = material["field"]
            material_logs[mid] = {"source": "supplied_field", "path": str(material["field"])}
        else:
            gen = material["generate"]
            field_path = dirs["step_1_field"] / f"{mid}_field.png"
            if spec["backend"] == "mock":
                _mock_field(gen["size"], gen.get("mock_color")).save(field_path)
                material_logs[mid] = {"source": "mock_field", "size": gen["size"]}
            else:
                refs = [gen["color_ref"]] if gen.get("color_ref") else []
                generate_with_provider(
                    provider_name=spec["backend"],
                    model_name=spec["model"],
                    prompt_text=gen["prompt"],
                    reference_images=refs,
                    output_path=field_path,
                    size_override=gen["size"],
                )
                material_logs[mid] = {"source": "generated", "size": gen["size"], "color_ref": bool(refs)}
        field_img = Image.open(field_path).convert("RGBA")
        tile_img = _seamless_tile_from_field(
            field_img, tile_size=tile_size, crop_frac=spec["crop_frac"], seal_band=spec["seal_band"]
        )
        material_tiles[mid] = tile_img
        tile_img.save(dirs["step_2_material"] / f"{mid}_tile.png")
        _proof_sheet(tile_img, dirs["step_2_material"] / f"_proof_{mid}.png")
        update_step_status_summary(
            run_root, variant=mid, step_key="step_2_material", status="ok",
            summary=f"seamless {mid} tile {tile_size}x{tile_size}",
            primary_artifact=str(dirs["step_2_material"] / f"{mid}_tile.png"),
        )

    # --- re-skin every source variant ---
    deliver: list[str] = []
    for name in spec["variants"]:
        original = Image.open(spec["tiles_dir"] / f"{name}.png")
        reskinned = _reskin_variant(
            original=original,
            regions=spec["regions"],
            material_tiles=material_tiles,
            tile_size=tile_size,
        )
        step_path = dirs["step_3_reskin"] / f"{name}.png"
        reskinned.save(step_path)
        deliver_path = dirs["deliverables"] / f"{name}.png"
        reskinned.save(deliver_path)
        deliver.append(str(deliver_path))
        update_step_status_summary(
            run_root, variant=name, step_key="step_3_reskin", status="ok",
            summary=f"re-skinned {name}", primary_artifact=str(deliver_path),
        )

    result = {
        "ok": True,
        "run_root": str(run_root),
        "tile_size": tile_size,
        "materials": material_logs,
        "deliverables": deliver,
        "variant_count": len(deliver),
        "finished_at": now_iso(),
    }
    write_json(dirs["logs"] / "generate.json", result)
    write_json(run_root / "deliverables" / "manifest.json", {
        "run_id": spec["run_id"],
        "tile_size": tile_size,
        "variants": spec["variants"],
    })
    return result
