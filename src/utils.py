"""Utility helpers for the Model Router testing tool."""

from __future__ import annotations

import json
import statistics
import time
from typing import Any

import httpx


# ---------------------------------------------------------------------------
# URL construction
# ---------------------------------------------------------------------------

def build_chat_url(endpoint: str, deployment: str, api_version: str) -> str:
    """Return the Azure OpenAI chat completions URL for *deployment*.

    >>> build_chat_url("https://res.openai.azure.com/", "myrouter", "2024-12-01-preview")
    'https://res.openai.azure.com/openai/deployments/myrouter/chat/completions?api-version=2024-12-01-preview'
    """
    base = endpoint.rstrip("/")
    return (
        f"{base}/openai/deployments/{deployment}"
        f"/chat/completions?api-version={api_version}"
    )


# ---------------------------------------------------------------------------
# HTTP call with retries
# ---------------------------------------------------------------------------

_RETRYABLE_STATUSES = {429, 500, 502, 503, 504}
_MAX_RETRIES = 3
_BACKOFF_BASE = 1.0  # seconds


def call_chat(
    client: httpx.Client,
    url: str,
    api_key: str,
    prompt: str,
    *,
    temperature: float = 0.2,
    max_tokens: int = 400,
    timeout: float = 60.0,
) -> dict[str, Any]:
    """Send a chat completion request with exponential-backoff retry.

    Returns a dict with keys:
        http_status, latency_ms, body (parsed JSON or None), error (str or None)
    """
    headers = {
        "api-key": api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    last_error: str | None = None
    last_status: int = 0

    for attempt in range(_MAX_RETRIES):
        try:
            start = time.perf_counter()
            resp = client.post(
                url,
                headers=headers,
                json=payload,
                timeout=timeout,
            )
            latency_ms = (time.perf_counter() - start) * 1000.0
            last_status = resp.status_code

            if resp.status_code in _RETRYABLE_STATUSES and attempt < _MAX_RETRIES - 1:
                wait = _BACKOFF_BASE * (2 ** attempt)
                last_error = f"HTTP {resp.status_code} (retrying in {wait:.1f}s)"
                time.sleep(wait)
                continue

            try:
                body = resp.json()
            except (json.JSONDecodeError, ValueError):
                body = None

            error = None if resp.is_success else resp.text[:500]
            return {
                "http_status": resp.status_code,
                "latency_ms": round(latency_ms, 2),
                "body": body,
                "error": error,
            }

        except httpx.TimeoutException:
            latency_ms = (time.perf_counter() - start) * 1000.0
            last_error = "timeout"
            last_status = 0
        except httpx.HTTPError as exc:
            latency_ms = (time.perf_counter() - start) * 1000.0
            last_error = str(exc)[:500]
            last_status = 0

        if attempt < _MAX_RETRIES - 1:
            time.sleep(_BACKOFF_BASE * (2 ** attempt))

    return {
        "http_status": last_status,
        "latency_ms": round(latency_ms, 2),
        "body": None,
        "error": last_error,
    }


# ---------------------------------------------------------------------------
# Response extraction
# ---------------------------------------------------------------------------

def extract_fields(body: dict[str, Any] | None) -> dict[str, Any]:
    """Pull useful fields out of a chat completion response body.

    Returns a dict with: model_reported, router_metadata, input_tokens,
    output_tokens, total_tokens, finish_reason, response_text.
    """
    defaults: dict[str, Any] = {
        "model_reported": None,
        "router_metadata": None,
        "input_tokens": None,
        "output_tokens": None,
        "total_tokens": None,
        "finish_reason": None,
        "response_text": None,
    }
    if body is None:
        return defaults

    defaults["model_reported"] = body.get("model")

    # Token usage
    usage = body.get("usage")
    if isinstance(usage, dict):
        defaults["input_tokens"] = usage.get("prompt_tokens")
        defaults["output_tokens"] = usage.get("completion_tokens")
        defaults["total_tokens"] = usage.get("total_tokens")

    # First choice
    choices = body.get("choices")
    if isinstance(choices, list) and choices:
        choice = choices[0]
        defaults["finish_reason"] = choice.get("finish_reason")
        msg = choice.get("message")
        if isinstance(msg, dict):
            defaults["response_text"] = msg.get("content")

    # Router metadata: capture anything beyond known top-level keys
    _KNOWN_KEYS = {"id", "object", "created", "model", "choices", "usage",
                    "system_fingerprint", "prompt_filter_results"}
    extra = {k: v for k, v in body.items() if k not in _KNOWN_KEYS}
    if extra:
        defaults["router_metadata"] = json.dumps(extra, default=str)

    return defaults


# ---------------------------------------------------------------------------
# Quality proxy
# ---------------------------------------------------------------------------

def keyword_score(response_text: str | None, expected: list[str]) -> float:
    """Return fraction of *expected* keywords found (case-insensitive).

    >>> keyword_score("The sky is blue because light scatters.", ["light", "scatter"])
    1.0
    >>> keyword_score("Hello world", ["light", "scatter"])
    0.0
    >>> keyword_score(None, ["a"])
    0.0
    >>> keyword_score("anything", [])
    1.0
    """
    if not expected:
        return 1.0
    if not response_text:
        return 0.0
    lower = response_text.lower()
    hits = sum(1 for kw in expected if kw.lower() in lower)
    return round(hits / len(expected), 4)


# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------

def compute_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute aggregate statistics from result rows.

    Returns dict with p50/p95 latency, avg tokens, error rate, avg quality.
    """
    latencies = [r["latency_ms"] for r in rows if r.get("latency_ms")]
    total_tok = [r["total_tokens"] for r in rows if r.get("total_tokens") is not None]
    errors = [r for r in rows if r.get("error")]
    scores = [r["quality_score"] for r in rows if r.get("quality_score") is not None]

    summary: dict[str, Any] = {
        "total_requests": len(rows),
        "errors": len(errors),
        "error_rate": round(len(errors) / max(len(rows), 1), 4),
    }

    if latencies:
        latencies_sorted = sorted(latencies)
        summary["p50_latency_ms"] = round(_percentile(latencies_sorted, 50), 2)
        summary["p95_latency_ms"] = round(_percentile(latencies_sorted, 95), 2)
    else:
        summary["p50_latency_ms"] = None
        summary["p95_latency_ms"] = None

    summary["avg_total_tokens"] = (
        round(statistics.mean(total_tok), 1) if total_tok else None
    )
    summary["avg_quality_score"] = (
        round(statistics.mean(scores), 4) if scores else None
    )

    return summary


def _percentile(sorted_data: list[float], pct: float) -> float:
    """Compute the *pct*-th percentile of already-sorted *sorted_data*."""
    if not sorted_data:
        return 0.0
    k = (len(sorted_data) - 1) * (pct / 100.0)
    f = int(k)
    c = f + 1
    if c >= len(sorted_data):
        return sorted_data[f]
    return sorted_data[f] + (k - f) * (sorted_data[c] - sorted_data[f])


def format_summary_table(summary: dict[str, Any]) -> str:
    """Return a human-readable summary table string."""
    lines = [
        "",
        "=" * 50,
        "  Model Router Test Summary",
        "=" * 50,
        f"  Total requests     : {summary['total_requests']}",
        f"  Errors             : {summary['errors']}",
        f"  Error rate         : {summary['error_rate']:.2%}",
        f"  p50 latency (ms)   : {summary['p50_latency_ms']}",
        f"  p95 latency (ms)   : {summary['p95_latency_ms']}",
        f"  Avg total tokens   : {summary['avg_total_tokens']}",
        f"  Avg quality score  : {summary['avg_quality_score']}",
        "=" * 50,
        "",
    ]
    return "\n".join(lines)
