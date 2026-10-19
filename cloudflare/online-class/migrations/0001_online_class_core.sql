-- Cloudflare D1 schema for the isolated Frahoosh online-class migration.
-- This is a NEW staging schema. It does not copy production data or alter Supabase.
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS app_users (
  id TEXT PRIMARY KEY,
  username TEXT NOT NULL UNIQUE COLLATE NOCASE,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  role TEXT NOT NULL CHECK (role IN ('manager','academic_deputy','teacher','student')),
  password_hash TEXT NOT NULL,
  password_salt TEXT NOT NULL,
  active INTEGER NOT NULL DEFAULT 1 CHECK (active IN (0,1)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS auth_sessions (
  token_hash TEXT PRIMARY KEY,
  user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  expires_at TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_user ON auth_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_auth_sessions_expiry ON auth_sessions(expires_at);

CREATE TABLE IF NOT EXISTS online_classes (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  subject TEXT,
  grade TEXT,
  class_name TEXT,
  teacher_user_id TEXT REFERENCES app_users(id) ON DELETE SET NULL,
  status TEXT NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled','active','ended')),
  duration_minutes INTEGER NOT NULL DEFAULT 50 CHECK (duration_minutes BETWEEN 1 AND 240),
  created_by TEXT NOT NULL REFERENCES app_users(id),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  started_at TEXT,
  ended_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_online_classes_teacher ON online_classes(teacher_user_id);
CREATE INDEX IF NOT EXISTS idx_online_classes_status ON online_classes(status);

CREATE TABLE IF NOT EXISTS class_members (
  class_id TEXT NOT NULL REFERENCES online_classes(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  member_role TEXT NOT NULL CHECK (member_role IN ('teacher','student')),
  can_draw INTEGER NOT NULL DEFAULT 0 CHECK (can_draw IN (0,1)),
  can_erase INTEGER NOT NULL DEFAULT 0 CHECK (can_erase IN (0,1)),
  can_audio INTEGER NOT NULL DEFAULT 0 CHECK (can_audio IN (0,1)),
  can_video INTEGER NOT NULL DEFAULT 0 CHECK (can_video IN (0,1)),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  PRIMARY KEY (class_id, user_id)
);

CREATE TABLE IF NOT EXISTS class_signals (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  class_id TEXT NOT NULL REFERENCES online_classes(id) ON DELETE CASCADE,
  user_id TEXT NOT NULL REFERENCES app_users(id) ON DELETE CASCADE,
  kind TEXT NOT NULL CHECK (kind IN ('presence','leave','board','permissions','audio','video','chat')),
  payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_class_signals_poll ON class_signals(class_id, id);

CREATE TABLE IF NOT EXISTS class_files (
  id TEXT PRIMARY KEY,
  class_id TEXT NOT NULL REFERENCES online_classes(id) ON DELETE CASCADE,
  object_key TEXT NOT NULL UNIQUE,
  original_name TEXT NOT NULL,
  content_type TEXT NOT NULL,
  size_bytes INTEGER NOT NULL CHECK (size_bytes BETWEEN 1 AND 20971520),
  uploaded_by TEXT NOT NULL REFERENCES app_users(id),
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
