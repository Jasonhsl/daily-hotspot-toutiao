"""Transactional publication reservations; browser evidence remains required."""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import sqlite3
import unicodedata
from datetime import date, datetime, timezone
from pathlib import Path

TRANSITIONS = {
    "reserved": {"preview_verified"},
    "preview_verified": {"submitting"},
    "submitting": {"submitted_review", "published", "unknown", "rejected"},
    "unknown": {"submitted_review", "published", "rejected"},
    "submitted_review": {"published", "rejected"},
    "published": set(), "rejected": set()
}

def fingerprint(article):
    parts = [article["lead"]]
    for section in article["sections"]:
        parts.extend([section["heading"], *section["paragraphs"]])
    body = re.sub(r"\s+", "", unicodedata.normalize("NFKC", "\n".join(parts)))
    if not body:
        raise ValueError("Empty body.")
    return hashlib.sha256(body.encode("utf-8")).hexdigest()

def connect(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(path, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY, account TEXT NOT NULL, run_date TEXT NOT NULL,
        edition TEXT NOT NULL DEFAULT 'daily',
        fingerprint TEXT NOT NULL, title TEXT NOT NULL, status TEXT NOT NULL,
        platform_id TEXT, evidence TEXT NOT NULL, updated_at TEXT NOT NULL,
        UNIQUE(account, run_date, edition), UNIQUE(account, fingerprint))""")
    if "edition" not in {row[1] for row in db.execute("PRAGMA table_info(posts)")}:
        # Preserve all IDs and evidence while allowing explicitly requested extras.
        with db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("""CREATE TABLE posts_with_editions (
                id INTEGER PRIMARY KEY, account TEXT NOT NULL, run_date TEXT NOT NULL,
                edition TEXT NOT NULL DEFAULT 'daily', fingerprint TEXT NOT NULL,
                title TEXT NOT NULL, status TEXT NOT NULL, platform_id TEXT,
                evidence TEXT NOT NULL, updated_at TEXT NOT NULL,
                UNIQUE(account, run_date, edition), UNIQUE(account, fingerprint))""")
            db.execute("""INSERT INTO posts_with_editions
                (id,account,run_date,fingerprint,title,status,platform_id,evidence,updated_at)
                SELECT id,account,run_date,fingerprint,title,status,platform_id,evidence,updated_at FROM posts""")
            db.execute("DROP TABLE posts")
            db.execute("ALTER TABLE posts_with_editions RENAME TO posts")
    db.execute("""CREATE TABLE IF NOT EXISTS events (
        post_id INTEGER, status TEXT, evidence TEXT, at TEXT)""")
    db.commit()
    return db

def now():
    return datetime.now(timezone.utc).isoformat()

def reserve(db, account, article, edition="daily", authorization=""):
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,63}", edition):
        raise ValueError("Invalid edition key.")
    if edition != "daily" and not authorization.strip():
        raise ValueError("Extra editions require an explicit user request as evidence.")
    day = date.fromisoformat(article["run_date"]).isoformat()
    digest = fingerprint(article)
    with db:
        db.execute("BEGIN IMMEDIATE")
        rows = db.execute("SELECT * FROM posts WHERE account=? AND ((run_date=? AND edition=?) OR fingerprint=?)",
                          (account, day, edition, digest)).fetchall()
        if rows:
            return {"created": False, "records": [dict(r) for r in rows]}
        at = now()
        evidence = "Reserved final article" + ("; explicit extra request: " + authorization if edition != "daily" else "")
        cur = db.execute("""INSERT INTO posts
            (account,run_date,edition,fingerprint,title,status,evidence,updated_at)
            VALUES (?,?,?,?,?,?,?,?)""",
            (account, day, edition, digest, article["title"], "reserved", evidence, at))
        db.execute("INSERT INTO events VALUES (?,?,?,?)",
                   (cur.lastrowid, "reserved", evidence, at))
        return {"created": True, "id": cur.lastrowid, "fingerprint": digest}

def mark(db, account, ident, status, evidence, platform_id=None, confirmed=False):
    if not evidence.strip():
        raise ValueError("Observed evidence is required.")
    with db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM posts WHERE id=? AND account=?", (ident, account)).fetchone()
        if row is None:
            raise ValueError("Unknown account/post.")
        recovery = (row["status"] in {"submitting", "unknown"}
                    and status == "preview_verified" and confirmed)
        if status not in TRANSITIONS[row["status"]] and not recovery:
            raise ValueError("Blocked transition: " + row["status"] + " -> " + status)
        if row["platform_id"] and platform_id and platform_id != row["platform_id"]:
            raise ValueError("Platform ID changed; reconcile the correct record.")
        pid = platform_id or row["platform_id"]
        if status in {"preview_verified", "submitting", "submitted_review", "published"} and not pid:
            raise ValueError("A visible platform draft/article ID is required.")
        at = now()
        db.execute("UPDATE posts SET status=?,platform_id=?,evidence=?,updated_at=? WHERE id=?",
                   (status, pid, evidence, at, ident))
        db.execute("INSERT INTO events VALUES (?,?,?,?)", (ident, status, evidence, at))
        return dict(db.execute("SELECT * FROM posts WHERE id=?", (ident,)).fetchone())

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", required=True)
    parser.add_argument("--account", required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    reserve_cmd = commands.add_parser("reserve")
    reserve_cmd.add_argument("--article", required=True, type=Path)
    reserve_cmd.add_argument("--edition", default="daily")
    reserve_cmd.add_argument("--authorization", default="")
    commands.add_parser("list")
    mark_cmd = commands.add_parser("mark")
    mark_cmd.add_argument("--id", required=True, type=int)
    mark_cmd.add_argument("--status", required=True, choices=TRANSITIONS)
    mark_cmd.add_argument("--evidence", required=True)
    mark_cmd.add_argument("--platform-id")
    mark_cmd.add_argument("--confirmed-not-submitted", action="store_true")
    args = parser.parse_args()
    db = connect(args.db)
    try:
        if args.command == "reserve":
            result = reserve(db, args.account, json.loads(args.article.read_text(encoding="utf-8-sig")),
                             args.edition, args.authorization)
        elif args.command == "mark":
            result = mark(db, args.account, args.id, args.status, args.evidence,
                          args.platform_id, args.confirmed_not_submitted)
        else:
            result = [dict(r) for r in db.execute(
                "SELECT * FROM posts WHERE account=? ORDER BY id DESC", (args.account,))]
        print(json.dumps(result, ensure_ascii=False))
    finally:
        db.close()

if __name__ == "__main__":
    main()
