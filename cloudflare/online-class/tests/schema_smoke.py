#!/usr/bin/env python3
"""Smoke-test the isolated Cloudflare D1 schema using Python's SQLite engine."""
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
SQL = ROOT / "migrations" / "0001_online_class_core.sql"

db = sqlite3.connect(":memory:")
db.execute("PRAGMA foreign_keys = ON")
db.executescript(SQL.read_text(encoding="utf-8"))

expected = {
    "app_users", "auth_sessions", "online_classes",
    "class_members", "class_signals", "class_files",
}
actual = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
missing = expected - actual
assert not missing, f"Missing tables: {sorted(missing)}"

# Manager, teacher and student roles are restricted to the explicit role set.
db.execute(
    "INSERT INTO app_users(id,username,first_name,last_name,role,password_hash,password_salt) VALUES(?,?,?,?,?,?,?)",
    ("manager-1", "manager", "School", "Manager", "manager", "hash", "salt"),
)
try:
    db.execute(
        "INSERT INTO app_users(id,username,first_name,last_name,role,password_hash,password_salt) VALUES(?,?,?,?,?,?,?)",
        ("bad-1", "bad", "Bad", "Role", "guest", "hash", "salt"),
    )
    raise AssertionError("Unexpected role was accepted")
except sqlite3.IntegrityError:
    pass

db.execute(
    "INSERT INTO online_classes(id,title,created_by) VALUES(?,?,?)",
    ("class-1", "Test classroom", "manager-1"),
)
try:
    db.execute(
        "INSERT INTO class_members(class_id,user_id,member_role) VALUES(?,?,?)",
        ("missing-class", "manager-1", "teacher"),
    )
    raise AssertionError("Foreign-key violation was accepted")
except sqlite3.IntegrityError:
    pass

print("Cloudflare D1 schema smoke test passed.")
