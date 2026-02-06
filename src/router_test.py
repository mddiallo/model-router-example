"""CLI tool to test Azure AI Foundry Model Router behavior.

Usage:
    python -m src.router_test --prompts src/prompts.json --runs 3 --out out/
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx
from dotenv import load_dotenv

from .utils import (
    build_chat_url,
    call_chat,
    compute_summary,
    extract_fields,
    format_summary_table,
    keyword_score,
)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_CSV_RESPONSE_TRUNCATE = 200  # max chars of response_text stored in CSV


def _load_config() -> dict:
    """Load configuration from environment variables (with .env support)."""
    load_dotenv()

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT") or os.getenv("FOUNDRY_ENDPOINT", "")
    api_key = os.getenv("AZURE_OPENAI_API_KEY") or os.getenv("FOUNDRY_API_KEY", "")
    api_version = os.getenv("API_VERSION", "2024-12-01-preview")
    deployment = os.getenv("DEPLOYMENT_NAME", "")
    mode = os.getenv("MODE", "balanced")
    runs = int(os.getenv("RUNS_PER_PROMPT", "3"))
    timeout = float(os.getenv("TIMEOUT_S", "60"))
    output_dir = os.getenv("OUTPUT_DIR", "./out")

    return {
        "endpoint": endpoint,
        "api_key": api_key,
        "api_version": api_version,
        "deployment": deployment,
        "mode": mode,
        "runs": runs,
        "timeout": timeout,
        "output_dir": output_dir,
    }


# ---------------------------------------------------------------------------
# Prompt loading
# ---------------------------------------------------------------------------


def load_prompts(path: str) -> list[dict]:
    """Load and validate prompts from a JSON file."""
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError(f"Prompts file must be a JSON array, got {type(data).__name__}")

    for i, item in enumerate(data):
        if "id" not in item or "prompt" not in item:
            raise ValueError(f"Prompt at index {i} missing required 'id' or 'prompt' key")

    return data


# ---------------------------------------------------------------------------
# Main test loop
# ---------------------------------------------------------------------------


def run_tests(
    prompts: list[dict],
    *,
    url: str,
    api_key: str,
    runs: int,
    timeout: float,
    deployment_label: str = "router",
) -> list[dict]:
    """Execute test runs and return a list of result rows."""
    rows: list[dict] = []
    total = len(prompts) * runs

    with httpx.Client() as client:
        counter = 0
        for prompt_item in prompts:
            pid = prompt_item["id"]
            prompt_text = prompt_item["prompt"]
            expected_kw = prompt_item.get("expected_keywords", [])

            for run_idx in range(1, runs + 1):
                counter += 1
                ts = datetime.now(timezone.utc).isoformat()
                print(
                    f"  [{counter}/{total}] {deployment_label} | "
                    f"prompt={pid} run={run_idx} ...",
                    end=" ",
                    flush=True,
                )

                result = call_chat(
                    client, url, api_key, prompt_text, timeout=timeout
                )
                fields = extract_fields(result["body"])
                score = keyword_score(fields["response_text"], expected_kw)

                row = {
                    "deployment": deployment_label,
                    "prompt_id": pid,
                    "category": prompt_item.get("category", ""),
                    "run_id": run_idx,
                    "timestamp_utc": ts,
                    "latency_ms": result["latency_ms"],
                    "http_status": result["http_status"],
                    "error": result["error"],
                    "model_reported": fields["model_reported"],
                    "router_metadata": fields["router_metadata"],
                    "input_tokens": fields["input_tokens"],
                    "output_tokens": fields["output_tokens"],
                    "total_tokens": fields["total_tokens"],
                    "finish_reason": fields["finish_reason"],
                    "quality_score": score,
                    "response_text": fields["response_text"],
                    "raw_body": result["body"],
                }
                rows.append(row)

                status_icon = "✓" if result["error"] is None else "✗"
                print(
                    f"{status_icon}  {result['latency_ms']}ms  "
                    f"status={result['http_status']}  "
                    f"tokens={fields['total_tokens']}  "
                    f"quality={score}"
                )

    return rows


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

_CSV_COLUMNS = [
    "deployment",
    "prompt_id",
    "category",
    "run_id",
    "timestamp_utc",
    "latency_ms",
    "http_status",
    "error",
    "model_reported",
    "router_metadata",
    "input_tokens",
    "output_tokens",
    "total_tokens",
    "finish_reason",
    "quality_score",
    "response_text",
]


def write_csv(rows: list[dict], path: Path) -> None:
    """Write result rows to a CSV file (response_text truncated)."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            csv_row = dict(row)
            text = csv_row.get("response_text") or ""
            csv_row["response_text"] = text[:_CSV_RESPONSE_TRUNCATE]
            writer.writerow(csv_row)


def write_raw_json(rows: list[dict], path: Path) -> None:
    """Write full raw response bodies to a JSON file for debugging."""
    raw = []
    for row in rows:
        raw.append({
            "prompt_id": row["prompt_id"],
            "run_id": row["run_id"],
            "deployment": row["deployment"],
            "raw_body": row.get("raw_body"),
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw, f, indent=2, default=str)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="router_test",
        description="Test Azure AI Foundry Model Router latency, cost, and quality.",
    )
    parser.add_argument(
        "--prompts",
        default="src/prompts.json",
        help="Path to prompts JSON file (default: src/prompts.json)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=None,
        help="Number of runs per prompt (overrides RUNS_PER_PROMPT env var)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Output directory (overrides OUTPUT_DIR env var)",
    )
    parser.add_argument(
        "--raw-json",
        action="store_true",
        default=False,
        help="Also save raw JSON responses for debugging",
    )
    parser.add_argument(
        "--direct-deployment",
        default=None,
        help="Run the same prompts against a direct (non-router) deployment for comparison",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Entry point for the CLI."""
    args = parse_args(argv)
    cfg = _load_config()

    # Override config with CLI args
    if args.runs is not None:
        cfg["runs"] = args.runs
    if args.out is not None:
        cfg["output_dir"] = args.out

    # Validate required config
    if not cfg["endpoint"]:
        print("ERROR: AZURE_OPENAI_ENDPOINT (or FOUNDRY_ENDPOINT) not set.", file=sys.stderr)
        sys.exit(1)
    if not cfg["api_key"]:
        print("ERROR: AZURE_OPENAI_API_KEY (or FOUNDRY_API_KEY) not set.", file=sys.stderr)
        sys.exit(1)
    if not cfg["deployment"]:
        print("ERROR: DEPLOYMENT_NAME not set.", file=sys.stderr)
        sys.exit(1)

    # Load prompts
    prompts = load_prompts(args.prompts)
    print(f"Loaded {len(prompts)} prompts from {args.prompts}")

    # Prepare output directory
    out_dir = Path(cfg["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build URL and run router tests
    router_url = build_chat_url(cfg["endpoint"], cfg["deployment"], cfg["api_version"])
    print(f"\n--- Router deployment: {cfg['deployment']} ---")
    print(f"    URL: {router_url}")
    print(f"    Runs per prompt: {cfg['runs']}\n")

    all_rows = run_tests(
        prompts,
        url=router_url,
        api_key=cfg["api_key"],
        runs=cfg["runs"],
        timeout=cfg["timeout"],
        deployment_label=cfg["deployment"],
    )

    # Optional direct deployment comparison
    if args.direct_deployment:
        direct_url = build_chat_url(
            cfg["endpoint"], args.direct_deployment, cfg["api_version"]
        )
        print(f"\n--- Direct deployment: {args.direct_deployment} ---")
        print(f"    URL: {direct_url}")
        print(f"    Runs per prompt: {cfg['runs']}\n")

        direct_rows = run_tests(
            prompts,
            url=direct_url,
            api_key=cfg["api_key"],
            runs=cfg["runs"],
            timeout=cfg["timeout"],
            deployment_label=args.direct_deployment,
        )
        all_rows.extend(direct_rows)

    # Write outputs
    csv_path = out_dir / "results.csv"
    write_csv(all_rows, csv_path)
    print(f"\nCSV saved to {csv_path}")

    if args.raw_json:
        json_path = out_dir / "raw_responses.json"
        write_raw_json(all_rows, json_path)
        print(f"Raw JSON saved to {json_path}")

    # Summary
    summary = compute_summary(all_rows)
    print(format_summary_table(summary))


if __name__ == "__main__":
    main()
