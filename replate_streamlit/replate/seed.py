"""Seed Hyderabad demo data — donors, recipients, listings, vouchers, history."""
from __future__ import annotations

import os
import uuid
import random
from datetime import datetime, timezone, timedelta

from .db import fetch_one, execute, fetch_all
from .auth import hash_password


ADMIN_EMAIL = os.environ.get("REPLATE_ADMIN_EMAIL", "admin@replate.app")
ADMIN_PASSWORD = os.environ.get("REPLATE_ADMIN_PASSWORD", "Admin123!")

CO2_PER_KG = 2.5
MEALS_PER_UNIT = {"servings": 1, "kg": 2, "items": 0.5, "loaves": 4, "trays": 8}


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


SAMPLE_DONORS = [
    {"email": "niloufer@replate.app", "name": "Rafiq Hussain", "org_name": "Café Niloufer", "org_type": "cafe", "address": "Lakdi-ka-Pul, Hyderabad", "lat": 17.3998, "lng": 78.4730},
    {"email": "karachi@replate.app", "name": "Aarti Khanna", "org_name": "Karachi Bakery", "org_type": "bakery", "address": "Mehdipatnam Rd, Banjara Hills, Hyderabad", "lat": 17.4156, "lng": 78.4351},
    {"email": "paradise@replate.app", "name": "Imran Qureshi", "org_name": "Paradise Restaurant", "org_type": "restaurant", "address": "SD Road, Secunderabad, Hyderabad", "lat": 17.4399, "lng": 78.4983},
    {"email": "chutneys@replate.app", "name": "Lakshmi Reddy", "org_name": "Chutneys", "org_type": "restaurant", "address": "Jubilee Hills, Hyderabad", "lat": 17.4326, "lng": 78.4071},
    {"email": "pistahouse@replate.app", "name": "Mohammed Abdul Majeed", "org_name": "Pista House", "org_type": "bakery", "address": "Shah Ali Banda, Charminar, Hyderabad", "lat": 17.3604, "lng": 78.4736},
    {"email": "bawarchi@replate.app", "name": "Suresh Kothapalli", "org_name": "Bawarchi Restaurant", "org_type": "restaurant", "address": "RTC X Roads, Hyderabad", "lat": 17.4030, "lng": 78.4986},
    {"email": "ohris@replate.app", "name": "Punita Sanghvi", "org_name": "Ohri's Banjara", "org_type": "restaurant", "address": "Road No. 12, Banjara Hills, Hyderabad", "lat": 17.4148, "lng": 78.4319},
    {"email": "almondhouse@replate.app", "name": "Khalid Pasha", "org_name": "Almond House", "org_type": "bakery", "address": "Road No. 36, Jubilee Hills, Hyderabad", "lat": 17.4234, "lng": 78.4070},
    {"email": "concu@replate.app", "name": "Nivedita Sharma", "org_name": "Conçu Patisserie", "org_type": "bakery", "address": "Road No. 1, Banjara Hills, Hyderabad", "lat": 17.4126, "lng": 78.4486},
]

SAMPLE_RECIPIENTS = [
    {"email": "akshaya@replate.app", "name": "Anand Rao", "org_name": "Akshaya Patra Hyderabad", "org_type": "community_kitchen", "address": "Narsingi, Hyderabad", "lat": 17.4239, "lng": 78.4738, "verified": True},
    {"email": "helpinghand@replate.app", "name": "Mujtaba Hasan Askari", "org_name": "Helping Hand Foundation", "org_type": "ngo", "address": "Mehdipatnam, Hyderabad", "lat": 17.4156, "lng": 78.4347, "verified": True},
    {"email": "robinhood@replate.app", "name": "Sanjana Iyer", "org_name": "Robin Hood Army Hyd", "org_type": "ngo", "address": "Gachibowli, Hyderabad", "lat": 17.4400, "lng": 78.3489, "verified": False},
    {"email": "goonj@replate.app", "name": "Vikram Bhargava", "org_name": "Goonj Hyderabad", "org_type": "ngo", "address": "Kondapur, Hyderabad", "lat": 17.4647, "lng": 78.3654, "verified": True},
    {"email": "feedingindia@replate.app", "name": "Ankit Kawatra", "org_name": "Feeding India - Zomato Foundation", "org_type": "food_bank", "address": "Madhapur, Hyderabad", "lat": 17.4483, "lng": 78.3915, "verified": True},
    {"email": "aasara@replate.app", "name": "Padmaja Rao", "org_name": "Aasara Old Age Home", "org_type": "community_kitchen", "address": "Saidabad, Hyderabad", "lat": 17.3645, "lng": 78.5043, "verified": True},
    {"email": "bhumi@replate.app", "name": "Ritika Singhal", "org_name": "Bhumi Hyderabad", "org_type": "ngo", "address": "Begumpet, Hyderabad", "lat": 17.4399, "lng": 78.4634, "verified": True},
]

SAMPLE_LISTINGS = [
    {"donor_email": "niloufer@replate.app", "name": "Irani chai urns & Osmania biscuits", "description": "End-of-evening Irani chai and Osmania biscuits from today's batch.", "category": "bakery", "quantity": 40, "unit": "items", "storage_condition": "ambient", "allergens": "gluten,dairy", "dietary": "vegetarian", "photo_url": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (1, 5), "expiry_hours_from_now": 8},
    {"donor_email": "paradise@replate.app", "name": "Hyderabadi dum biryani — 20 portions", "description": "Surplus chicken & veg dum biryani. Sealed in eco trays, ready to serve.", "category": "prepared_meals", "quantity": 20, "unit": "servings", "storage_condition": "hot", "allergens": "nuts,dairy", "dietary": "halal", "photo_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (0, 2), "expiry_hours_from_now": 4},
    {"donor_email": "karachi@replate.app", "name": "Fruit biscuits, cake slices & rusks", "description": "Surplus bakery items near best-by date.", "category": "bakery", "quantity": 12, "unit": "kg", "storage_condition": "ambient", "allergens": "gluten,dairy,nuts", "dietary": "vegetarian", "photo_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (2, 8), "expiry_hours_from_now": 24},
    {"donor_email": "chutneys@replate.app", "name": "Idli, dosa batter & sambar (large batch)", "description": "Surplus South Indian breakfast prep.", "category": "prepared_meals", "quantity": 30, "unit": "servings", "storage_condition": "refrigerated", "allergens": "", "dietary": "vegetarian,vegan,gluten-free", "photo_url": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (1, 6), "expiry_hours_from_now": 14},
    {"donor_email": "niloufer@replate.app", "name": "Cold milk bottles & samosas", "description": "Unopened buffalo milk + crispy veg samosas.", "category": "beverages", "quantity": 36, "unit": "items", "storage_condition": "refrigerated", "allergens": "dairy,gluten", "dietary": "vegetarian", "photo_url": "https://images.unsplash.com/photo-1601050690597-df0568f70950?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (1, 10), "expiry_hours_from_now": 30},
    {"donor_email": "pistahouse@replate.app", "name": "Haleem trays — Ramadan special", "description": "Slow-cooked mutton haleem. Sealed trays.", "category": "prepared_meals", "quantity": 25, "unit": "servings", "storage_condition": "hot", "allergens": "gluten,dairy", "dietary": "halal", "photo_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (0, 3), "expiry_hours_from_now": 5},
    {"donor_email": "pistahouse@replate.app", "name": "Mawa cakes, fruit cake & dilkush", "description": "Signature bakery items from today's counter.", "category": "bakery", "quantity": 8, "unit": "kg", "storage_condition": "ambient", "allergens": "gluten,dairy,nuts,eggs", "dietary": "vegetarian", "photo_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (1, 8), "expiry_hours_from_now": 20},
    {"donor_email": "bawarchi@replate.app", "name": "Mutton biryani + raita pots (15 portions)", "description": "Bawarchi mutton biryani, served with mirchi salan.", "category": "prepared_meals", "quantity": 15, "unit": "servings", "storage_condition": "hot", "allergens": "dairy,nuts", "dietary": "halal", "photo_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (0, 2), "expiry_hours_from_now": 4},
    {"donor_email": "ohris@replate.app", "name": "Mirchi ka salan, bagara baingan & rotis", "description": "Surplus North Indian gravies + 60 fresh rotis.", "category": "prepared_meals", "quantity": 22, "unit": "servings", "storage_condition": "refrigerated", "allergens": "dairy,nuts,gluten", "dietary": "vegetarian", "photo_url": "https://images.unsplash.com/photo-1668236543090-82eba5ee5976?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (1, 6), "expiry_hours_from_now": 18},
    {"donor_email": "almondhouse@replate.app", "name": "Badam halwa, dry-fruit laddoos & kaju katli", "description": "Surplus mithai trays. Sealed boxes.", "category": "other", "quantity": 6, "unit": "kg", "storage_condition": "ambient", "allergens": "nuts,dairy", "dietary": "vegetarian,gluten-free", "photo_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (2, 12), "expiry_hours_from_now": 48},
    {"donor_email": "concu@replate.app", "name": "French pastries, croissants & quiche", "description": "End-of-day patisserie surplus.", "category": "bakery", "quantity": 32, "unit": "items", "storage_condition": "refrigerated", "allergens": "gluten,dairy,eggs,nuts", "dietary": "vegetarian", "photo_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (0, 4), "expiry_hours_from_now": 12},
    {"donor_email": "karachi@replate.app", "name": "Plum cake, dundee cake & banana bread", "description": "Surplus tea-time loaves.", "category": "bakery", "quantity": 18, "unit": "loaves", "storage_condition": "ambient", "allergens": "gluten,dairy,eggs,nuts", "dietary": "vegetarian", "photo_url": "https://images.unsplash.com/photo-1565557623262-b51c2513a641?auto=format&fit=crop&q=80&w=1000", "pickup_hours_from_now": (3, 10), "expiry_hours_from_now": 36},
]

SAMPLE_VOUCHERS = [
    {"id": "v-coffee-1", "partner": "Café Niloufer", "title": "Free Irani chai + Osmania biscuit", "description": "Redeemable at any Café Niloufer outlet.", "points_cost": 80, "image_url": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-grocery-1", "partner": "Heirloom Grocers", "title": "₹200 Grocery Voucher", "description": "Towards any seasonal produce.", "points_cost": 250, "image_url": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-bakery-1", "partner": "Karachi Bakery", "title": "Free pastry of the day", "description": "Pick any pastry from the morning case.", "points_cost": 60, "image_url": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-meal-1", "partner": "Paradise Restaurant", "title": "Two-portion biryani lunch", "description": "Signature Hyderabadi dum biryani lunch for two.", "points_cost": 500, "image_url": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-tote-1", "partner": "RePlate", "title": "Canvas Tote Bag", "description": "Made from organic, undyed cotton.", "points_cost": 150, "image_url": "https://images.unsplash.com/photo-1593113565687-cc2f464d1f2e?auto=format&fit=crop&q=80&w=800"},
    {"id": "v-tree-1", "partner": "One Tree Planted", "title": "Plant 5 trees", "description": "Donate points to fund tree planting.", "points_cost": 300, "image_url": "https://images.unsplash.com/photo-1466692476868-aef1dfb1e735?auto=format&fit=crop&q=80&w=800"},
]


def _upsert_user(u: dict, role: str, password: str = "Demo123!") -> str:
    existing = fetch_one("SELECT id FROM users WHERE email = ?", [u["email"]])
    if existing:
        return existing["id"]
    user_id = str(uuid.uuid4())
    execute(
        """INSERT INTO users (id, email, password_hash, name, role, org_name, org_type,
                              phone, address, lat, lng, verified, points, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        [
            user_id, u["email"], hash_password(password), u["name"], role,
            u["org_name"], u["org_type"], "+91 91234 56789",
            u["address"], u["lat"], u["lng"],
            1 if (role == "donor" or u.get("verified")) else 0,
            0, iso(now_utc()),
        ],
    )
    return user_id


def seed_all() -> None:
    """Idempotent. Safe to call on every run."""
    # Admin
    if not fetch_one("SELECT id FROM users WHERE email = ?", [ADMIN_EMAIL]):
        execute(
            """INSERT INTO users (id, email, password_hash, name, role, verified, points, created_at)
               VALUES (?,?,?,?,?,?,?,?)""",
            [str(uuid.uuid4()), ADMIN_EMAIL, hash_password(ADMIN_PASSWORD),
             "Platform Admin", "admin", 1, 0, iso(now_utc())],
        )

    donor_map: dict[str, str] = {}
    for d in SAMPLE_DONORS:
        donor_map[d["email"]] = _upsert_user(d, "donor")
    for r in SAMPLE_RECIPIENTS:
        _upsert_user(r, "recipient")

    # Vouchers
    for v in SAMPLE_VOUCHERS:
        execute(
            """INSERT OR REPLACE INTO vouchers (id, partner, title, description, points_cost, image_url)
               VALUES (?,?,?,?,?,?)""",
            [v["id"], v["partner"], v["title"], v["description"], v["points_cost"], v["image_url"]],
        )

    # Listings — deterministic IDs (refresh photos/timestamps each run, preserve any with requests)
    now = now_utc()
    for s in SAMPLE_LISTINGS:
        donor_id = donor_map.get(s["donor_email"])
        if not donor_id:
            continue
        donor = fetch_one("SELECT * FROM users WHERE id = ?", [donor_id])
        det_id = "seed-" + s["donor_email"].split("@")[0] + "-" + s["name"][:30].lower().replace(" ", "-").replace(",", "")
        has_activity = fetch_one("SELECT id FROM requests WHERE listing_id = ?", [det_id])
        if has_activity:
            continue
        existing = fetch_one("SELECT pickup_pin, created_at FROM listings WHERE id = ?", [det_id])
        ps, pe = s["pickup_hours_from_now"]
        params = [
            det_id, donor_id, donor["org_name"], donor["org_type"], s["name"], s["description"],
            s["category"], s["quantity"], s["quantity"], s["unit"], s["storage_condition"],
            s["allergens"], s["dietary"], s["photo_url"], donor["address"], donor["lat"], donor["lng"],
            iso(now + timedelta(hours=ps)), iso(now + timedelta(hours=pe)),
            iso(now + timedelta(hours=s["expiry_hours_from_now"])),
            "active",
            (existing["pickup_pin"] if existing else str(uuid.uuid4().int)[:4]),
            (existing["created_at"] if existing else iso(now)),
        ]
        execute(
            """INSERT OR REPLACE INTO listings
               (id, donor_id, donor_name, donor_org_type, name, description, category,
                quantity, remaining_quantity, unit, storage_condition, allergens, dietary,
                photo_url, pickup_address, lat, lng, pickup_start, pickup_end, expiry_time,
                status, pickup_pin, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            params,
        )

    # Historical impact events (idempotent — checks for seed-history-*)
    if not fetch_one("SELECT id FROM impact_events WHERE id LIKE 'seed-history-%' LIMIT 1"):
        verified_recipients = fetch_all("SELECT id FROM users WHERE role = 'recipient' AND verified = 1")
        donor_ids = list(donor_map.values())
        recipient_ids = [r["id"] for r in verified_recipients]
        if donor_ids and recipient_ids:
            random.seed(42)
            for i in range(120):
                days_ago = random.randint(0, 13)
                hours_ago = random.randint(0, 23)
                ts = now - timedelta(days=days_ago, hours=hours_ago, minutes=random.randint(0, 59))
                qty = round(random.uniform(3, 30), 1)
                unit = random.choices(["servings", "kg", "items", "loaves"], weights=[5, 3, 2, 1])[0]
                meals = qty * MEALS_PER_UNIT.get(unit, 1)
                co2 = qty * (CO2_PER_KG if unit == "kg" else 0.5)
                donor_id = random.choice(donor_ids)
                recipient_id = random.choice(recipient_ids)
                execute(
                    """INSERT INTO impact_events
                       (id, donor_id, recipient_id, listing_id, request_id, quantity, unit, meals, co2_kg, created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    [f"seed-history-{i}", donor_id, recipient_id, f"seed-history-listing-{i}",
                     f"seed-history-req-{i}", qty, unit, meals, co2, iso(ts)],
                )
                points = int(round(qty * 10))
                execute("UPDATE users SET points = points + ? WHERE id = ?", [points, donor_id])
                execute(
                    """INSERT INTO point_transactions
                       (id, user_id, amount, type, reason, created_at) VALUES (?,?,?,?,?,?)""",
                    [f"seed-history-tx-{i}", donor_id, points, "earned",
                     "Pickup completed: surplus rescue", iso(ts)],
                )
