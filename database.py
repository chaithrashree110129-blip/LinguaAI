"""SQLite helpers for translation history and simple settings."""

import sqlite3
from datetime import datetime, timezone

import config


def _connect():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(config.DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db():
    with _connect() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS translations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_text TEXT NOT NULL,
                source_language TEXT NOT NULL,
                detected_language TEXT,
                target_language TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )


def save_translation(
    original_text,
    source_language,
    target_language,
    translated_text,
    detected_language=None,
):
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO translations (
                original_text,
                source_language,
                detected_language,
                target_language,
                translated_text,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                original_text,
                source_language,
                detected_language,
                target_language,
                translated_text,
                stamp,
            ),
        )


def list_translations():
    with _connect() as connection:
        rows = connection.execute(
            "SELECT * FROM translations ORDER BY id DESC"
        ).fetchall()
    return [dict(row) for row in rows]


def get_translation(item_id):
    with _connect() as connection:
        row = connection.execute(
            "SELECT * FROM translations WHERE id = ?", (item_id,)
        ).fetchone()
    return dict(row) if row else None


def delete_translation(item_id):
    with _connect() as connection:
        connection.execute("DELETE FROM translations WHERE id = ?", (item_id,))


def clear_translations():
    with _connect() as connection:
        connection.execute("DELETE FROM translations")


def get_setting(key, default=None):
    with _connect() as connection:
        row = connection.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
