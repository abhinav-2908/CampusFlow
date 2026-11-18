@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python 3 is required. Install it from https://www.python.org/downloads/ and try again.
  pause
  exit /b 1
)
if not exist .venv\Scripts\python.exe py -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt
echo CampusFlow is starting. Leave this window open while using the app.
echo Open http://127.0.0.1:8000 in your browser.
python -m uvicorn main:app --host 127.0.0.1 --port 8000
pause
