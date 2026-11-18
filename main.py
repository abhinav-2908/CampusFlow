"""CampusFlow: a private, vibe-aware student planner."""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import sqlite3
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

ROOT = Path(__file__).parent
DB = ROOT / "campusflow.db"
app = FastAPI(title="CampusFlow API", version="1.0.0")
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
SESSIONS: dict[str, int] = {}
KINDS = {"timetable", "attendance", "assignment", "exam", "note", "expense", "event"}


def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c


with db() as c:
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT NOT NULL,
      email TEXT NOT NULL UNIQUE, salt TEXT NOT NULL, password_hash TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS records(id INTEGER PRIMARY KEY, user_id INTEGER NOT NULL,
      kind TEXT NOT NULL, title TEXT NOT NULL, data TEXT NOT NULL DEFAULT '{}',
      created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
    CREATE INDEX IF NOT EXISTS idx_records_user_kind ON records(user_id, kind);
    """)


def password_hash(password: str, salt: Optional[str] = None):
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 240000).hex()
    return salt, digest


def new_session(uid: int):
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = uid
    return token


def current_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Please sign in to continue.")
    uid = SESSIONS.get(authorization[7:])
    if not uid:
        raise HTTPException(401, "Your session expired. Please sign in again.")
    with db() as c:
        row = c.execute("SELECT id,name,email FROM users WHERE id=?", (uid,)).fetchone()
    if not row:
        raise HTTPException(401, "Account not found.")
    return dict(row)


class Register(BaseModel):
    name: str = Field(min_length=2, max_length=60)
    email: str = Field(max_length=254)
    password: str = Field(min_length=8, max_length=128)


class Login(BaseModel):
    email: str
    password: str


class Record(BaseModel):
    kind: str
    title: str = Field(min_length=1, max_length=140)
    data: dict = Field(default_factory=dict)


@app.get("/")
def home():
    return FileResponse(ROOT / "static" / "index.html")


@app.post("/api/register")
def register(body: Register):
    name, email = body.name.strip(), body.email.strip().lower()
    if "@" not in email or "." not in email.rsplit("@", 1)[-1]:
        raise HTTPException(400, "Enter a valid email address.")
    salt, digest = password_hash(body.password)
    try:
        with db() as c:
            cur = c.execute("INSERT INTO users(name,email,salt,password_hash) VALUES(?,?,?,?)", (name, email, salt, digest))
            uid = cur.lastrowid
    except sqlite3.IntegrityError:
        raise HTTPException(409, "An account with this email already exists.")
    return {"token": new_session(uid), "user": {"id": uid, "name": name, "email": email}}


@app.post("/api/login")
def login(body: Login):
    with db() as c:
        row = c.execute("SELECT * FROM users WHERE email=?", (body.email.strip().lower(),)).fetchone()
    if not row:
        raise HTTPException(401, "Incorrect email or password.")
    _, digest = password_hash(body.password, row["salt"])
    if not hmac.compare_digest(digest, row["password_hash"]):
        raise HTTPException(401, "Incorrect email or password.")
    return {"token": new_session(row["id"]), "user": {"id": row["id"], "name": row["name"], "email": row["email"]}}


@app.post("/api/logout")
def logout(authorization: Optional[str] = Header(default=None)):
    if authorization and authorization.startswith("Bearer "):
        SESSIONS.pop(authorization[7:], None)
    return {"ok": True}


@app.get("/api/me")
def me(user=Depends(current_user)):
    return user


@app.get("/api/records")
def list_records(kind: Optional[str] = None, user=Depends(current_user)):
    if kind and kind not in KINDS:
        raise HTTPException(400, "Unknown category.")
    with db() as c:
        query = "SELECT id,kind,title,data,created_at FROM records WHERE user_id=?"
        args = [user["id"]]
        if kind:
            query += " AND kind=?"
            args.append(kind)
        rows = c.execute(query + " ORDER BY id DESC", args).fetchall()
    return [{"id": r["id"], "kind": r["kind"], "title": r["title"], "data": json.loads(r["data"]), "created_at": r["created_at"]} for r in rows]


@app.post("/api/records")
def create_record(body: Record, user=Depends(current_user)):
    if body.kind not in KINDS:
        raise HTTPException(400, "Unknown category.")
    title = body.title.strip()
    with db() as c:
        cur = c.execute("INSERT INTO records(user_id,kind,title,data) VALUES(?,?,?,?)", (user["id"], body.kind, title, json.dumps(body.data)))
    return {"id": cur.lastrowid, "kind": body.kind, "title": title, "data": body.data}


@app.put("/api/records/{record_id}")
def update_record(record_id: int, body: Record, user=Depends(current_user)):
    if body.kind not in KINDS:
        raise HTTPException(400, "Unknown category.")
    with db() as c:
        cur = c.execute("UPDATE records SET kind=?,title=?,data=? WHERE id=? AND user_id=?", (body.kind, body.title.strip(), json.dumps(body.data), record_id, user["id"]))
    if not cur.rowcount:
        raise HTTPException(404, "Record not found.")
    return {"ok": True}


@app.delete("/api/records/{record_id}")
def delete_record(record_id: int, user=Depends(current_user)):
    with db() as c:
        cur = c.execute("DELETE FROM records WHERE id=? AND user_id=?", (record_id, user["id"]))
    if not cur.rowcount:
        raise HTTPException(404, "Record not found.")
    return {"ok": True}
