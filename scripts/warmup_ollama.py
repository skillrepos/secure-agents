#!/usr/bin/env python3
"""Warm up an Ollama model with a tiny one-shot generation request.

Usage:
  python3 scripts/warmup_ollama.py
    python3 scripts/warmup_ollama.py --model llama3.2:3b --retries 8
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request


def _post_json(url: str, payload: dict, timeout: int) -> dict:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _check_server(base_url: str, timeout: int) -> None:
    req = urllib.request.Request(f"{base_url}/api/tags", method="GET")
    with urllib.request.urlopen(req, timeout=timeout):
        return


def warmup(base_url: str, model: str, timeout: int, retries: int, pause: float) -> int:
    _check_server(base_url, timeout)

    payload = {
        "model": model,
        "prompt": "Reply with exactly one word: ready",
        "stream": False,
        "keep_alive": "30m",
        "options": {"temperature": 0, "num_predict": 8},
    }

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        t0 = time.time()
        try:
            data = _post_json(f"{base_url}/api/generate", payload, timeout)
            elapsed = time.time() - t0
            text = (data.get("response") or "").strip().replace("\n", " ")
            preview = text[:80] if text else "<empty>"
            print(f"[warmup] ok model={model} latency={elapsed:.2f}s response={preview}")
            return 0
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            last_error = exc
            print(
                f"[warmup] attempt {attempt}/{retries} failed: {exc}",
                file=sys.stderr,
            )
            if attempt < retries:
                time.sleep(pause)

    print(f"[warmup] failed after {retries} attempts: {last_error}", file=sys.stderr)
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Warm up an Ollama model")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
        help="Ollama server base URL",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("OLLAMA_MODEL", "llama3.2:3b"),
        help="Model to warm up",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=int(os.environ.get("OLLAMA_TIMEOUT", "120")),
        help="HTTP timeout seconds",
    )
    parser.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Number of retries for warmup request",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=2.0,
        help="Seconds to wait between retries",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    return warmup(args.base_url.rstrip("/"), args.model, args.timeout, args.retries, args.pause)


if __name__ == "__main__":
    raise SystemExit(main())
