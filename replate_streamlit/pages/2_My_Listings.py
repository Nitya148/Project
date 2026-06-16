"""My Listings — donor view to manage own listings + create new."""
from datetime import datetime, timedelta, timezone

import streamlit as st

from replate.auth import require_role
from replate.services import list_by_donor, create_listing, cancel_listing
from replate.utils import inject_style, time_until, overline, logo_header, fmt_qty

st.set_page_config(page_title="My Listings · RePlate", page_icon="📦", layout="wide")
inject_style()
user = require_role(["donor"])

with st.sidebar:
    logo_header()

overline("Your kitchen")
st.title("Your listings")

CATEGORY_PHOTOS = {
    "produce": "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=1000",
    "bakery": "https://images.unsplash.com/photo-1499636136210-6f4ee915583e?auto=format&fit=crop&q=80&w=1000",
    "prepared_meals": "https://images.unsplash.com/photo-1633945274405-b6c8069047b0?auto=format&fit=crop&q=80&w=1000",
    "dairy": "https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&q=80&w=1000",
    "pantry": "https://images.unsplash.com/photo-1589302168068-964664d93dc0?auto=format&fit=crop&q=80&w=1000",
    "beverages": "https://images.unsplash.com/photo-1571934811356-5cc061b6821f?auto=format&fit=crop&q=80&w=1000",
    "other": "https://images.unsplash.com/photo-1593113565687-cc2f464d1f2e?auto=format&fit=crop&q=80&w=1000",
}

tabs = st.tabs(["Active", "Completed", "Expired", "Cancelled", "Create new"])
TAB_STATUS = ["active", "completed", "expired", "cancelled"]

for idx, status in enumerate(TAB_STATUS):
    items = list_by_donor(user["id"], status)
    with tabs[idx]:
        if not items:
            st.info(f"No {status} listings.")
            continue
        cols = st.columns(3)
        for i, l in enumerate(items):
            with cols[i % 3]:
                label, mins = time_until(l["expiry_time"]) if status == "active" else ("—", 0)
                st.markdown(
                    f"""<div class="listing-card">
                        <img src="{l.get('photo_url','')}" alt=""/>
                        <div class="info">
                            <div class="donor">{l['category'].replace('_',' ')} · {status}</div>
                            <div class="title">{l['name']}</div>
                            <div class="meta">
                                <span><strong>{fmt_qty(l['remaining_quantity'])}</strong>/{fmt_qty(l['quantity'])} {l['unit']}</span>
                                <span>{label}</span>
                            </div>
                            <div style="margin-top:8px;font-size:11px;color:#695A62;letter-spacing:0.1em;">
                                PICKUP PIN · <span style="color:#C85A40;font-weight:700;letter-spacing:0.4em;">{l['pickup_pin']}</span>
                            </div>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if status == "active":
                    if st.button("Cancel listing", key=f"cancel_{l['id']}", type="secondary"):
                        cancel_listing(l["id"])
                        st.rerun()

# Create new tab
with tabs[4]:
    st.markdown("##### List today's surplus")
    with st.form("new_listing"):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input("What are you offering?", placeholder="e.g. Surplus Hyderabadi biryani — 10 portions")
            category = st.selectbox(
                "Category",
                list(CATEGORY_PHOTOS.keys()),
                format_func=lambda x: x.replace("_", " ").title(),
            )
            qty = st.number_input("Quantity", min_value=0.1, value=5.0, step=0.5)
            unit = st.selectbox("Unit", ["servings", "kg", "items", "loaves", "trays"])
            storage = st.selectbox("Storage condition", ["ambient", "refrigerated", "frozen", "hot"])
        with c2:
            description = st.text_area("Description (optional)", height=120)
            allergens = st.multiselect("Allergens", ["gluten", "dairy", "nuts", "eggs", "soy", "shellfish"])
            dietary = st.multiselect("Dietary tags", ["vegetarian", "vegan", "gluten-free", "halal", "kosher"])
            address = st.text_input("Pickup address", value=user.get("address") or "")
            photo = st.text_input("Photo URL (auto-suggested)", value=CATEGORY_PHOTOS[category])
            st.markdown("##### Pickup window & expiry")

        c3, c4, c5 = st.columns(3)
        now = datetime.now(timezone.utc)

        with c3:
            pickup_start_date = st.date_input(
                "Pickup starts (date)",
                value=now.date()
            )
            pickup_start_time = st.time_input(
                "Pickup starts (time)",
                value=(now + timedelta(hours=1)).time(),
                step=900
            )

        with c4:
            pickup_end_date = st.date_input(
                "Pickup ends (date)",
                value=now.date()
            )
            pickup_end_time = st.time_input(
                "Pickup ends (time)",
                value=(now + timedelta(hours=4)).time(),
                step=900
            )

        with c5:
            expiry_date = st.date_input(
                "Expires on (date)",
                value=now.date()
            )
            expiry_time = st.time_input(
                "Expires on (time)",
                value=(now + timedelta(hours=8)).time(),
                step=900
            )

        safety = st.checkbox(
            "I confirm this food is safe for consumption, handled per standard food-safety guidelines, and labeled with relevant allergens.",
            value=True,
        )

        submitted = st.form_submit_button(
            "Publish listing",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            if not (name and address and safety):
                st.error("Please fill the name, pickup address, and confirm safety.")
            else:
                try:
                    listing_id = create_listing(user, {
                        "name": name,
                        "description": description,
                        "category": category,
                        "quantity": qty,
                        "unit": unit,
                        "storage_condition": storage,
                        "allergens": allergens,
                        "dietary": dietary,
                        "photo_url": photo,
                        "pickup_address": address,
                        "pickup_start": datetime.combine(pickup_start_date, pickup_start_time, tzinfo=timezone.utc),
                        "pickup_end": datetime.combine(pickup_end_date, pickup_end_time, tzinfo=timezone.utc),
                        "expiry_time": datetime.combine(expiry_date, expiry_time, tzinfo=timezone.utc),
                    })
                    st.success("Listing published — recipients will see it now.")
                    st.session_state["selected_listing"] = listing_id
                    st.switch_page("pages/4_Listing.py")
                except Exception as e:
                    st.error(f"Could not publish: {e}")
