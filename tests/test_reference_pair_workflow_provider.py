from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.reference_pair_workflow import generate_with_provider, load_and_validate_spec, prepare_reference_pair_run


PNG_1X1_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a5f8AAAAASUVORK5CYII="
)


class _FakeHTTPResponse:
    def __init__(self, payload: dict):
        self._payload = json.dumps(payload).encode("utf-8")

    def read(self) -> bytes:
        return self._payload

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None


class ReferencePairWorkflowProviderTests(unittest.TestCase):
    def test_direct_imagegen_is_normalized_to_cliproxyapi_backend(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            reference_path = temp_path / "ref.png"
            reference_path.write_bytes(base64.b64decode(PNG_1X1_BASE64))
            spec_path = temp_path / "spec.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "schema_version": "reference_pair_workflow_v1",
                        "theme": "test floor",
                        "run_id": "test_floor",
                        "output_root": str(temp_path / "runs"),
                        "variants": ["full"],
                        "provider": {"name": "imagegen"},
                        "reference_pair": {"full": str(reference_path)},
                        "prompt_parts": {"style": "pixel stone floor"},
                        "background": {"mode": "transparent"},
                        "validation": {},
                    }
                ),
                encoding="utf-8",
            )

            spec, warnings = load_and_validate_spec(spec_path)
            self.assertEqual(spec["provider"]["name"], "cliproxyapi")
            self.assertEqual(spec["provider"]["mode"], "direct")
            self.assertEqual(spec["model"]["name"], "gpt-image-2")
            self.assertTrue(any("normalized" in warning for warning in warnings))

            prepare_result = prepare_reference_pair_run(spec_path)
            self.assertIsNone(prepare_result["agent_handoff_path"])

    def test_canonical_provider_and_model_are_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            reference_path = temp_path / "ref.png"
            reference_path.write_bytes(base64.b64decode(PNG_1X1_BASE64))
            spec_path = temp_path / "spec.json"
            spec_path.write_text(
                json.dumps(
                    {
                        "schema_version": "reference_pair_workflow_v1",
                        "theme": "test wall",
                        "run_id": "test_wall",
                        "output_root": str(temp_path / "runs"),
                        "variants": ["left"],
                        "provider": {"name": "cliproxyapi", "mode": "direct"},
                        "model": {"name": "gpt-image-2"},
                        "reference_pair": {"left": str(reference_path)},
                        "variant_profiles": {"left": {"selector_profile": "wall", "wall_side": "left", "height_units": 1, "reference_rotation": 90}},
                        "prompt_parts": {"style": "pixel stone wall"},
                        "background": {"mode": "transparent"},
                        "validation": {},
                    }
                ),
                encoding="utf-8",
            )

            spec, _ = load_and_validate_spec(spec_path)
            self.assertEqual(spec["provider"]["name"], "cliproxyapi")
            self.assertEqual(spec["model"]["name"], "gpt-image-2")

    @patch("pipeline.reference_pair_workflow._resolve_cli_proxy_api_settings")
    @patch("pipeline.reference_pair_workflow._probe_cli_proxy_api_capabilities")
    @patch("pipeline.reference_pair_workflow.urllib.request.urlopen")
    def test_cliproxyapi_provider_writes_edit_output(self, mock_urlopen, mock_probe, mock_settings) -> None:
        mock_settings.return_value = {
            "base_url": "http://127.0.0.1:8317/v1",
            "api_key": "local-dev-image-key",
            "config_path": "/Users/hunglingki/.cli-proxy-api/config.yaml",
        }
        mock_probe.return_value = {"endpoints": ["POST /v1/chat/completions", "GET /v1/models"]}
        mock_urlopen.return_value = _FakeHTTPResponse({"data": [{"b64_json": PNG_1X1_BASE64}]})

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            reference_path = temp_path / "ref.png"
            reference_path.write_bytes(base64.b64decode(PNG_1X1_BASE64))
            output_path = temp_path / "out.png"

            result = generate_with_provider(
                provider_name="cliproxyapi",
                model_name="gpt-image-2",
                prompt_text="edit this tile into stone",
                reference_images=[reference_path],
                output_path=output_path,
            )

            self.assertEqual(result["provider"], "cliproxyapi")
            self.assertEqual(result["request_mode"], "edit")
            self.assertTrue(output_path.exists())
            self.assertEqual(output_path.read_bytes(), base64.b64decode(PNG_1X1_BASE64))
            request = mock_urlopen.call_args.args[0]
            self.assertEqual(request.full_url, "http://127.0.0.1:8317/v1/images/edits")
            self.assertEqual(request.get_method(), "POST")
            self.assertEqual(request.get_header("Content-type"), "application/json")
            body = json.loads(request.data.decode("utf-8"))
            self.assertEqual(body["model"], "gpt-image-2")
            self.assertEqual(body["response_format"], "b64_json")
            self.assertTrue(body["images"][0]["image_url"].startswith("data:image/png;base64,"))


if __name__ == "__main__":
    unittest.main()
