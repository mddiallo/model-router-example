# Model Router Example

A production-quality CLI tool that tests **Microsoft Azure AI Foundry "Model Router"** behavior — measuring latency, token usage, routing choice signals, and basic quality proxy across multiple prompts.

## Features

- **Reproducible benchmarking**: sends a list of test prompts to a Model Router deployment and captures per-request metrics.
- **Metrics captured**: end-to-end latency, token usage, HTTP status, finish reason, model reported, router metadata, and a keyword-based quality score.
- **Multiple output formats**: CSV (one row per request), console summary table (p50/p95 latency, avg tokens, error rate), and optional raw JSON dump.
- **Robust error handling**: exponential backoff with up to 3 retries on 429/5xx errors.
- **Direct deployment comparison**: optional `--direct-deployment` flag to run the same prompts against a non-router deployment for side-by-side analysis.

## Quick Start

### 1. Prerequisites

- Python 3.10+
- An Azure AI Foundry (or Azure OpenAI) resource with a Model Router deployment configured

### 2. Install

```bash
# Clone and install dependencies
git clone https://github.com/mddiallo/model-router-example.git
cd model-router-example
pip install -r requirements.txt
```

Or use the Makefile:

```bash
make install
```

### 3. Configure

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

Required environment variables:

| Variable | Description | Example |
|---|---|---|
| `AZURE_OPENAI_ENDPOINT` | Your Azure OpenAI / Foundry endpoint | `https://myresource.openai.azure.com/` |
| `AZURE_OPENAI_API_KEY` | API key for authentication | `abc123...` |
| `DEPLOYMENT_NAME` | The router deployment name | `my-router` |

Optional:

| Variable | Default | Description |
|---|---|---|
| `API_VERSION` | `2024-12-01-preview` | Azure API version |
| `MODE` | `balanced` | Router mode hint (`balanced`, `cost`, `quality`) |
| `RUNS_PER_PROMPT` | `3` | Number of times each prompt is sent |
| `TIMEOUT_S` | `60` | HTTP request timeout in seconds |
| `OUTPUT_DIR` | `./out` | Directory for output files |

### 4. Run

```bash
# Basic run
python -m src.router_test

# Custom prompts, runs, and output directory
python -m src.router_test --prompts src/prompts.json --runs 5 --out results/

# Include raw JSON responses for debugging
python -m src.router_test --raw-json

# Compare router vs. a direct model deployment
python -m src.router_test --direct-deployment gpt-4o --raw-json
```

Or use the Makefile:

```bash
make run
```

## Prompts File Format

The prompts file is a JSON array. Each item has:

```json
[
  {
    "id": "p01",
    "category": "summarization",
    "prompt": "Summarize the key benefits of cloud computing in three bullet points.",
    "expected_keywords": ["scalability", "cost", "flexibility"]
  }
]
```

- `id` (required): unique identifier for the prompt.
- `prompt` (required): the user message to send.
- `category` (optional): a label for grouping results.
- `expected_keywords` (optional): keywords to compute a quality score (fraction found in the response, case-insensitive).

## Sample Output

### Console

```
Loaded 5 prompts from src/prompts.json

--- Router deployment: my-router ---
    URL: https://myresource.openai.azure.com/openai/deployments/my-router/chat/completions?api-version=2024-12-01-preview
    Runs per prompt: 3

  [1/15] my-router | prompt=p01 run=1 ... ✓  523.41ms  status=200  tokens=95  quality=1.0
  [2/15] my-router | prompt=p01 run=2 ... ✓  412.78ms  status=200  tokens=102 quality=0.6667
  ...

CSV saved to out/results.csv

==================================================
  Model Router Test Summary
==================================================
  Total requests     : 15
  Errors             : 0
  Error rate         : 0.00%
  p50 latency (ms)   : 487.32
  p95 latency (ms)   : 1023.55
  Avg total tokens   : 98.4
  Avg quality score  : 0.7833
==================================================
```

### CSV Columns

| Column | Description |
|---|---|
| `deployment` | Deployment name used |
| `prompt_id` | Prompt identifier |
| `category` | Prompt category |
| `run_id` | Run number (1-based) |
| `timestamp_utc` | UTC timestamp of the request |
| `latency_ms` | End-to-end latency in milliseconds |
| `http_status` | HTTP status code |
| `error` | Error message (if any) |
| `model_reported` | Model name from the response (if returned) |
| `router_metadata` | Any extra/routing fields from the response (JSON) |
| `input_tokens` | Prompt tokens used |
| `output_tokens` | Completion tokens used |
| `total_tokens` | Total tokens used |
| `finish_reason` | Completion finish reason |
| `quality_score` | Fraction of expected keywords found |
| `response_text` | Response text (truncated in CSV) |

## Interpreting Results

### Routing Variability

- Look at the `model_reported` column across runs of the same prompt. If the router is distributing across models, you'll see different model names.
- The `router_metadata` column captures any additional routing information the API returns.

### Latency vs. Tokens

- Compare `latency_ms` against `total_tokens` to see if latency scales with output length or varies by routed model.
- Use `p50` and `p95` from the summary to understand typical vs. tail latency.

### Quality Score

- The quality score is a simple proxy: it checks what fraction of `expected_keywords` appear in the response.
- A score of 1.0 means all keywords were found; 0.0 means none were found.
- Use this to spot cases where routing to a smaller/cheaper model may reduce answer quality.

### Router vs. Direct Comparison

- Use `--direct-deployment <name>` to run the same prompts against a specific model.
- Compare latency, token usage, and quality scores between the router and direct deployments in the CSV.

## Running Tests

```bash
# Install test dependencies
pip install pytest

# Run tests
python -m pytest tests/ -v
```

Or:

```bash
make test
```

## Project Structure

```
.
├── .env.example          # Template for environment variables
├── Makefile              # Convenience targets
├── README.md             # This file
├── requirements.txt      # Python dependencies
├── src/
│   ├── __init__.py
│   ├── prompts.json      # Sample test prompts
│   ├── router_test.py    # Main CLI entry point
│   └── utils.py          # Helpers (URL building, retries, metrics)
├── tests/
│   ├── __init__.py
│   ├── test_router_test.py
│   └── test_utils.py
└── out/                  # Default output directory (git-ignored)
    ├── results.csv
    └── raw_responses.json
```

## License

MIT
