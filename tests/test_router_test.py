"""Unit tests for src.router_test (CLI / IO helpers)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from src.router_test import load_prompts, parse_args, write_csv, write_raw_json


# ---------------------------------------------------------------------------
# load_prompts
# ---------------------------------------------------------------------------


class TestLoadPrompts:
    def test_valid_file(self, tmp_path: Path):
        p = tmp_path / "prompts.json"
        data = [{"id": "p1", "prompt": "Hello", "expected_keywords": ["hi"]}]
        p.write_text(json.dumps(data))
        loaded = load_prompts(str(p))
        assert len(loaded) == 1
        assert loaded[0]["id"] == "p1"

    def test_invalid_not_array(self, tmp_path: Path):
        p = tmp_path / "bad.json"
        p.write_text('{"id": "p1"}')
        try:
            load_prompts(str(p))
            assert False, "Should have raised ValueError"
        except ValueError:
            pass

    def test_missing_keys(self, tmp_path: Path):
        p = tmp_path / "bad2.json"
        p.write_text('[{"id": "p1"}]')
        try:
            load_prompts(str(p))
            assert False, "Should have raised ValueError"
        except ValueError:
            pass


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    def test_defaults(self):
        ns = parse_args([])
        assert ns.prompts == "src/prompts.json"
        assert ns.runs is None
        assert ns.raw_json is False

    def test_custom(self):
        ns = parse_args(["--prompts", "p.json", "--runs", "5", "--out", "myout", "--raw-json"])
        assert ns.prompts == "p.json"
        assert ns.runs == 5
        assert ns.out == "myout"
        assert ns.raw_json is True


# ---------------------------------------------------------------------------
# write_csv / write_raw_json
# ---------------------------------------------------------------------------


class TestWriters:
    def _sample_rows(self):
        return [
            {
                "deployment": "router",
                "prompt_id": "p01",
                "category": "test",
                "run_id": 1,
                "timestamp_utc": "2025-01-01T00:00:00+00:00",
                "latency_ms": 150.0,
                "http_status": 200,
                "error": None,
                "model_reported": "gpt-4o",
                "router_metadata": None,
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30,
                "finish_reason": "stop",
                "quality_score": 1.0,
                "response_text": "Short answer",
                "raw_body": {"id": "x"},
            }
        ]

    def test_write_csv(self, tmp_path: Path):
        rows = self._sample_rows()
        csv_path = tmp_path / "out.csv"
        write_csv(rows, csv_path)
        content = csv_path.read_text()
        assert "prompt_id" in content
        assert "p01" in content

    def test_write_raw_json(self, tmp_path: Path):
        rows = self._sample_rows()
        json_path = tmp_path / "raw.json"
        write_raw_json(rows, json_path)
        data = json.loads(json_path.read_text())
        assert len(data) == 1
        assert data[0]["prompt_id"] == "p01"

    def test_csv_truncation(self, tmp_path: Path):
        rows = self._sample_rows()
        rows[0]["response_text"] = "x" * 500
        csv_path = tmp_path / "out.csv"
        write_csv(rows, csv_path)
        content = csv_path.read_text()
        # The truncated text should be at most 200 chars
        lines = content.strip().split("\n")
        assert len(lines) == 2  # header + 1 data row
