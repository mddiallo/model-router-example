"""Unit tests for src.utils."""

from __future__ import annotations

import json

from src.utils import (
    build_chat_url,
    compute_summary,
    extract_fields,
    format_summary_table,
    keyword_score,
)


# ---------------------------------------------------------------------------
# build_chat_url
# ---------------------------------------------------------------------------


class TestBuildChatUrl:
    def test_basic(self):
        url = build_chat_url(
            "https://res.openai.azure.com/", "router1", "2024-12-01-preview"
        )
        assert url == (
            "https://res.openai.azure.com/openai/deployments/router1"
            "/chat/completions?api-version=2024-12-01-preview"
        )

    def test_strips_trailing_slash(self):
        url = build_chat_url(
            "https://res.openai.azure.com///", "d", "v1"
        )
        assert url.startswith("https://res.openai.azure.com/openai/")


# ---------------------------------------------------------------------------
# extract_fields
# ---------------------------------------------------------------------------


class TestExtractFields:
    def test_none_body(self):
        fields = extract_fields(None)
        assert fields["model_reported"] is None
        assert fields["response_text"] is None

    def test_full_body(self):
        body = {
            "id": "chatcmpl-123",
            "object": "chat.completion",
            "model": "gpt-4o-mini",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "Hello!"},
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
        }
        fields = extract_fields(body)
        assert fields["model_reported"] == "gpt-4o-mini"
        assert fields["input_tokens"] == 10
        assert fields["output_tokens"] == 5
        assert fields["total_tokens"] == 15
        assert fields["finish_reason"] == "stop"
        assert fields["response_text"] == "Hello!"
        assert fields["router_metadata"] is None  # no extra keys

    def test_extra_keys_captured(self):
        body = {
            "id": "x",
            "model": "m",
            "choices": [],
            "usage": {},
            "router_info": {"chosen": "gpt-4o"},
        }
        fields = extract_fields(body)
        assert fields["router_metadata"] is not None
        meta = json.loads(fields["router_metadata"])
        assert "router_info" in meta


# ---------------------------------------------------------------------------
# keyword_score
# ---------------------------------------------------------------------------


class TestKeywordScore:
    def test_all_match(self):
        assert keyword_score("light scatters at short wavelength", ["light", "scatter"]) == 1.0

    def test_none_match(self):
        assert keyword_score("hello world", ["light", "scatter"]) == 0.0

    def test_partial(self):
        assert keyword_score("light is bright", ["light", "scatter"]) == 0.5

    def test_case_insensitive(self):
        assert keyword_score("LIGHT scATTer", ["light", "scatter"]) == 1.0

    def test_none_text(self):
        assert keyword_score(None, ["a"]) == 0.0

    def test_empty_expected(self):
        assert keyword_score("anything", []) == 1.0


# ---------------------------------------------------------------------------
# compute_summary
# ---------------------------------------------------------------------------


class TestComputeSummary:
    def test_empty(self):
        s = compute_summary([])
        assert s["total_requests"] == 0
        assert s["error_rate"] == 0.0

    def test_basic(self):
        rows = [
            {"latency_ms": 100, "total_tokens": 20, "error": None, "quality_score": 1.0},
            {"latency_ms": 200, "total_tokens": 30, "error": None, "quality_score": 0.5},
            {"latency_ms": 300, "total_tokens": None, "error": "timeout", "quality_score": 0.0},
        ]
        s = compute_summary(rows)
        assert s["total_requests"] == 3
        assert s["errors"] == 1
        assert s["avg_total_tokens"] == 25.0
        assert s["p50_latency_ms"] is not None


# ---------------------------------------------------------------------------
# format_summary_table
# ---------------------------------------------------------------------------


class TestFormatSummaryTable:
    def test_returns_string(self):
        s = compute_summary([])
        table = format_summary_table(s)
        assert "Model Router Test Summary" in table
