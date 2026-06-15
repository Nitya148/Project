"""Auth helpers — bcrypt + Streamlit session_state."""
from __future__ import annotations

import bcrypt
import streamlit as st

from .db import fetch_one, execute
import uuid
from datetime import datetime, timezone


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), hashed.encode())
    except Exception:
        return False


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def login(email: str, password: str) -> tuple[bool, str]:
    email = email.lower().strip()
    user = fetch_one("SELECT * FROM users WHERE email = ?", [email])
    if not user or not verify_password(password, user["password_hash"]):
        return False, "Invalid email or password."
    st.session_state["user"] = _serialize(user)
    return True, "Welcome back."


def register(payload: dict) -> tuple[bool, str]:
    email = payload["email"].lower().strip()
    if fetch_one("SELECT id FROM users WHERE email = ?", [email]):
        return False, "Email already registered."
    user_id = str(uuid.uuid4())
    execute(
        """INSERT INTO users (id, email, password_hash, name, role, org_name, org_type,
                              phone, address, lat, lng, verified, points, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        [
            user_id,
            email,
            hash_password(payload["password"]),
            payload.get("name"),
            payload["role"],
            payload.get("org_name"),
            payload.get("org_type"),
            payload.get("phone"),
            payload.get("address"),
            payload.get("lat"),
            payload.get("lng"),
            1 if payload["role"] == "donor" else 0,
            0,
            now_iso(),
        ],
    )
    user = fetch_one("SELECT * FROM users WHERE id = ?", [user_id])
    st.session_state["user"] = _serialize(user)
    return True, "Account created."


def logout() -> None:
    st.session_state.pop("user", None)


def current_user() -> dict | None:
    return st.session_state.get("user")


def refresh_user() -> None:
    u = current_user()
    if u:
        fresh = fetch_one("SELECT * FROM users WHERE id = ?", [u["id"]])
        if fresh:
            st.session_state["user"] = _serialize(fresh)


def require_login() -> dict:
    u = current_user()
    if not u:
        st.warning("Please sign in to continue.")
        st.page_link("streamlit_app.py", label="Go to Sign in", icon="🔑")
        st.stop()
    return u


def require_role(roles: list[str]) -> dict:
    u = require_login()
    if u["role"] not in roles:
        st.error(f"This page is available only to: {', '.join(roles)}.")
        st.stop()
    return u


def _serialize(row: dict) -> dict:
    """Strip password_hash, convert verified int to bool."""
    if not row:
        return row
    d = dict(row)
    d.pop("password_hash", None)
    d["verified"] = bool(d.get("verified", 0))
    return d
