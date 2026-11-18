# CampusFlow

**A calmer campus planner that adapts to your energy.** Pick Low key, Steady, or Deep focus to change your focus forecast and study suggestion. CampusFlow includes the core private student workspace tools, with a focus timer and study streak as extras.

## Included

- Student registration, sign in, sign out, and private per-account records
- Overview dashboard with assignments, exams, attendance, expenses, focus forecast, and upcoming deadlines
- Weekly timetable
- Attendance tracker with a 75% planning calculation
- Assignment and practical task tracker with completion status
- Exam planner with date, time, venue, and preparation status
- Quick notes with pinning
- Expense tracker with categories and monthly totals
- Calendar for assignments, exams, and events
- Add, edit, and delete records
- Focus timer, completed session count, and streaks
- Responsive desktop and mobile interface
- SQLite database is created automatically

## Quick start on macOS

Double-click `run.command` and leave the Terminal window open while using CampusFlow. The first run creates a virtual environment and installs the required packages. Then open <http://127.0.0.1:8000> in your browser.

If macOS blocks the launcher, open Terminal, navigate to this folder, then run:

```bash
chmod +x run.command
./run.command
```

## Run on macOS or Linux manually

```bash
cd CampusFlow
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000> and create an account. Keep the terminal running while you use the app. Opening `static/index.html` directly will not work because registration and records require the backend server.

## Quick start on Windows

Double-click `run.bat`. The first run creates a virtual environment and installs the required packages. Then open <http://127.0.0.1:8000> in your browser. Keep the command window open while using CampusFlow.

## Run on Windows manually

```powershell
cd CampusFlow
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open <http://127.0.0.1:8000> and create an account.

## Data and deployment

Student records are scoped to the authenticated account on the backend. Passwords use salted PBKDF2-HMAC-SHA256 hashes. Session tokens are held in server memory, so users sign in again after a server restart. This is a local/demo starter, not a hardened public service; use HTTPS, persistent/revocable sessions, CSRF and rate limiting, password reset, backups, and a managed database before public deployment. Each browser stores focus vibe and timer streak preferences locally; academic records are stored in `campusflow.db`.
