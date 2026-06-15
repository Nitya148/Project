"""SQLite data access layer for RePlate."""
from __future__ import annotations

import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

DB_PATH = os.environ.get("REPLATE_DB_PATH", str(Path(__file__).parent.parent / "replate.db"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_conn():
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name TEXT,
    role TEXT NOT NULL,           -- donor | recipient | admin
    org_name TEXT,
    org_type TEXT,
    phone TEXT,
    address TEXT,
    lat REAL,
    lng REAL,
    verified INTEGER DEFAULT 0,
    points INTEGER DEFAULT 0,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS listings (
    id TEXT PRIMARY KEY,
    donor_id TEXT NOT NULL,
    donor_name TEXT,
    donor_org_type TEXT,
    name TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    quantity REAL NOT NULL,
    remaining_quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    storage_condition TEXT,
    allergens TEXT,              -- comma-separated
    dietary TEXT,                -- comma-separated
    photo_url TEXT,
    pickup_address TEXT,
    lat REAL,
    lng REAL,
    pickup_start TEXT,
    pickup_end TEXT,
    expiry_time TEXT,
    status TEXT DEFAULT 'active', -- active | claimed | completed | expired | cancelled
    pickup_pin TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (donor_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS requests (
    id TEXT PRIMARY KEY,
    listing_id TEXT NOT NULL,
    listing_name TEXT,
    donor_id TEXT NOT NULL,
    donor_name TEXT,
    recipient_id TEXT NOT NULL,
    recipient_name TEXT,
    requested_quantity REAL NOT NULL,
    unit TEXT,
    note TEXT,
    status TEXT DEFAULT 'pending', -- pending | approved | rejected | completed | cancelled
    created_at TEXT NOT NULL,
    approved_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (listing_id) REFERENCES listings(id),
    FOREIGN KEY (donor_id) REFERENCES users(id),
    FOREIGN KEY (recipient_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS vouchers (
    id TEXT PRIMARY KEY,
    partner TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    points_cost INTEGER NOT NULL,
    image_url TEXT
);

CREATE TABLE IF NOT EXISTS redemptions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    voucher_id TEXT NOT NULL,
    voucher_title TEXT,
    partner TEXT,
    points_cost INTEGER NOT NULL,
    code TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS point_transactions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    type TEXT NOT NULL,           -- earned | redeemed
    reason TEXT,
    request_id TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS impact_events (
    id TEXT PRIMARY KEY,
    donor_id TEXT NOT NULL,
    recipient_id TEXT NOT NULL,
    listing_id TEXT,
    request_id TEXT,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    meals REAL NOT NULL,
    co2_kg REAL NOT NULL,
    created_at TEXT NOT NULL
);
"""


def init_db() -> None:
    """Create tables. Idempotent."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)


# -------- Helpers ----------------------------------------------------------

def fetch_all(query: str, params: Iterable[Any] = ()) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(query, list(params)).fetchall()
        return [dict(r) for r in rows]


def fetch_one(query: str, params: Iterable[Any] = ()) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(query, list(params)).fetchone()
        return dict(row) if row else None


def execute(query: str, params: Iterable[Any] = ()) -> None:
    with get_conn() as conn:
        conn.execute(query, list(params))


def execute_many(query: str, seq: Iterable[Iterable[Any]]) -> None:
    with get_conn() as conn:
        conn.executemany(query, seq)
