#!/usr/bin/env bash
# Installs Ollama, ensures the server is running, and makes sure the selected
# model is present. This script is safe to run from both postCreateCommand and
# postAttachCommand.
set -e
MODEL="${OLLAMA_MODEL:-llama3.2:3b}"
SKIP_PULL=0
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ensure_zstd() {
    if command -v zstd >/dev/null 2>&1; then
        return
    fi

    echo "[ollama] installing zstd..."
    if command -v sudo >/dev/null 2>&1 && sudo -n true >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y zstd
    elif [[ "${EUID:-$(id -u)}" -eq 0 ]]; then
        apt-get update
        apt-get install -y zstd
    else
        echo "[ollama] error: zstd is required to install Ollama. Install it with sudo apt-get install -y zstd and retry."
        exit 1
    fi
}

if [[ "${1:-}" == "--skip-pull" ]]; then
    SKIP_PULL=1
fi

if ! command -v ollama >/dev/null 2>&1; then
    echo "[ollama] installing Ollama..."
    ensure_zstd
    curl -fsSL https://ollama.com/install.sh | sh
fi

# Start the server in the background if it isn't already running.
if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "[ollama] starting server..."
    nohup ollama serve >/tmp/ollama.log 2>&1 &
    sleep 3
fi

if [[ "$SKIP_PULL" -eq 1 ]]; then
    echo "[ollama] skipping model pull check (--skip-pull)"
else
    if ollama list 2>/dev/null | awk 'NR>1 {print $1}' | grep -Fx "$MODEL" >/dev/null 2>&1; then
        echo "[ollama] model already present: $MODEL"
    else
        echo "[ollama] pulling model $MODEL (one-time download)..."
        ollama pull "$MODEL"
    fi

    if command -v python3 >/dev/null 2>&1; then
        echo "[ollama] warming up model $MODEL..."
        if ! python3 "$SCRIPT_DIR/warmup_ollama.py" --model "$MODEL"; then
            echo "[ollama] warning: warmup failed; startup can continue."
        fi
    else
        echo "[ollama] warning: python3 not found; skipping warmup"
    fi
fi

echo "[ollama] ready. Server: http://localhost:11434 | Model: $MODEL"
