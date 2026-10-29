"""Regression checks for the published ``roots`` console entry point."""

from __future__ import annotations

import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from roots.cli import main


class RootsCliTests(unittest.TestCase):
    def invoke(self, *args: str) -> tuple[int, dict[str, object] | None, str]:
        stdout = io.StringIO()
        stderr = io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            status = main(list(args))
        body = json.loads(stdout.getvalue()) if stdout.getvalue().strip() else None
        return status, body, stderr.getvalue()

    def test_entrypoint_is_importable(self) -> None:
        # pyproject.toml advertises roots.cli:main; packaging must not point to a 404.
        self.assertTrue(callable(main))

    def test_candidates_return_evidence_without_origin_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "records.jsonl"
            source.write_text(json.dumps({"id": "e1", "timestamp": "2026-10-28", "content": "Vera remembers this"}) + "\n")
            status, response, _ = self.invoke("candidates", "Vera", "--source", str(source))
        self.assertEqual(status, 0)
        assert response is not None
        self.assertEqual(response["operation"], "candidate_discovery")
        self.assertEqual(response["origin_status"], "NOT_ASSESSED")
        self.assertEqual(response["source_completeness"], "UNKNOWN")
        self.assertEqual(response["candidate_count"], 1)
        candidates = response["candidates"]
        assert isinstance(candidates, list)
        self.assertEqual(candidates[0]["record_id"], "e1")
        self.assertEqual(candidates[0]["event_time"]["precision"], "DAY")
        self.assertNotIn("content", candidates[0])

    def test_candidates_content_is_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "record.md"
            source.write_text("A private Vera candidate", encoding="utf-8")
            status, response, _ = self.invoke("candidates", "Vera", "--source", str(source), "--include-content")
        self.assertEqual(status, 0)
        assert response is not None
        self.assertEqual(response["candidates"][0]["content"], "A private Vera candidate")

    def test_candidates_limit_reports_truncation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "records.jsonl"
            source.write_text("\n".join(json.dumps({"id": str(i), "content": "Vera"}) for i in range(3)))
            status, response, _ = self.invoke("candidates", "Vera", "--source", str(source), "--limit", "1")
        self.assertEqual(status, 0)
        assert response is not None
        self.assertEqual(response["candidate_count"], 1)
        self.assertTrue(response["limit_reached"])

    def test_missing_and_unsupported_sources_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            status, _, stderr = self.invoke("candidates", "Vera", "--source", str(Path(tmp) / "missing.jsonl"))
            self.assertEqual(status, 2)
            self.assertIn("not a readable file", stderr)
            unsupported = Path(tmp) / "records.exe"
            unsupported.write_text("Vera")
            status, _, stderr = self.invoke("candidates", "Vera", "--source", str(unsupported))
            self.assertEqual(status, 2)
            self.assertIn("unsupported source", stderr)

    def test_module_cli_help_is_invokable(self) -> None:
        result = subprocess.run([sys.executable, "-m", "roots.cli", "--help"], capture_output=True, text=True, check=False)
        self.assertEqual(result.returncode, 0)
        self.assertIn("candidates", result.stdout)


if __name__ == "__main__":
    unittest.main()
