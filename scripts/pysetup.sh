#!/usr/bin/env bash
# Sets up the Python environment for the AI Security full-day labs.
PYTHON_ENV=${1:-py_env}
python3 -m venv ./$PYTHON_ENV \
    && export PATH=./$PYTHON_ENV/bin:$PATH \
    && grep -qxF "source $(pwd)/$PYTHON_ENV/bin/activate" ~/.bashrc \
    || echo "source $(pwd)/$PYTHON_ENV/bin/activate" >> ~/.bashrc
source ./$PYTHON_ENV/bin/activate
if [ -f "./requirements.txt" ]; then
    pip3 install -r "./requirements.txt"
fi

# Pre-download Chroma's embedding model (~80MB) so Lab 2's first run is fast.
echo "Warming up the Chroma embedding model (one-time download)..."
python3 - <<'PY' || echo "  (embedder will download on first use of Lab 2)"
import chromadb
c = chromadb.Client()
col = c.get_or_create_collection("warmup_kb")
col.add(documents=["warm up the embedder"], ids=["1"])
print("  embedding model ready.")
PY

echo "Environment ready (stdlib + PyYAML + Chroma)."
