"""Mock-mode tests for tile_reskin_workflow_v1."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from pipeline.tile_reskin_workflow import (
    TileReskinWorkflowError,
    generate_tile_reskin,
    load_and_validate_tile_reskin_spec,
)

import pytest


def _make_source_tile(path: Path) -> None:
    """A 32x32 tile: gray core with a green band on the top edge (like an
    autotile 'top' overlay)."""
    img = Image.new("RGBA", (32, 32), (190, 190, 200, 255))
    px = img.load()
    for y in range(0, 6):
        for x in range(32):
            px[x, y] = (70, 150, 80, 255)
    img.save(path)


def _write_spec(tmp_path: Path, tiles_dir: Path) -> Path:
    spec = {
        "schema_version": "tile_reskin_workflow_v1",
        "run_id": "unit_reskin",
        "output_root": str(tmp_path / "out"),
        "provider": {"name": "mock", "mode": "mock"},
        "model": {"name": "mock"},
        "tile_size": 64,
        "source_tiles": {"dir": str(tiles_dir), "prefix": "road"},
        "materials": [
            {"id": "grass", "generate": {"prompt": "grass", "size": "128x128", "mock_color": "#4e8a3c"}},
            {"id": "road", "generate": {"prompt": "road", "size": "128x128", "mock_color": "#b9b9c8"}},
        ],
        "reskin": {
            "regions": [
                {"match": "green", "material": "grass", "soft": True},
                {"match": "else", "material": "road", "modulate_luma": True},
            ]
        },
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    return spec_path


def test_generate_tile_reskin_mock(tmp_path: Path) -> None:
    tiles_dir = tmp_path / "overlay"
    tiles_dir.mkdir()
    for name in ("road", "road_top"):
        _make_source_tile(tiles_dir / f"{name}.png")

    spec_path = _write_spec(tmp_path, tiles_dir)
    result = generate_tile_reskin(spec_path)

    assert result["ok"] is True
    assert result["variant_count"] == 2
    run_root = Path(result["run_root"])
    for name in ("road", "road_top"):
        out = run_root / "deliverables" / f"{name}.png"
        assert out.exists()
        img = Image.open(out).convert("RGBA")
        assert img.size == (64, 64)

    # the top band (green in source) should be re-skinned toward grass-green,
    # the core toward road-gray.
    top = Image.open(run_root / "deliverables" / "road_top.png").convert("RGBA").load()
    band = top[32, 4]
    core = top[32, 50]
    assert band[1] > band[0] and band[1] > band[2]  # greenish band
    assert abs(core[0] - core[2]) < 40 and core[0] > 120  # grayish core

    # seamless material tiles + proof sheets emitted
    assert (run_root / "step_2_material" / "grass_tile.png").exists()
    assert (run_root / "step_2_material" / "_proof_grass.png").exists()
    assert (run_root / "artifact_status.json").exists()


def test_reskin_requires_else_region(tmp_path: Path) -> None:
    tiles_dir = tmp_path / "overlay"
    tiles_dir.mkdir()
    _make_source_tile(tiles_dir / "road.png")
    spec = {
        "schema_version": "tile_reskin_workflow_v1",
        "run_id": "bad",
        "output_root": str(tmp_path / "out"),
        "provider": {"name": "mock", "mode": "mock"},
        "model": {"name": "mock"},
        "source_tiles": {"dir": str(tiles_dir), "prefix": "road"},
        "materials": [{"id": "road", "generate": {"prompt": "x", "size": "64x64"}}],
        "reskin": {"regions": [{"match": "green", "material": "road"}]},
    }
    spec_path = tmp_path / "spec.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    with pytest.raises(TileReskinWorkflowError):
        load_and_validate_tile_reskin_spec(spec_path)
