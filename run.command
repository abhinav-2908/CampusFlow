#!/bin/zsh
set -e
cd "$(dirname "$0")"
if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it from https://www.python.org/downloads/ and try again."
  read -k 1 "?Press any key to close..."
  exit 1
fi
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi
source .venv/bin/activate
python -m pip install -r requirements.txt
echo "CampusFlow is starting. Leave this window open while using the app."
echo "Open http://127.0.0.1:8000 in your browser."
python -m uvicorn main:app --host 127.0.0.1 --port 8000
