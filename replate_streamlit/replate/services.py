"""Business logic for listings, requests, vouchers, impact."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from .db import fetch_all, fetch_one, execute
from .utils import haversine_km, parse_iso
from .seed import CO2_PER_KG, MEALS_PER_UNIT


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ------------- LISTINGS ----------------------------------------------------

def list_active(category: str | None = None) -> list[dict]:
    sql = "SELECT * FROM listings WHERE status = 'active'"
    params: list = []
    if category:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY datetime(expiry_time) ASC"
    return fetch_all(sql, params)


def list_by_donor(donor_id: str, status: str | None = None) -> list[dict]:
    sql = "SELECT * FROM listings WHERE donor_id = ?"
    params: list = [donor_id]
    if status:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY datetime(created_at) DESC"
    return fetch_all(sql, params)


def get_listing(listing_id: str) -> dict | None:
    return fetch_one("SELECT * FROM listings WHERE id = ?", [listing_id])


def discover(user: dict, radius_km: float = 100.0, category: str | None = None) -> list[dict]:
    items = list_active(category)
    out = []
    for it in items:
        # Auto-expire
        if parse_iso(it["expiry_time"]) < datetime.now(timezone.utc):
            execute("UPDATE listings SET status = 'expired' WHERE id = ?", [it["id"]])
            continue
        dist = haversine_km(user.get("lat"), user.get("lng"), it.get("lat"), it.get("lng"))
        if user.get("lat") is not None and dist > radius_km:
            continue
        it_copy = dict(it)
        it_copy["distance_km"] = round(dist, 2) if user.get("lat") is not None else None
        out.append(it_copy)
    out.sort(key=lambda x: ((x.get("distance_km") or 0), x["expiry_time"]))
    return out


def create_listing(user: dict, data: dict) -> str:
    listing_id = str(uuid.uuid4())
    pin = str(uuid.uuid4().int)[:4]
    execute(
        """INSERT INTO listings
           (id, donor_id, donor_name, donor_org_type, name, description, category,
            quantity, remaining_quantity, unit, storage_condition, allergens, dietary,
            photo_url, pickup_address, lat, lng, pickup_start, pickup_end, expiry_time,
            status, pickup_pin, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [
            listing_id, user["id"], user.get("org_name") or user.get("name"),
            user.get("org_type"),
            data["name"], data.get("description"), data["category"],
            data["quantity"], data["quantity"], data["unit"], data["storage_condition"],
            ",".join(data.get("allergens", [])), ",".join(data.get("dietary", [])),
            data.get("photo_url"), data.get("pickup_address") or user.get("address"),
            user.get("lat"), user.get("lng"),
            data["pickup_start"].isoformat(), data["pickup_end"].isoformat(),
            data["expiry_time"].isoformat(),
            "active", pin, now_iso(),
        ],
    )
    return listing_id


def cancel_listing(listing_id: str) -> None:
    execute("UPDATE listings SET status = 'cancelled' WHERE id = ?", [listing_id])


# ------------- REQUESTS ----------------------------------------------------

def create_request(user: dict, listing_id: str, qty: float, note: str = "") -> tuple[bool, str]:
    listing = get_listing(listing_id)
    if not listing or listing["status"] != "active":
        return False, "Listing is not available."
    if qty <= 0 or qty > listing["remaining_quantity"]:
        return False, "Invalid quantity."
    if listing["donor_id"] == user["id"]:
        return False, "You can't request your own listing."
    if not user.get("verified"):
        return False, "Your organization must be verified by an admin first."
    # No duplicate pending
    dup = fetch_one(
        "SELECT id FROM requests WHERE listing_id = ? AND recipient_id = ? AND status = 'pending'",
        [listing_id, user["id"]],
    )
    if dup:
        return False, "You already have a pending request for this listing."
    rid = str(uuid.uuid4())
    execute(
        """INSERT INTO requests
           (id, listing_id, listing_name, donor_id, donor_name, recipient_id, recipient_name,
            requested_quantity, unit, note, status, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        [rid, listing_id, listing["name"], listing["donor_id"], listing["donor_name"],
         user["id"], user.get("org_name") or user.get("name"),
         qty, listing["unit"], note, "pending", now_iso()],
    )
    return True, rid


def requests_for(user: dict, role: str = "all") -> list[dict]:
    if role == "incoming":
        return fetch_all("SELECT * FROM requests WHERE donor_id = ? ORDER BY datetime(created_at) DESC", [user["id"]])
    if role == "outgoing":
        return fetch_all("SELECT * FROM requests WHERE recipient_id = ? ORDER BY datetime(created_at) DESC", [user["id"]])
    return fetch_all(
        "SELECT * FROM requests WHERE donor_id = ? OR recipient_id = ? ORDER BY datetime(created_at) DESC",
        [user["id"], user["id"]],
    )


def approve_request(request_id: str) -> None:
    execute("UPDATE requests SET status = 'approved', approved_at = ? WHERE id = ?",
            [now_iso(), request_id])


def reject_request(request_id: str) -> None:
    execute("UPDATE requests SET status = 'rejected' WHERE id = ?", [request_id])


def confirm_pickup(request_id: str, pin: str) -> tuple[bool, str, dict | None]:
    req = fetch_one("SELECT * FROM requests WHERE id = ?", [request_id])
    if not req:
        return False, "Request not found.", None
    if req["status"] != "approved":
        return False, "Request must be approved first.", None
    listing = get_listing(req["listing_id"])
    if not listing or str(pin).strip() != str(listing.get("pickup_pin")):
        return False, "Incorrect PIN.", None

    new_remaining = max(0.0, listing["remaining_quantity"] - req["requested_quantity"])
    new_status = "completed" if new_remaining <= 0 else "active"
    execute("UPDATE listings SET remaining_quantity = ?, status = ? WHERE id = ?",
            [new_remaining, new_status, listing["id"]])
    execute("UPDATE requests SET status = 'completed', completed_at = ? WHERE id = ?",
            [now_iso(), request_id])

    points = int(round(req["requested_quantity"] * 10))
    meals = req["requested_quantity"] * MEALS_PER_UNIT.get(listing["unit"], 1)
    co2 = req["requested_quantity"] * (CO2_PER_KG if listing["unit"] == "kg" else 0.5)
    execute("UPDATE users SET points = points + ? WHERE id = ?", [points, req["donor_id"]])
    execute(
        """INSERT INTO point_transactions (id, user_id, amount, type, reason, request_id, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        [str(uuid.uuid4()), req["donor_id"], points, "earned",
         f"Pickup completed: {listing['name']}", request_id, now_iso()],
    )
    execute(
        """INSERT INTO impact_events
           (id, donor_id, recipient_id, listing_id, request_id, quantity, unit, meals, co2_kg, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)""",
        [str(uuid.uuid4()), req["donor_id"], req["recipient_id"], listing["id"], request_id,
         req["requested_quantity"], listing["unit"], meals, co2, now_iso()],
    )
    return True, f"+{points} points awarded.", {"points": points, "meals": meals, "co2": co2}


# ------------- VOUCHERS ----------------------------------------------------

def list_vouchers() -> list[dict]:
    return fetch_all("SELECT * FROM vouchers ORDER BY points_cost ASC")


def redeem(user: dict, voucher_id: str) -> tuple[bool, str, str | None]:
    v = fetch_one("SELECT * FROM vouchers WHERE id = ?", [voucher_id])
    if not v:
        return False, "Voucher not found.", None
    fresh = fetch_one("SELECT points FROM users WHERE id = ?", [user["id"]])
    if (fresh["points"] or 0) < v["points_cost"]:
        return False, "Not enough points.", None
    code = f"RP-{uuid.uuid4().hex[:8].upper()}"
    execute("UPDATE users SET points = points - ? WHERE id = ?", [v["points_cost"], user["id"]])
    execute(
        """INSERT INTO redemptions
           (id, user_id, voucher_id, voucher_title, partner, points_cost, code, created_at)
           VALUES (?,?,?,?,?,?,?,?)""",
        [str(uuid.uuid4()), user["id"], v["id"], v["title"], v["partner"],
         v["points_cost"], code, now_iso()],
    )
    execute(
        """INSERT INTO point_transactions (id, user_id, amount, type, reason, created_at)
           VALUES (?,?,?,?,?,?)""",
        [str(uuid.uuid4()), user["id"], -v["points_cost"], "redeemed",
         f"Redeemed: {v['title']}", now_iso()],
    )
    return True, code, code


def my_redemptions(user_id: str) -> list[dict]:
    return fetch_all(
        "SELECT * FROM redemptions WHERE user_id = ? ORDER BY datetime(created_at) DESC",
        [user_id],
    )


def my_transactions(user_id: str) -> list[dict]:
    return fetch_all(
        "SELECT * FROM point_transactions WHERE user_id = ? ORDER BY datetime(created_at) DESC LIMIT 50",
        [user_id],
    )


# ------------- IMPACT ------------------------------------------------------

def _impact_stats(events: list[dict]) -> dict:
    total_kg = sum(e["quantity"] for e in events if e["unit"] == "kg")
    total_meals = sum(e["meals"] for e in events)
    total_co2 = sum(e["co2_kg"] for e in events)
    by_day: dict[str, float] = {}
    for e in events:
        d = parse_iso(e["created_at"]).date().isoformat()
        by_day[d] = by_day.get(d, 0) + e["meals"]
    return {
        "total_pickups": len(events),
        "total_kg": round(total_kg, 1),
        "total_meals": int(round(total_meals)),
        "total_co2_kg": round(total_co2, 1),
        "by_day": [{"date": k, "meals": int(round(v))} for k, v in sorted(by_day.items())],
    }


def global_impact() -> dict:
    return _impact_stats(fetch_all("SELECT * FROM impact_events"))


def impact_for_user(user: dict) -> dict:
    col = "donor_id" if user["role"] == "donor" else "recipient_id"
    return _impact_stats(fetch_all(f"SELECT * FROM impact_events WHERE {col} = ?", [user["id"]]))


def leaderboard() -> list[dict]:
    return fetch_all(
        "SELECT id, org_name, name, points FROM users WHERE role = 'donor' "
        "AND points > 0 ORDER BY points DESC LIMIT 10"
    )


# ------------- ADMIN -------------------------------------------------------

def admin_stats() -> dict:
    return {
        "users": fetch_one("SELECT COUNT(*) c FROM users")["c"],
        "donors": fetch_one("SELECT COUNT(*) c FROM users WHERE role = 'donor'")["c"],
        "recipients": fetch_one("SELECT COUNT(*) c FROM users WHERE role = 'recipient'")["c"],
        "pending_verifications": fetch_one(
            "SELECT COUNT(*) c FROM users WHERE role = 'recipient' AND verified = 0"
        )["c"],
        "active_listings": fetch_one("SELECT COUNT(*) c FROM listings WHERE status = 'active'")["c"],
        "completed_pickups": fetch_one("SELECT COUNT(*) c FROM requests WHERE status = 'completed'")["c"],
    }


def all_recipients() -> list[dict]:
    return fetch_all("SELECT * FROM users WHERE role = 'recipient' ORDER BY verified, org_name")


def verify_recipient(user_id: str) -> None:
    execute("UPDATE users SET verified = 1 WHERE id = ? AND role = 'recipient'", [user_id])


def unverify_recipient(user_id: str) -> None:
    execute("UPDATE users SET verified = 0 WHERE id = ? AND role = 'recipient'", [user_id])
