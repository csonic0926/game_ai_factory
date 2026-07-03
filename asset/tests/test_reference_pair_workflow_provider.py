from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pipeline.reference_pair_workflow import (
    ReferencePairWorkflowError,
    _probe_cli_proxy_api_capabilities,
    generate_with_provider,
    load_and_validate_spec,
    prepare_reference_pair_run,
)


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

    def test_agent_handoff_packet_includes_codex_exec_persistence_contract(self) -> None:
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
                        "run_id": "test_floor_handoff",
                        "output_root": str(temp_path / "runs"),
                        "variants": ["full"],
                        "provider": {"name": "agent_handoff", "mode": "agent_handoff"},
                        "model": {"name": "gpt-image-2"},
                        "reference_pair": {"full": str(reference_path)},
                        "prompt_parts": {"style": "pixel stone floor"},
                        "background": {"mode": "transparent"},
                        "validation": {},
                    }
                ),
                encoding="utf-8",
            )

            prepare_result = prepare_reference_pair_run(spec_path)
            handoff_path = Path(prepare_result["agent_handoff_path"])
            handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
            task = handoff["tasks"]["full"]

            self.assertTrue(handoff["primary_for_codex_agent_callers"])
            self.assertTrue(handoff["one_variant_per_session"])
            self.assertIn("image_gen.imagegen", task["codex_exec_prompt_text"])
            self.assertIn("Do NOT hand-draw", task["codex_exec_prompt_text"])
            self.assertIn("ls -la", task["codex_exec_prompt_text"])
            self.assertIn(task["output_path"], task["codex_exec_prompt_text"])
            self.assertIn("< /dev/null", task["codex_exec_shell_command"])
            self.assertIn("--sandbox workspace-write", task["codex_exec_shell_command"])
            self.assertEqual(task["output_path"], str(Path(prepare_result["run_root"]) / "agent_handoff" / "step_1_raw" / "full.png"))

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

    @patch("pipeline.reference_pair_workflow.urllib.request.urlopen")
    def test_cliproxyapi_probe_uses_models_health_endpoint(self, mock_urlopen) -> None:
        mock_urlopen.return_value = _FakeHTTPResponse({"data": [{"id": "gpt-image-2"}]})

        payload = _probe_cli_proxy_api_capabilities(
            base_url="http://127.0.0.1:8317/v1",
            api_key="local-dev-image-key",
            timeout=4,
        )

        self.assertTrue(payload["_ok"])
        self.assertEqual(payload["probe_url"], "http://127.0.0.1:8317/v1/models")
        request = mock_urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "http://127.0.0.1:8317/v1/models")
        self.assertEqual(request.get_method(), "GET")

    @patch("pipeline.reference_pair_workflow._resolve_cli_proxy_api_settings")
    @patch("pipeline.reference_pair_workflow._probe_cli_proxy_api_capabilities")
    def test_cliproxyapi_provider_fails_with_actionable_proxy_start_error(self, mock_probe, mock_settings) -> None:
        mock_settings.return_value = {
            "base_url": "http://127.0.0.1:8317/v1",
            "api_key": "local-dev-image-key",
            "config_path": "/Users/hunglingki/.cli-proxy-api/config.yaml",
        }
        mock_probe.return_value = {
            "_ok": False,
            "probe_url": "http://127.0.0.1:8317/v1/models",
            "error_type": "URLError",
            "error": "[Errno 61] Connection refused",
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "out.png"
            with self.assertRaises(ReferencePairWorkflowError) as context:
                generate_with_provider(
                    provider_name="cliproxyapi",
                    model_name="gpt-image-2",
                    prompt_text="generate a tile",
                    reference_images=[],
                    output_path=output_path,
                )

        message = str(context.exception)
        self.assertIn("cli-proxy not running", message)
        self.assertIn("http://127.0.0.1:8317/v1/models", message)
        self.assertIn("gpt-image-2", message)
        self.assertIn("cliproxyapi", message)
        self.assertIn("--config /Users/hunglingki/.cli-proxy-api/config.yaml", message)


if __name__ == "__main__":
    unittest.main()
