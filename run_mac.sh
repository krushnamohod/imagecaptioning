#!/usr/bin/env bash
# Set up and run the Image Captioning project on macOS (also works on Linux).
#   Backend  (FastAPI + BLIP):  http://127.0.0.1:8000  (docs at /docs)
#   Frontend (Streamlit):       http://localhost:8501
#
# Usage:  ./run_mac.sh            # install deps if needed, then start both
#         ./run_mac.sh --reinstall  # force reinstall of Python deps
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV="$ROOT/.venv-unix"
BACKEND_PORT="${BACKEND_PORT:-8000}"
STREAMLIT_PORT="${STREAMLIT_PORT:-8501}"

# Pick a Python version that PyTorch supports (3.10 - 3.12 is safest).
find_python() {
  PYTHON=""
  for candidate in python3.12 python3.11 python3.10; do
    if command -v "$candidate" >/dev/null 2>&1; then
      PYTHON="$candidate"
      return 0
    fi
  done
  return 1
}

# Install Python 3.12 (and Homebrew, if needed) when no suitable Python exists.
install_python() {
  if [[ "$(uname)" == "Darwin" ]]; then
    if ! command -v brew >/dev/null 2>&1; then
      for prefix in /opt/homebrew /usr/local; do
        [[ -x "$prefix/bin/brew" ]] && eval "$("$prefix/bin/brew" shellenv)"
      done
    fi
    if ! command -v brew >/dev/null 2>&1; then
      echo "Homebrew not found. Installing Homebrew (you may be asked for your password) ..."
      /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
      for prefix in /opt/homebrew /usr/local; do
        [[ -x "$prefix/bin/brew" ]] && eval "$("$prefix/bin/brew" shellenv)"
      done
    fi
    echo "Installing Python 3.12 with Homebrew ..."
    brew install python@3.12
    export PATH="$(brew --prefix python@3.12)/libexec/bin:$(brew --prefix)/bin:$PATH"
  elif command -v dnf >/dev/null 2>&1; then
    sudo dnf install -y python3.12 python3.12-devel
  elif command -v apt-get >/dev/null 2>&1; then
    sudo apt-get update && sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
  else
    echo "Could not install Python automatically. Please install Python 3.12 and re-run." >&2
    exit 1
  fi
}

if ! find_python; then
  echo "Python 3.10-3.12 not found."
  install_python
  if ! find_python; then
    echo "Python installation failed; install Python 3.12 manually and re-run." >&2
    exit 1
  fi
fi
echo "Using $PYTHON ($("$PYTHON" --version))"

if [[ ! -f "$ROOT/models/blip-flickr8k/model.safetensors" ]]; then
  echo "Missing fine-tuned model at models/blip-flickr8k (model.safetensors)." >&2
  exit 1
fi

if [[ ! -f "$ROOT/backend/.env" ]]; then
  cp "$ROOT/backend/.env.example" "$ROOT/backend/.env"
  echo "Created backend/.env from .env.example - add your GROQ_API_KEY to it."
fi
if ! grep -qE '^GROQ_API_KEY=.+' "$ROOT/backend/.env"; then
  echo "Warning: GROQ_API_KEY is not set in backend/.env; Groq captions will fail." >&2
fi

# Create the virtual environment and install dependencies on first run.
if [[ ! -x "$VENV/bin/python" ]]; then
  echo "Creating virtual environment with $PYTHON ..."
  "$PYTHON" -m venv "$VENV"
  rm -f "$VENV/.installed"
fi
if [[ ! -f "$VENV/.installed" || "${1:-}" == "--reinstall" ]]; then
  echo "Installing Python dependencies (first run downloads PyTorch, this can take a while) ..."
  "$VENV/bin/python" -m pip install --upgrade pip
  "$VENV/bin/python" -m pip install -r backend/requirements.txt -r streamlit_app/requirements.txt
  touch "$VENV/.installed"
fi

PIDS=()
cleanup() {
  echo
  echo "Stopping services ..."
  for pid in "${PIDS[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

echo "Starting FastAPI backend on port $BACKEND_PORT ..."
"$VENV/bin/python" -m uvicorn app.main:app --app-dir backend \
  --host 127.0.0.1 --port "$BACKEND_PORT" &
PIDS+=($!)

# Wait for the backend to finish loading the BLIP model.
echo "Waiting for backend to load the BLIP model ..."
for _ in $(seq 1 180); do
  if curl -fs "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1; then
    echo "Backend is up."
    break
  fi
  if ! kill -0 "${PIDS[0]}" 2>/dev/null; then
    echo "Backend exited during startup; see the log above." >&2
    exit 1
  fi
  sleep 1
done

echo "Starting Streamlit frontend on port $STREAMLIT_PORT ..."
BACKEND_API_URL="http://127.0.0.1:$BACKEND_PORT" \
  "$VENV/bin/python" -m streamlit run streamlit_app/app.py \
  --server.port "$STREAMLIT_PORT" --server.headless true --browser.gatherUsageStats false &
PIDS+=($!)

sleep 2
echo
echo "  Backend API:  http://127.0.0.1:$BACKEND_PORT/docs"
echo "  Streamlit UI: http://localhost:$STREAMLIT_PORT"
echo "  Press Ctrl+C to stop."
if [[ "$(uname)" == "Darwin" ]]; then
  open "http://localhost:$STREAMLIT_PORT" || true
fi

wait
