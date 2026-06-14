"""
Backend tests for Food Waste Exchange platform.
Covers: auth, listings, requests flow, rewards, admin, impact, leaderboard.
"""
import os
import time
import uuid
import requests
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Load frontend env to grab public URL
load_dotenv(Path("/app/frontend/.env"))
BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

# --- Credentials (seeded) ---
ADMIN = ("admin@foodxchange.app", "Admin123!")
DONOR_LUMA = ("luma@cafeluma.app", "Demo123!")
DONOR_FOLK = ("folk@folkflour.app", "Demo123!")
RECIP_HARBOR = ("harbor@harborkitchen.app", "Demo123!")
RECIP_SHELTER = ("shelter@kindshelter.app", "Demo123!")


def login(email, password):
    r = requests.post(f"{API}/auth/login", json={"email": email, "password": password}, timeout=15)
    assert r.status_code == 200, f"Login failed for {email}: {r.status_code} {r.text}"
    data = r.json()
    assert "token" in data and "user" in data
    return data


def auth_headers(token):
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module", autouse=True)
def reset_shelter_unverified():
    """Ensure the seeded unverified recipient starts unverified before the suite."""
    try:
        a = login(*ADMIN)
        s = login(*RECIP_SHELTER)
        requests.post(f"{API}/admin/unverify/{s['user']['id']}", headers=auth_headers(a["token"]))
    except Exception:
        pass
    yield


# ============================== AUTH ==============================

class TestAuth:
    def test_login_admin(self):
        d = login(*ADMIN)
        assert d["user"]["role"] == "admin"
        assert d["user"]["email"] == ADMIN[0]

    def test_login_donor(self):
        d = login(*DONOR_LUMA)
        assert d["user"]["role"] == "donor"
        assert d["user"]["org_name"] == "Café Luma"
        assert d["user"]["verified"] is True

    def test_login_recipient_verified(self):
        d = login(*RECIP_HARBOR)
        assert d["user"]["role"] == "recipient"
        assert d["user"]["verified"] is True

    def test_login_recipient_unverified(self):
        d = login(*RECIP_SHELTER)
        assert d["user"]["verified"] is False

    def test_login_invalid(self):
        r = requests.post(f"{API}/auth/login", json={"email": "nope@nope.app", "password": "wrong"})
        assert r.status_code == 401

    def test_me_with_bearer(self):
        d = login(*DONOR_LUMA)
        r = requests.get(f"{API}/auth/me", headers=auth_headers(d["token"]))
        assert r.status_code == 200
        assert r.json()["email"] == DONOR_LUMA[0]

    def test_me_no_token(self):
        r = requests.get(f"{API}/auth/me")
        assert r.status_code == 401

    def test_register_donor_default_verified(self):
        email = f"test_donor_{uuid.uuid4().hex[:8]}@test.app"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "Test123!", "name": "T Donor",
            "role": "donor", "org_name": "Test Donor Org", "org_type": "cafe"
        })
        assert r.status_code == 200, r.text
        data = r.json()
        assert "token" in data
        assert data["user"]["verified"] is True
        assert data["user"]["role"] == "donor"

    def test_register_recipient_default_unverified(self):
        email = f"test_recip_{uuid.uuid4().hex[:8]}@test.app"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "Test123!", "name": "T Recip",
            "role": "recipient", "org_name": "Test Recip", "org_type": "ngo"
        })
        assert r.status_code == 200, r.text
        assert r.json()["user"]["verified"] is False


# ============================== LISTINGS ==============================

class TestListings:
    def test_discover_as_recipient(self):
        d = login(*RECIP_HARBOR)
        r = requests.get(f"{API}/listings/discover", headers=auth_headers(d["token"]))
        assert r.status_code == 200
        listings = r.json()
        assert isinstance(listings, list)
        assert len(listings) >= 1, "Expected seeded active listings"
        # pickup_pin must be hidden
        for it in listings:
            assert it["pickup_pin"] is None, "pickup_pin should be hidden in discover"
            assert "distance_km" in it

    def test_get_listing_pin_hidden_for_unrelated_recipient(self):
        d = login(*RECIP_HARBOR)
        listings = requests.get(f"{API}/listings/discover", headers=auth_headers(d["token"])).json()
        lid = listings[0]["id"]
        r = requests.get(f"{API}/listings/{lid}", headers=auth_headers(d["token"]))
        assert r.status_code == 200
        assert r.json()["pickup_pin"] is None

    def test_get_listing_pin_visible_to_donor(self):
        d = login(*DONOR_LUMA)
        mine = requests.get(f"{API}/listings?mine=true", headers=auth_headers(d["token"])).json()
        assert len(mine) >= 1
        lid = mine[0]["id"]
        r = requests.get(f"{API}/listings/{lid}", headers=auth_headers(d["token"]))
        assert r.status_code == 200
        assert r.json()["pickup_pin"] is not None
        assert len(r.json()["pickup_pin"]) == 4

    def test_discover_category_filter(self):
        d = login(*RECIP_HARBOR)
        r = requests.get(f"{API}/listings/discover?category=bakery", headers=auth_headers(d["token"]))
        assert r.status_code == 200
        for it in r.json():
            assert it["category"] == "bakery"

    def test_discover_radius_filter(self):
        d = login(*RECIP_HARBOR)
        r = requests.get(f"{API}/listings/discover?radius_km=0.001", headers=auth_headers(d["token"]))
        assert r.status_code == 200
        # extremely tight radius should drop seeded listings
        assert len(r.json()) == 0


# ========================= FULL HAPPY PATH =========================

class TestHappyPath:
    """End-to-end: donor creates listing -> recipient requests -> approve -> confirm -> points."""

    def test_full_flow(self):
        # 1. Donor creates listing
        donor = login(*DONOR_LUMA)
        donor_token = donor["token"]
        donor_id_before = donor["user"]["id"]
        points_before = donor["user"]["points"]

        now = datetime.now(timezone.utc)
        listing_payload = {
            "name": "TEST_E2E_loaves",
            "description": "End-to-end test loaves",
            "category": "bakery",
            "quantity": 7,
            "unit": "kg",
            "storage_condition": "ambient",
            "allergens": [],
            "dietary": [],
            "pickup_address": "Test Lane, Brooklyn",
            "lat": 40.7081, "lng": -73.9571,
            "pickup_start": (now + timedelta(hours=1)).isoformat(),
            "pickup_end": (now + timedelta(hours=5)).isoformat(),
            "expiry_time": (now + timedelta(hours=8)).isoformat(),
            "safety_acknowledged": True,
        }
        r = requests.post(f"{API}/listings", json=listing_payload, headers=auth_headers(donor_token))
        assert r.status_code == 200, r.text
        listing = r.json()
        listing_id = listing["id"]
        pin = listing["pickup_pin"]
        assert pin and len(pin) == 4

        # 2. Recipient discovers
        recip = login(*RECIP_HARBOR)
        rtok = recip["token"]
        disc = requests.get(f"{API}/listings/discover", headers=auth_headers(rtok)).json()
        ids = [x["id"] for x in disc]
        assert listing_id in ids

        # Request the listing
        r = requests.post(f"{API}/requests",
                          json={"listing_id": listing_id, "requested_quantity": 7, "note": "test"},
                          headers=auth_headers(rtok))
        assert r.status_code == 200, r.text
        req = r.json()
        req_id = req["id"]
        assert req["status"] == "pending"

        # 3. Donor sees incoming
        incoming = requests.get(f"{API}/requests?role=incoming", headers=auth_headers(donor_token)).json()
        assert any(x["id"] == req_id for x in incoming)

        # Approve
        r = requests.post(f"{API}/requests/{req_id}/approve", headers=auth_headers(donor_token))
        assert r.status_code == 200, r.text

        # 4. Recipient sees outgoing, can now see pin
        outgoing = requests.get(f"{API}/requests?role=outgoing", headers=auth_headers(rtok)).json()
        assert any(x["id"] == req_id and x["status"] == "approved" for x in outgoing)

        det = requests.get(f"{API}/listings/{listing_id}", headers=auth_headers(rtok)).json()
        assert det["pickup_pin"] == pin

        # 5. Recipient confirms with PIN
        r = requests.post(f"{API}/requests/{req_id}/confirm",
                          json={"pin": pin}, headers=auth_headers(rtok))
        assert r.status_code == 200, r.text
        result = r.json()
        assert result["points_awarded"] == 70  # 7 kg * 10
        assert result["meals"] > 0
        assert result["co2_kg"] > 0

        # 6. Donor's points updated; impact recorded
        me = requests.get(f"{API}/auth/me", headers=auth_headers(donor_token)).json()
        assert me["points"] == points_before + 70

        impact = requests.get(f"{API}/impact/me", headers=auth_headers(donor_token)).json()
        assert impact["total_pickups"] >= 1

        # Wrong PIN rejection (sanity: cannot reconfirm anyway)
        r = requests.post(f"{API}/requests/{req_id}/confirm",
                          json={"pin": "9999"}, headers=auth_headers(rtok))
        assert r.status_code == 400


# ========================== AUTHORIZATION ==========================

class TestAuthorization:
    def test_unverified_recipient_cannot_request(self):
        d = login(*RECIP_SHELTER)
        # Get any active listing
        h = login(*RECIP_HARBOR)
        disc = requests.get(f"{API}/listings/discover", headers=auth_headers(h["token"])).json()
        assert len(disc) > 0
        lid = disc[0]["id"]
        r = requests.post(f"{API}/requests",
                          json={"listing_id": lid, "requested_quantity": 1},
                          headers=auth_headers(d["token"]))
        assert r.status_code == 403

    def test_donor_cannot_access_admin(self):
        d = login(*DONOR_LUMA)
        for path in ["/admin/pending-recipients", "/admin/recipients", "/admin/stats"]:
            r = requests.get(f"{API}{path}", headers=auth_headers(d["token"]))
            assert r.status_code == 403, f"{path} expected 403 got {r.status_code}"


# ============================ REWARDS ============================

class TestRewards:
    def test_list_vouchers(self):
        r = requests.get(f"{API}/vouchers")
        assert r.status_code == 200
        items = r.json()
        assert len(items) == 6
        # sorted by points_cost ascending
        costs = [v["points_cost"] for v in items]
        assert costs == sorted(costs)

    def test_redeem_cheapest_voucher_as_donor(self):
        # Luma should have points from happy-path test. Top up by running another pickup if needed.
        d = login(*DONOR_LUMA)
        token = d["token"]
        me = requests.get(f"{API}/auth/me", headers=auth_headers(token)).json()
        if me["points"] < 60:
            pytest.skip(f"Donor has only {me['points']} pts; need >=60. Happy-path may not have run.")

        vouchers = requests.get(f"{API}/vouchers").json()
        cheapest = vouchers[0]
        assert cheapest["points_cost"] == 60

        before = me["points"]
        r = requests.post(f"{API}/vouchers/redeem",
                          json={"voucher_id": cheapest["id"]},
                          headers=auth_headers(token))
        assert r.status_code == 200, r.text
        red = r.json()
        assert red["code"].startswith("FX-")
        assert red["points_cost"] == 60

        after = requests.get(f"{API}/auth/me", headers=auth_headers(token)).json()["points"]
        assert after == before - 60

    def test_redeem_insufficient_points(self):
        # New donor with 0 points
        email = f"test_poor_{uuid.uuid4().hex[:8]}@test.app"
        r = requests.post(f"{API}/auth/register", json={
            "email": email, "password": "Test123!", "name": "P", "role": "donor",
            "org_name": "Poor", "org_type": "cafe"
        })
        tok = r.json()["token"]
        vouchers = requests.get(f"{API}/vouchers").json()
        r = requests.post(f"{API}/vouchers/redeem",
                          json={"voucher_id": vouchers[0]["id"]},
                          headers=auth_headers(tok))
        assert r.status_code == 400


# ============================== ADMIN ==============================

class TestAdmin:
    def test_admin_pending_recipients_lists_shelter(self):
        a = login(*ADMIN)
        # Ensure shelter is unverified to make test deterministic
        s = login(*RECIP_SHELTER)
        requests.post(f"{API}/admin/unverify/{s['user']['id']}", headers=auth_headers(a["token"]))
        r = requests.get(f"{API}/admin/pending-recipients", headers=auth_headers(a["token"]))
        assert r.status_code == 200
        emails = [u["email"] for u in r.json()]
        assert RECIP_SHELTER[0] in emails

    def test_admin_verify_and_then_request_works(self):
        # Find shelter user id
        a = login(*ADMIN)
        atok = a["token"]
        pending = requests.get(f"{API}/admin/pending-recipients", headers=auth_headers(atok)).json()
        shelter = next((u for u in pending if u["email"] == RECIP_SHELTER[0]), None)
        if not shelter:
            # already verified by a previous run
            pytest.skip("Shelter already verified")
        sid = shelter["id"]

        r = requests.post(f"{API}/admin/verify/{sid}", headers=auth_headers(atok))
        assert r.status_code == 200

        # Now shelter should be able to POST request
        s = login(*RECIP_SHELTER)
        assert s["user"]["verified"] is True
        disc = requests.get(f"{API}/listings/discover", headers=auth_headers(s["token"])).json()
        if not disc:
            pytest.skip("No active listings to claim")
        # Skip listings shelter already has pending requests for
        outgoing = requests.get(f"{API}/requests?role=outgoing", headers=auth_headers(s["token"])).json()
        already = {x["listing_id"] for x in outgoing if x["status"] == "pending"}
        target = next((x for x in disc if x["id"] not in already), None)
        if not target:
            pytest.skip("Shelter already has pending requests on all listings")
        r = requests.post(f"{API}/requests",
                          json={"listing_id": target["id"], "requested_quantity": 1},
                          headers=auth_headers(s["token"]))
        assert r.status_code == 200, r.text

        # Cleanup: unverify shelter back so test is repeatable
        requests.post(f"{API}/admin/unverify/{sid}", headers=auth_headers(atok))

    def test_admin_stats(self):
        a = login(*ADMIN)
        r = requests.get(f"{API}/admin/stats", headers=auth_headers(a["token"]))
        assert r.status_code == 200
        s = r.json()
        for key in ["users", "donors", "recipients", "active_listings"]:
            assert key in s
            assert isinstance(s[key], int)


# ========================= IMPACT & LEADERBOARD ====================

class TestImpactLeaderboard:
    def test_impact_global_shape(self):
        r = requests.get(f"{API}/impact/global")
        assert r.status_code == 200
        d = r.json()
        for k in ["total_pickups", "total_kg", "total_meals", "total_co2_kg", "by_day"]:
            assert k in d

    def test_impact_me_donor(self):
        d = login(*DONOR_LUMA)
        r = requests.get(f"{API}/impact/me", headers=auth_headers(d["token"]))
        assert r.status_code == 200
        assert "total_pickups" in r.json()

    def test_leaderboard(self):
        r = requests.get(f"{API}/leaderboard")
        assert r.status_code == 200
        lb = r.json()
        assert isinstance(lb, list)
        if lb:
            assert "points" in lb[0]
            # sorted desc
            pts = [u["points"] for u in lb]
            assert pts == sorted(pts, reverse=True)
