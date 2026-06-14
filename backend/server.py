from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import math
import random
import uuid
import logging
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Literal

from fastapi import FastAPI, APIRouter, HTTPException, Depends, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# ------------------------------- Setup -------------------------------

mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

JWT_ALGORITHM = "HS256"

def get_jwt_secret() -> str:
    return os.environ["JWT_SECRET"]


app = FastAPI(title="Food Waste Exchange API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ------------------------------- Helpers ------------------------------

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()

def parse_dt(v):
    if isinstance(v, datetime):
        return v
    if isinstance(v, str):
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    return v

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "exp": now_utc() + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm=JWT_ALGORITHM)


def serialize_user(u: dict) -> dict:
    return {
        "id": u["id"],
        "email": u["email"],
        "name": u.get("name"),
        "role": u.get("role"),
        "org_name": u.get("org_name"),
        "org_type": u.get("org_type"),
        "phone": u.get("phone"),
        "address": u.get("address"),
        "lat": u.get("lat"),
        "lng": u.get("lng"),
        "verified": u.get("verified", False),
        "points": u.get("points", 0),
        "created_at": u.get("created_at"),
    }


# ---------------------------- Pydantic Models -------------------------

Role = Literal["donor", "recipient", "admin"]
OrgType = Literal["restaurant", "cafe", "bakery", "ngo", "community_kitchen", "food_bank", "other"]
ListingStatus = Literal["active", "claimed", "completed", "expired", "cancelled"]
RequestStatus = Literal["pending", "approved", "rejected", "completed", "cancelled"]
FoodCategory = Literal["produce", "bakery", "prepared_meals", "dairy", "pantry", "beverages", "other"]
StorageCondition = Literal["ambient", "refrigerated", "frozen", "hot"]


class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str
    role: Role
    org_name: Optional[str] = None
    org_type: Optional[OrgType] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    org_name: Optional[str] = None
    org_type: Optional[OrgType] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class ListingIn(BaseModel):
    name: str
    description: Optional[str] = None
    category: FoodCategory
    quantity: float
    unit: str = "servings"
    storage_condition: StorageCondition = "ambient"
    allergens: List[str] = []
    dietary: List[str] = []
    photo_url: Optional[str] = None
    pickup_address: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    pickup_start: datetime
    pickup_end: datetime
    expiry_time: datetime
    safety_acknowledged: bool = True


class RequestIn(BaseModel):
    listing_id: str
    requested_quantity: float
    note: Optional[str] = None


class RedeemIn(BaseModel):
    voucher_id: str


# ----------------------------- Auth helpers ---------------------------

async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def require_role(user: dict, roles: List[str]):
    if user.get("role") not in roles:
        raise HTTPException(status_code=403, detail=f"Requires role: {', '.join(roles)}")


def set_auth_cookie(response: Response, token: str):
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )


# ----------------------------- Distance util --------------------------

def haversine_km(lat1, lng1, lat2, lng2) -> float:
    if None in (lat1, lng1, lat2, lng2):
        return 999.0
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


# ----------------------------- Auth endpoints --------------------------

@api.post("/auth/register")
async def register(body: RegisterIn, response: Response):
    email = body.email.lower().strip()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    user = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(body.password),
        "name": body.name,
        "role": body.role,
        "org_name": body.org_name,
        "org_type": body.org_type,
        "phone": body.phone,
        "address": body.address,
        "lat": body.lat,
        "lng": body.lng,
        # Recipients require admin verification before they can claim
        "verified": body.role == "donor",
        "points": 0,
        "created_at": iso(now_utc()),
    }
    await db.users.insert_one(user)
    token = create_access_token(user["id"], user["email"])
    set_auth_cookie(response, token)
    return {"user": serialize_user(user), "token": token}


@api.post("/auth/login")
async def login(body: LoginIn, response: Response):
    email = body.email.lower().strip()
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token(user["id"], user["email"])
    set_auth_cookie(response, token)
    return {"user": serialize_user(user), "token": token}


@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}


@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return serialize_user(user)


@api.patch("/auth/profile")
async def update_profile(body: ProfileUpdate, user: dict = Depends(get_current_user)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if updates:
        await db.users.update_one({"id": user["id"]}, {"$set": updates})
    fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    return serialize_user(fresh)


# ----------------------------- Listings -------------------------------

CO2_PER_KG = 2.5  # estimate kg CO2 saved per kg food rescued
MEALS_PER_UNIT = {"servings": 1, "kg": 2, "items": 0.5, "loaves": 4, "trays": 8}


@api.post("/listings")
async def create_listing(body: ListingIn, user: dict = Depends(get_current_user)):
    await require_role(user, ["donor"])
    pin = str(uuid.uuid4().int)[:4]
    listing = {
        "id": str(uuid.uuid4()),
        "donor_id": user["id"],
        "donor_name": user.get("org_name") or user.get("name"),
        "donor_org_type": user.get("org_type"),
        "name": body.name,
        "description": body.description,
        "category": body.category,
        "quantity": body.quantity,
        "remaining_quantity": body.quantity,
        "unit": body.unit,
        "storage_condition": body.storage_condition,
        "allergens": body.allergens,
        "dietary": body.dietary,
        "photo_url": body.photo_url,
        "pickup_address": body.pickup_address,
        "lat": body.lat or user.get("lat"),
        "lng": body.lng or user.get("lng"),
        "pickup_start": iso(body.pickup_start),
        "pickup_end": iso(body.pickup_end),
        "expiry_time": iso(body.expiry_time),
        "status": "active",
        "pickup_pin": pin,
        "created_at": iso(now_utc()),
    }
    await db.listings.insert_one(listing)
    listing.pop("_id", None)
    return listing


@api.get("/listings")
async def list_listings(
    status: Optional[str] = None,
    mine: bool = False,
    user: dict = Depends(get_current_user),
):
    q = {}
    if mine:
        q["donor_id"] = user["id"]
    if status:
        q["status"] = status
    items = await db.listings.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    # Auto-expire
    now = now_utc()
    for it in items:
        if it["status"] == "active" and parse_dt(it["expiry_time"]) < now:
            await db.listings.update_one({"id": it["id"]}, {"$set": {"status": "expired"}})
            it["status"] = "expired"
    return items


@api.get("/listings/discover")
async def discover(
    radius_km: float = 50.0,
    category: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """Public discovery for recipients — active listings sorted by distance + expiry."""
    q = {"status": "active"}
    if category:
        q["category"] = category
    items = await db.listings.find(q, {"_id": 0}).to_list(500)
    out = []
    now = now_utc()
    user_lat = user.get("lat")
    user_lng = user.get("lng")
    for it in items:
        if parse_dt(it["expiry_time"]) < now:
            continue
        dist = haversine_km(user_lat, user_lng, it.get("lat"), it.get("lng"))
        if user_lat is not None and dist > radius_km:
            continue
        it_copy = {**it}
        it_copy["distance_km"] = round(dist, 2) if user_lat is not None else None
        # Hide exact address until approved
        it_copy["pickup_pin"] = None
        out.append(it_copy)
    out.sort(key=lambda x: (x.get("distance_km") or 0, parse_dt(x["expiry_time"])))
    return out


@api.get("/listings/{listing_id}")
async def get_listing(listing_id: str, user: dict = Depends(get_current_user)):
    listing = await db.listings.find_one({"id": listing_id}, {"_id": 0})
    if not listing:
        raise HTTPException(404, "Listing not found")
    # Only show pin to donor or to recipient with approved request
    if listing["donor_id"] != user["id"]:
        approved = await db.requests.find_one({
            "listing_id": listing_id,
            "recipient_id": user["id"],
            "status": {"$in": ["approved", "completed"]},
        })
        if not approved:
            listing["pickup_pin"] = None
    return listing


@api.delete("/listings/{listing_id}")
async def cancel_listing(listing_id: str, user: dict = Depends(get_current_user)):
    listing = await db.listings.find_one({"id": listing_id})
    if not listing:
        raise HTTPException(404, "Not found")
    if listing["donor_id"] != user["id"]:
        raise HTTPException(403, "Not your listing")
    await db.listings.update_one({"id": listing_id}, {"$set": {"status": "cancelled"}})
    return {"ok": True}


# ----------------------------- Requests -------------------------------

@api.post("/requests")
async def create_request(body: RequestIn, user: dict = Depends(get_current_user)):
    await require_role(user, ["recipient"])
    if not user.get("verified"):
        raise HTTPException(403, "Recipient organization must be verified by an admin first")
    listing = await db.listings.find_one({"id": body.listing_id})
    if not listing:
        raise HTTPException(404, "Listing not found")
    if listing["status"] != "active":
        raise HTTPException(400, "Listing not available")
    if body.requested_quantity <= 0 or body.requested_quantity > listing["remaining_quantity"]:
        raise HTTPException(400, "Invalid requested quantity")
    # prevent duplicate pending request
    existing = await db.requests.find_one({
        "listing_id": body.listing_id,
        "recipient_id": user["id"],
        "status": "pending",
    })
    if existing:
        raise HTTPException(400, "You already have a pending request for this listing")
    req = {
        "id": str(uuid.uuid4()),
        "listing_id": body.listing_id,
        "listing_name": listing["name"],
        "donor_id": listing["donor_id"],
        "donor_name": listing.get("donor_name"),
        "recipient_id": user["id"],
        "recipient_name": user.get("org_name") or user.get("name"),
        "requested_quantity": body.requested_quantity,
        "unit": listing["unit"],
        "note": body.note,
        "status": "pending",
        "created_at": iso(now_utc()),
    }
    await db.requests.insert_one(req)
    req.pop("_id", None)
    return req


@api.get("/requests")
async def list_requests(role: Optional[str] = None, user: dict = Depends(get_current_user)):
    """role=incoming returns requests for the donor's listings; role=outgoing for recipient."""
    if role == "incoming":
        q = {"donor_id": user["id"]}
    elif role == "outgoing":
        q = {"recipient_id": user["id"]}
    else:
        q = {"$or": [{"donor_id": user["id"]}, {"recipient_id": user["id"]}]}
    items = await db.requests.find(q, {"_id": 0}).sort("created_at", -1).to_list(500)
    return items


@api.post("/requests/{req_id}/approve")
async def approve_request(req_id: str, user: dict = Depends(get_current_user)):
    req = await db.requests.find_one({"id": req_id})
    if not req:
        raise HTTPException(404, "Not found")
    if req["donor_id"] != user["id"]:
        raise HTTPException(403, "Not authorized")
    if req["status"] != "pending":
        raise HTTPException(400, "Request not pending")
    await db.requests.update_one({"id": req_id}, {"$set": {"status": "approved", "approved_at": iso(now_utc())}})
    # Reserve quantity but don't fully claim until completion
    return {"ok": True}


@api.post("/requests/{req_id}/reject")
async def reject_request(req_id: str, user: dict = Depends(get_current_user)):
    req = await db.requests.find_one({"id": req_id})
    if not req:
        raise HTTPException(404, "Not found")
    if req["donor_id"] != user["id"]:
        raise HTTPException(403, "Not authorized")
    if req["status"] != "pending":
        raise HTTPException(400, "Request not pending")
    await db.requests.update_one({"id": req_id}, {"$set": {"status": "rejected"}})
    return {"ok": True}


class ConfirmIn(BaseModel):
    pin: str


@api.post("/requests/{req_id}/confirm")
async def confirm_pickup(req_id: str, body: ConfirmIn, user: dict = Depends(get_current_user)):
    req = await db.requests.find_one({"id": req_id})
    if not req:
        raise HTTPException(404, "Not found")
    if req["recipient_id"] != user["id"]:
        raise HTTPException(403, "Only the recipient can confirm pickup")
    if req["status"] != "approved":
        raise HTTPException(400, "Request must be approved before pickup")
    listing = await db.listings.find_one({"id": req["listing_id"]})
    if not listing:
        raise HTTPException(404, "Listing missing")
    if body.pin.strip() != listing.get("pickup_pin"):
        raise HTTPException(400, "Incorrect pickup PIN")

    # Update remaining quantity and listing status
    new_remaining = max(0.0, listing["remaining_quantity"] - req["requested_quantity"])
    new_status = "completed" if new_remaining <= 0 else "active"
    await db.listings.update_one(
        {"id": listing["id"]},
        {"$set": {"remaining_quantity": new_remaining, "status": new_status}},
    )
    await db.requests.update_one(
        {"id": req_id},
        {"$set": {"status": "completed", "completed_at": iso(now_utc())}},
    )

    # Award points (10 per unit)
    points_to_award = int(round(req["requested_quantity"] * 10))
    meals = req["requested_quantity"] * MEALS_PER_UNIT.get(listing["unit"], 1)
    co2 = req["requested_quantity"] * (CO2_PER_KG if listing["unit"] == "kg" else 0.5)

    await db.users.update_one({"id": req["donor_id"]}, {"$inc": {"points": points_to_award}})
    await db.point_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": req["donor_id"],
        "amount": points_to_award,
        "type": "earned",
        "reason": f"Pickup completed: {listing['name']}",
        "request_id": req_id,
        "created_at": iso(now_utc()),
    })
    await db.impact_events.insert_one({
        "id": str(uuid.uuid4()),
        "donor_id": req["donor_id"],
        "recipient_id": req["recipient_id"],
        "listing_id": listing["id"],
        "request_id": req_id,
        "quantity": req["requested_quantity"],
        "unit": listing["unit"],
        "meals": meals,
        "co2_kg": co2,
        "created_at": iso(now_utc()),
    })

    return {"ok": True, "points_awarded": points_to_award, "meals": meals, "co2_kg": co2}


# ------------------------------ Rewards -------------------------------

@api.get("/vouchers")
async def list_vouchers():
    items = await db.vouchers.find({}, {"_id": 0}).sort("points_cost", 1).to_list(100)
    return items


@api.post("/vouchers/redeem")
async def redeem_voucher(body: RedeemIn, user: dict = Depends(get_current_user)):
    v = await db.vouchers.find_one({"id": body.voucher_id}, {"_id": 0})
    if not v:
        raise HTTPException(404, "Voucher not found")
    fresh = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if fresh.get("points", 0) < v["points_cost"]:
        raise HTTPException(400, "Not enough points")
    code = f"FX-{uuid.uuid4().hex[:8].upper()}"
    await db.users.update_one({"id": user["id"]}, {"$inc": {"points": -v["points_cost"]}})
    redemption = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "voucher_id": v["id"],
        "voucher_title": v["title"],
        "partner": v["partner"],
        "points_cost": v["points_cost"],
        "code": code,
        "created_at": iso(now_utc()),
    }
    await db.redemptions.insert_one(redemption)
    await db.point_transactions.insert_one({
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "amount": -v["points_cost"],
        "type": "redeemed",
        "reason": f"Redeemed: {v['title']}",
        "created_at": iso(now_utc()),
    })
    redemption.pop("_id", None)
    return redemption


@api.get("/redemptions")
async def my_redemptions(user: dict = Depends(get_current_user)):
    items = await db.redemptions.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return items


@api.get("/points/transactions")
async def my_points(user: dict = Depends(get_current_user)):
    items = await db.point_transactions.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(200)
    return items


# ------------------------------ Impact --------------------------------

@api.get("/impact/me")
async def impact_me(user: dict = Depends(get_current_user)):
    q = {"donor_id": user["id"]} if user["role"] == "donor" else {"recipient_id": user["id"]}
    events = await db.impact_events.find(q, {"_id": 0}).to_list(2000)
    total_kg = sum(e["quantity"] for e in events if e["unit"] == "kg")
    total_meals = sum(e["meals"] for e in events)
    total_co2 = sum(e["co2_kg"] for e in events)
    return {
        "total_pickups": len(events),
        "total_kg": round(total_kg, 1),
        "total_meals": int(round(total_meals)),
        "total_co2_kg": round(total_co2, 1),
        "by_day": _by_day(events),
    }


@api.get("/impact/global")
async def impact_global():
    events = await db.impact_events.find({}, {"_id": 0}).to_list(5000)
    total_kg = sum(e["quantity"] for e in events if e["unit"] == "kg")
    total_meals = sum(e["meals"] for e in events)
    total_co2 = sum(e["co2_kg"] for e in events)
    return {
        "total_pickups": len(events),
        "total_kg": round(total_kg, 1),
        "total_meals": int(round(total_meals)),
        "total_co2_kg": round(total_co2, 1),
        "by_day": _by_day(events),
    }


def _by_day(events):
    bucket = {}
    for e in events:
        d = parse_dt(e["created_at"]).date().isoformat()
        bucket[d] = bucket.get(d, 0) + e["meals"]
    return [{"date": k, "meals": int(round(v))} for k, v in sorted(bucket.items())]


@api.get("/leaderboard")
async def leaderboard():
    donors = await db.users.find({"role": "donor"}, {"_id": 0, "password_hash": 0}).sort("points", -1).limit(10).to_list(10)
    return [serialize_user(u) for u in donors]


# ------------------------------ Admin ---------------------------------

@api.get("/admin/pending-recipients")
async def pending_recipients(user: dict = Depends(get_current_user)):
    await require_role(user, ["admin"])
    items = await db.users.find({"role": "recipient", "verified": False}, {"_id": 0, "password_hash": 0}).to_list(200)
    return [serialize_user(u) for u in items]


@api.get("/admin/recipients")
async def all_recipients(user: dict = Depends(get_current_user)):
    await require_role(user, ["admin"])
    items = await db.users.find({"role": "recipient"}, {"_id": 0, "password_hash": 0}).to_list(500)
    return [serialize_user(u) for u in items]


@api.post("/admin/verify/{user_id}")
async def verify_recipient(user_id: str, user: dict = Depends(get_current_user)):
    await require_role(user, ["admin"])
    await db.users.update_one({"id": user_id, "role": "recipient"}, {"$set": {"verified": True}})
    return {"ok": True}


@api.post("/admin/unverify/{user_id}")
async def unverify_recipient(user_id: str, user: dict = Depends(get_current_user)):
    await require_role(user, ["admin"])
    await db.users.update_one({"id": user_id, "role": "recipient"}, {"$set": {"verified": False}})
    return {"ok": True}


@api.get("/admin/stats")
async def admin_stats(user: dict = Depends(get_current_user)):
    await require_role(user, ["admin"])
    return {
        "users": await db.users.count_documents({}),
        "donors": await db.users.count_documents({"role": "donor"}),
        "recipients": await db.users.count_documents({"role": "recipient"}),
        "pending_verifications": await db.users.count_documents({"role": "recipient", "verified": False}),
        "active_listings": await db.listings.count_documents({"status": "active"}),
        "completed_pickups": await db.requests.count_documents({"status": "completed"}),
    }


# ----------------------------- Misc -----------------------------------

@api.get("/")
async def root():
    return {"name": "Food Waste Exchange API", "status": "ok"}


# ------------------------------ Seed ---------------------------------

SAMPLE_VOUCHERS = [
    {"id": "v-coffee-1", "partner": "Loom Coffee Roasters", "title": "Free Pour-Over Coffee", "description": "Redeemable at any Loom location for one hand-brewed coffee.", "points_cost": 80, "image_url": "https://images.unsplash.com/photo-1497935586351-b67a49e012bf?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-grocery-1", "partner": "Heirloom Grocers", "title": "$10 Grocery Voucher", "description": "Toward any seasonal produce at Heirloom.", "points_cost": 250, "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-bakery-1", "partner": "Folk & Flour", "title": "Free Pastry of the Day", "description": "Pick any pastry from the morning case.", "points_cost": 60, "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-meal-1", "partner": "Field & Vine", "title": "Two-Course Lunch", "description": "Seasonal prix-fixe lunch for one.", "points_cost": 500, "image_url": "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-tote-1", "partner": "Food Xchange", "title": "Canvas Tote Bag", "description": "Made from organic, undyed cotton.", "points_cost": 150, "image_url": "https://images.unsplash.com/photo-1593113565687-cc2f464d1f2e?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-tree-1", "partner": "One Tree Planted", "title": "Plant 5 Trees", "description": "Donate points to fund tree planting.", "points_cost": 300, "image_url": "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?auto=format&fit=crop&q=80&w=800"},
]

SAMPLE_DONORS = [
    {"email": "niloufer@foodxchange.in", "name": "Rafiq Hussain", "org_name": "Café Niloufer", "org_type": "cafe", "address": "Lakdi-ka-Pul, Hyderabad", "lat": 17.3998, "lng": 78.4730},
    {"email": "karachi@foodxchange.in", "name": "Aarti Khanna", "org_name": "Karachi Bakery", "org_type": "bakery", "address": "Mehdipatnam Rd, Banjara Hills, Hyderabad", "lat": 17.4156, "lng": 78.4351},
    {"email": "paradise@foodxchange.in", "name": "Imran Qureshi", "org_name": "Paradise Restaurant", "org_type": "restaurant", "address": "SD Road, Secunderabad, Hyderabad", "lat": 17.4399, "lng": 78.4983},
    {"email": "chutneys@foodxchange.in", "name": "Lakshmi Reddy", "org_name": "Chutneys", "org_type": "restaurant", "address": "Jubilee Hills, Hyderabad", "lat": 17.4326, "lng": 78.4071},
    {"email": "pistahouse@foodxchange.in", "name": "Mohammed Abdul Majeed", "org_name": "Pista House", "org_type": "bakery", "address": "Shah Ali Banda, Charminar, Hyderabad", "lat": 17.3604, "lng": 78.4736},
    {"email": "bawarchi@foodxchange.in", "name": "Suresh Kothapalli", "org_name": "Bawarchi Restaurant", "org_type": "restaurant", "address": "RTC X Roads, Hyderabad", "lat": 17.4030, "lng": 78.4986},
    {"email": "ohris@foodxchange.in", "name": "Punita Sanghvi", "org_name": "Ohri's Banjara", "org_type": "restaurant", "address": "Road No. 12, Banjara Hills, Hyderabad", "lat": 17.4148, "lng": 78.4319},
    {"email": "almondhouse@foodxchange.in", "name": "Khalid Pasha", "org_name": "Almond House", "org_type": "bakery", "address": "Road No. 36, Jubilee Hills, Hyderabad", "lat": 17.4234, "lng": 78.4070},
    {"email": "concu@foodxchange.in", "name": "Nivedita Sharma", "org_name": "Conçu Patisserie", "org_type": "bakery", "address": "Road No. 1, Banjara Hills, Hyderabad", "lat": 17.4126, "lng": 78.4486},
]

SAMPLE_RECIPIENTS = [
    {"email": "akshaya@foodxchange.in", "name": "Anand Rao", "org_name": "Akshaya Patra Hyderabad", "org_type": "community_kitchen", "address": "Narsingi, Hyderabad", "lat": 17.4239, "lng": 78.4738, "verified": True},
    {"email": "helpinghand@foodxchange.in", "name": "Mujtaba Hasan Askari", "org_name": "Helping Hand Foundation", "org_type": "ngo", "address": "Mehdipatnam, Hyderabad", "lat": 17.4156, "lng": 78.4347, "verified": True},
    {"email": "robinhood@foodxchange.in", "name": "Sanjana Iyer", "org_name": "Robin Hood Army Hyd", "org_type": "ngo", "address": "Gachibowli, Hyderabad", "lat": 17.4400, "lng": 78.3489, "verified": False},
    {"email": "goonj@foodxchange.in", "name": "Vikram Bhargava", "org_name": "Goonj Hyderabad", "org_type": "ngo", "address": "Kondapur, Hyderabad", "lat": 17.4647, "lng": 78.3654, "verified": True},
    {"email": "feedingindia@foodxchange.in", "name": "Ankit Kawatra", "org_name": "Feeding India — Zomato Foundation", "org_type": "food_bank", "address": "Madhapur, Hyderabad", "lat": 17.4483, "lng": 78.3915, "verified": True},
    {"email": "aasara@foodxchange.in", "name": "Padmaja Rao", "org_name": "Aasara Old Age Home", "org_type": "community_kitchen", "address": "Saidabad, Hyderabad", "lat": 17.3645, "lng": 78.5043, "verified": True},
    {"email": "bhumi@foodxchange.in", "name": "Ritika Singhal", "org_name": "Bhumi Hyderabad", "org_type": "ngo", "address": "Begumpet, Hyderabad", "lat": 17.4399, "lng": 78.4634, "verified": True},
]

SAMPLE_LISTINGS = [
    {
        "donor_email": "niloufer@foodxchange.in",
        "name": "Irani chai urns & Osmania biscuits",
        "description": "End-of-evening Irani chai and freshly-baked Osmania biscuits from today's batch.",
        "category": "bakery", "quantity": 40, "unit": "items", "storage_condition": "ambient",
        "allergens": ["gluten", "dairy"], "dietary": ["vegetarian"],
        "photo_url": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (1, 5), "expiry_hours_from_now": 8,
    },
    {
        "donor_email": "paradise@foodxchange.in",
        "name": "Hyderabadi dum biryani — 20 portions",
        "description": "Surplus chicken & veg dum biryani from tonight's service. Sealed in eco trays, ready to serve.",
        "category": "prepared_meals", "quantity": 20, "unit": "servings", "storage_condition": "hot",
        "allergens": ["nuts", "dairy"], "dietary": ["halal"],
        "photo_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (0, 2), "expiry_hours_from_now": 4,
    },
    {
        "donor_email": "karachi@foodxchange.in",
        "name": "Fruit biscuits, cake slices & rusks",
        "description": "Surplus bakery items near best-by date. Excellent for tea-time distribution.",
        "category": "bakery", "quantity": 12, "unit": "kg", "storage_condition": "ambient",
        "allergens": ["gluten", "dairy", "nuts"], "dietary": ["vegetarian"],
        "photo_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (2, 8), "expiry_hours_from_now": 24,
    },
    {
        "donor_email": "chutneys@foodxchange.in",
        "name": "Idli, dosa batter & sambar (large batch)",
        "description": "Surplus South Indian breakfast prep — idli, dosa batter, sambar and chutneys.",
        "category": "prepared_meals", "quantity": 30, "unit": "servings", "storage_condition": "refrigerated",
        "allergens": [], "dietary": ["vegetarian", "vegan", "gluten-free"],
        "photo_url": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (1, 6), "expiry_hours_from_now": 14,
    },
    {
        "donor_email": "niloufer@foodxchange.in",
        "name": "Cold milk bottles & samosas",
        "description": "Unopened buffalo milk bottles + crispy veg samosas from evening counter.",
        "category": "beverages", "quantity": 36, "unit": "items", "storage_condition": "refrigerated",
        "allergens": ["dairy", "gluten"], "dietary": ["vegetarian"],
        "photo_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (1, 10), "expiry_hours_from_now": 30,
    },
    {
        "donor_email": "pistahouse@foodxchange.in",
        "name": "Haleem trays — Ramadan special",
        "description": "Slow-cooked mutton haleem, freshly prepared. Sealed trays, ready to distribute.",
        "category": "prepared_meals", "quantity": 25, "unit": "servings", "storage_condition": "hot",
        "allergens": ["gluten", "dairy"], "dietary": ["halal"],
        "photo_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (0, 3), "expiry_hours_from_now": 5,
    },
    {
        "donor_email": "pistahouse@foodxchange.in",
        "name": "Mawa cakes, fruit cake & dilkush",
        "description": "Surplus signature bakery items from today's counter. Best within 24 hours.",
        "category": "bakery", "quantity": 8, "unit": "kg", "storage_condition": "ambient",
        "allergens": ["gluten", "dairy", "nuts", "eggs"], "dietary": ["vegetarian"],
        "photo_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (1, 8), "expiry_hours_from_now": 20,
    },
    {
        "donor_email": "bawarchi@foodxchange.in",
        "name": "Mutton biryani + raita pots (15 portions)",
        "description": "Signature Bawarchi mutton biryani, served with mirchi salan and raita.",
        "category": "prepared_meals", "quantity": 15, "unit": "servings", "storage_condition": "hot",
        "allergens": ["dairy", "nuts"], "dietary": ["halal"],
        "photo_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (0, 2), "expiry_hours_from_now": 4,
    },
    {
        "donor_email": "ohris@foodxchange.in",
        "name": "Mirchi ka salan, bagara baingan & rotis",
        "description": "Surplus North Indian + Hyderabadi gravies and 60 fresh rotis. Refrigerated.",
        "category": "prepared_meals", "quantity": 22, "unit": "servings", "storage_condition": "refrigerated",
        "allergens": ["dairy", "nuts", "gluten"], "dietary": ["vegetarian"],
        "photo_url": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (1, 6), "expiry_hours_from_now": 18,
    },
    {
        "donor_email": "almondhouse@foodxchange.in",
        "name": "Badam halwa, dry-fruit laddoos & kaju katli",
        "description": "Surplus mithai trays from today's production. Sealed boxes.",
        "category": "other", "quantity": 6, "unit": "kg", "storage_condition": "ambient",
        "allergens": ["nuts", "dairy"], "dietary": ["vegetarian", "gluten-free"],
        "photo_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (2, 12), "expiry_hours_from_now": 48,
    },
    {
        "donor_email": "concu@foodxchange.in",
        "name": "French pastries, croissants & quiche",
        "description": "End-of-day patisserie surplus — almond croissants, eclairs, mini quiches.",
        "category": "bakery", "quantity": 32, "unit": "items", "storage_condition": "refrigerated",
        "allergens": ["gluten", "dairy", "eggs", "nuts"], "dietary": ["vegetarian"],
        "photo_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (0, 4), "expiry_hours_from_now": 12,
    },
    {
        "donor_email": "karachi@foodxchange.in",
        "name": "Plum cake, dundee cake & banana bread",
        "description": "Surplus tea-time loaves perfect for evening distribution.",
        "category": "bakery", "quantity": 18, "unit": "loaves", "storage_condition": "ambient",
        "allergens": ["gluten", "dairy", "eggs", "nuts"], "dietary": ["vegetarian"],
        "photo_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&q=80&w=1000",
        "pickup_hours_from_now": (3, 10), "expiry_hours_from_now": 36,
    },
]


async def seed():
    await db.users.create_index("email", unique=True)
    await db.listings.create_index("status")
    await db.requests.create_index("status")

    # Cleanup OLD seeded sample data (one-time migration from US -> Hyderabad demo)
    OLD_SAMPLE_EMAILS = [
        "luma@cafeluma.app", "folk@folkflour.app", "field@fieldvine.app",
        "harbor@harborkitchen.app", "shelter@kindshelter.app",
    ]
    old_users = await db.users.find({"email": {"$in": OLD_SAMPLE_EMAILS}}, {"id": 1, "_id": 0}).to_list(100)
    old_ids = [u["id"] for u in old_users]
    if old_ids:
        await db.listings.delete_many({"donor_id": {"$in": old_ids}})
        await db.requests.delete_many({"$or": [{"donor_id": {"$in": old_ids}}, {"recipient_id": {"$in": old_ids}}]})
        await db.point_transactions.delete_many({"user_id": {"$in": old_ids}})
        await db.impact_events.delete_many({"$or": [{"donor_id": {"$in": old_ids}}, {"recipient_id": {"$in": old_ids}}]})
        await db.redemptions.delete_many({"user_id": {"$in": old_ids}})
        await db.users.delete_many({"email": {"$in": OLD_SAMPLE_EMAILS}})
        logger.info("Cleaned up %d old sample users + related data", len(old_ids))

    # Admin
    admin_email = os.environ["ADMIN_EMAIL"].lower()
    admin_pw = os.environ["ADMIN_PASSWORD"]
    existing = await db.users.find_one({"email": admin_email})
    if not existing:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": admin_email,
            "password_hash": hash_password(admin_pw),
            "name": "Platform Admin",
            "role": "admin",
            "verified": True,
            "points": 0,
            "created_at": iso(now_utc()),
        })
        logger.info("Seeded admin user: %s", admin_email)
    elif not verify_password(admin_pw, existing["password_hash"]):
        await db.users.update_one({"email": admin_email}, {"$set": {"password_hash": hash_password(admin_pw)}})

    # Donors
    donor_map = {}
    for d in SAMPLE_DONORS:
        existing = await db.users.find_one({"email": d["email"]})
        if not existing:
            doc = {
                "id": str(uuid.uuid4()),
                "email": d["email"],
                "password_hash": hash_password("Demo123!"),
                "name": d["name"],
                "role": "donor",
                "org_name": d["org_name"],
                "org_type": d["org_type"],
                "phone": "+1 555 0100",
                "address": d["address"],
                "lat": d["lat"],
                "lng": d["lng"],
                "verified": True,
                "points": 0,
                "created_at": iso(now_utc()),
            }
            await db.users.insert_one(doc)
            donor_map[d["email"]] = doc["id"]
        else:
            donor_map[d["email"]] = existing["id"]

    # Recipients
    for r in SAMPLE_RECIPIENTS:
        existing = await db.users.find_one({"email": r["email"]})
        if not existing:
            await db.users.insert_one({
                "id": str(uuid.uuid4()),
                "email": r["email"],
                "password_hash": hash_password("Demo123!"),
                "name": r["name"],
                "role": "recipient",
                "org_name": r["org_name"],
                "org_type": r["org_type"],
                "phone": "+1 555 0200",
                "address": r["address"],
                "lat": r["lat"],
                "lng": r["lng"],
                "verified": r.get("verified", False),
                "points": 0,
                "created_at": iso(now_utc()),
            })

    # Vouchers
    for v in SAMPLE_VOUCHERS:
        await db.vouchers.update_one({"id": v["id"]}, {"$set": v}, upsert=True)

    # Listings — deterministic upsert so updates to seed photos/descriptions take effect
    now = now_utc()
    sample_names = {s["name"] for s in SAMPLE_LISTINGS}
    sample_donor_ids = list(donor_map.values())
    # Remove old duplicate UUID-based seed listings: same name & donor as a sample,
    # but id doesn't start with "seed-", and has no activity. Preserves user listings.
    duplicates = await db.listings.find({
        "donor_id": {"$in": sample_donor_ids},
        "name": {"$in": list(sample_names)},
        "id": {"$not": {"$regex": "^seed-"}},
    }, {"id": 1, "_id": 0}).to_list(200)
    dup_ids = [d["id"] for d in duplicates]
    if dup_ids:
        has_activity_ids = set()
        async for req in db.requests.find({"listing_id": {"$in": dup_ids}}, {"listing_id": 1, "_id": 0}):
            has_activity_ids.add(req["listing_id"])
        to_delete = [i for i in dup_ids if i not in has_activity_ids]
        if to_delete:
            await db.listings.delete_many({"id": {"$in": to_delete}})
            logger.info("Removed %d duplicate UUID-based seed listings", len(to_delete))

    # One-time migration: update photos on user-created listings that still have
    # the old generic produce-default photo for a non-produce category.
    OLD_GENERIC = "https://images.unsplash.com/photo-1542838132-92c53300491e"
    CATEGORY_PHOTO_MAP = {
        "bakery": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000",
        "prepared_meals": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=1000",
        "dairy": "https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&q=80&w=1000",
        "pantry": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&q=80&w=1000",
        "beverages": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?auto=format&fit=crop&q=80&w=1000",
        "other": "https://images.unsplash.com/photo-1593113565687-cc2f464d1f2e?auto=format&fit=crop&q=80&w=1000",
    }
    async for doc in db.listings.find({
        "photo_url": {"$regex": OLD_GENERIC},
        "category": {"$ne": "produce"},
    }, {"id": 1, "category": 1, "_id": 0}):
        new_url = CATEGORY_PHOTO_MAP.get(doc["category"])
        if new_url:
            await db.listings.update_one({"id": doc["id"]}, {"$set": {"photo_url": new_url}})

    for s in SAMPLE_LISTINGS:
        donor_id = donor_map.get(s["donor_email"])
        if not donor_id:
            continue
        donor = await db.users.find_one({"id": donor_id})
        ps, pe = s["pickup_hours_from_now"]
        deterministic_id = f"seed-{s['donor_email'].split('@')[0]}-{s['name'][:30].lower().replace(' ', '-').replace(',', '')}"
        existing = await db.listings.find_one({"id": deterministic_id})
        # If any request was made against this seeded listing, leave it untouched
        has_activity = False
        if existing:
            has_activity = bool(await db.requests.find_one({"listing_id": deterministic_id}))
        if has_activity:
            continue
        listing = {
            "id": deterministic_id,
            "donor_id": donor_id,
            "donor_name": donor.get("org_name"),
            "donor_org_type": donor.get("org_type"),
            "name": s["name"],
            "description": s["description"],
            "category": s["category"],
            "quantity": s["quantity"],
            "remaining_quantity": s["quantity"],
            "unit": s["unit"],
            "storage_condition": s["storage_condition"],
            "allergens": s["allergens"],
            "dietary": s["dietary"],
            "photo_url": s["photo_url"],
            "pickup_address": donor.get("address"),
            "lat": donor.get("lat"),
            "lng": donor.get("lng"),
            "pickup_start": iso(now + timedelta(hours=ps)),
            "pickup_end": iso(now + timedelta(hours=pe)),
            "expiry_time": iso(now + timedelta(hours=s["expiry_hours_from_now"])),
            "status": "active",
            "pickup_pin": existing.get("pickup_pin") if existing else str(uuid.uuid4().int)[:4],
            "created_at": existing.get("created_at") if existing else iso(now),
        }
        await db.listings.update_one({"id": deterministic_id}, {"$set": listing}, upsert=True)
    logger.info("Seeded/refreshed sample listings")

    # Seed historical impact events so dashboards/landing show realistic numbers.
    # Idempotent: only inserts if no events with marker "seed-history-" exist.
    existing_history = await db.impact_events.find_one({"id": {"$regex": "^seed-history-"}})
    if not existing_history:
        donor_ids = list(donor_map.values())
        verified_recipient_ids = []
        async for u in db.users.find({"role": "recipient", "verified": True}, {"id": 1, "_id": 0}):
            verified_recipient_ids.append(u["id"])
        if donor_ids and verified_recipient_ids:
            random.seed(42)  # deterministic demo data
            HISTORY_COUNT = 120
            now = now_utc()
            events_to_insert = []
            for i in range(HISTORY_COUNT):
                days_ago = random.randint(0, 13)
                hours_ago = random.randint(0, 23)
                minutes_ago = random.randint(0, 59)
                ts = now - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
                qty = round(random.uniform(3, 30), 1)
                unit = random.choices(
                    ["servings", "kg", "items", "loaves"],
                    weights=[5, 3, 2, 1],
                )[0]
                meals = qty * MEALS_PER_UNIT.get(unit, 1)
                co2 = qty * (CO2_PER_KG if unit == "kg" else 0.5)
                donor_id = random.choice(donor_ids)
                recipient_id = random.choice(verified_recipient_ids)
                events_to_insert.append({
                    "id": f"seed-history-{i}",
                    "donor_id": donor_id,
                    "recipient_id": recipient_id,
                    "listing_id": f"seed-history-listing-{i}",
                    "request_id": f"seed-history-req-{i}",
                    "quantity": qty,
                    "unit": unit,
                    "meals": meals,
                    "co2_kg": co2,
                    "created_at": iso(ts),
                })
                points = int(round(qty * 10))
                await db.users.update_one({"id": donor_id}, {"$inc": {"points": points}})
                await db.point_transactions.insert_one({
                    "id": f"seed-history-tx-{i}",
                    "user_id": donor_id,
                    "amount": points,
                    "type": "earned",
                    "reason": "Pickup completed: surplus rescue",
                    "created_at": iso(ts),
                })
            if events_to_insert:
                await db.impact_events.insert_many(events_to_insert)
                logger.info("Seeded %d historical impact events", len(events_to_insert))


# ------------------------------ App wiring ----------------------------

app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    try:
        await seed()
    except Exception as e:
        logger.exception("Seeding failed: %s", e)


@app.on_event("shutdown")
async def on_shutdown():
    client.close()
