import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "radar.db"

def connect(path: str | Path = DB_PATH):
    db = sqlite3.connect(str(path))
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA journal_mode=WAL")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS repos (
        full_name TEXT PRIMARY KEY, description TEXT, url TEXT, language TEXT,
        topics TEXT NOT NULL DEFAULT '[]', stars INTEGER NOT NULL,
        license TEXT, created_at TEXT, updated_at TEXT,
        metrics TEXT NOT NULL, sampled_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS sync_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL,
        completed_at TEXT, discovered INTEGER DEFAULT 0, refreshed INTEGER DEFAULT 0,
        failures INTEGER DEFAULT 0, status TEXT NOT NULL
    );
    """)
    db.commit()
    return db

def upsert(db, item: dict, values: dict, sampled_at: str):
    db.execute("""INSERT INTO repos(full_name,description,url,language,topics,stars,license,created_at,updated_at,metrics,sampled_at)
     VALUES (?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(full_name) DO UPDATE SET
     description=excluded.description,url=excluded.url,language=excluded.language,
     topics=excluded.topics,stars=excluded.stars,license=excluded.license,
     created_at=excluded.created_at,updated_at=excluded.updated_at,
     metrics=excluded.metrics,sampled_at=excluded.sampled_at""", (
        item["full_name"], item.get("description"), item.get("html_url"), item.get("language"),
        json.dumps(item.get("topics", [])), int(item.get("stargazers_count", 0)),
        (item.get("license") or {}).get("spdx_id"), item.get("created_at"), item.get("updated_at"),
        json.dumps(values), sampled_at,
    ))

def ranking(db, window="30d", language="", limit=20):
    if window not in ("7d", "30d", "90d", "6m", "1y"):
        raise ValueError("Unsupported time window")
    if limit < 1 or limit > 100:
        raise ValueError("limit out of bounds")
    rows = db.execute("SELECT * FROM repos").fetchall()
    repos = []
    for row in rows:
        item = dict(row)
        item["metrics"] = json.loads(item["metrics"])
        item["topics"] = json.loads(item["topics"])
        if language and (item["language"] or "").lower() != language.lower():
            continue
        item["growth"] = item["metrics"][window]["added"]
        item["growth_rate"] = item["metrics"][window]["rate"]
        repos.append(item)
    repos.sort(key=lambda item: (-item["growth"], -item["stars"], item["full_name"]))
    return repos[:limit]
