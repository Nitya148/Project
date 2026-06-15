"""Listing detail — shows full listing + request action + mini map."""
import streamlit as st

from replate.auth import require_login
from replate.services import get_listing, create_request
from replate.utils import inject_style, time_until, overline, logo_header, fmt_qty
from replate.maps import render_map

st.set_page_config(page_title="Listing · RePlate", page_icon="🍞", layout="wide")
inject_style()
user = require_login()

with st.sidebar:
    logo_header()

listing_id = st.session_state.get("selected_listing")
if not listing_id:
    st.warning("No listing selected.")
    st.page_link("pages/1_Discover.py", label="← Back to Discover")
    st.stop()

l = get_listing(listing_id)
if not l:
    st.error("Listing not found.")
    st.stop()

is_owner = l["donor_id"] == user["id"]
label, mins = time_until(l["expiry_time"])
urgent = mins <= 240

if st.button("← Back", type="secondary"):
    st.switch_page("pages/1_Discover.py")

left, right = st.columns([3, 2])

with left:
    st.image(l.get("photo_url") or "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=1000", use_container_width=True)
    if l.get("lat") is not None:
        overline("Pickup location")
        origin = {"lat": user.get("lat"), "lng": user.get("lng"), "label": user.get("org_name", "You")} if user.get("lat") else None
        render_map([l], origin=origin, height=320, key="detail-map")

with right:
    overline(l["donor_name"] or "")
    st.markdown(f"## {l['name']}")
    st.markdown(
        f"""
        <div style="display:flex;flex-direction:column;gap:8px;font-size:14px;color:#2A1B24;margin-top:14px;">
            <div>📦 <strong>{fmt_qty(l['remaining_quantity'])}</strong> / {fmt_qty(l['quantity'])} {l['unit']} available</div>
            <div>🧊 Storage: {l['storage_condition']}</div>
            <div>⏱ Pickup: {l['pickup_start'][:16].replace('T',' ')} → {l['pickup_end'][:16].replace('T',' ')}</div>
            <div style="color:{'#D97D3A' if urgent else '#695A62'};font-weight:600;">⏳ Expires in {label}</div>
            <div>📍 {l.get('pickup_address','—')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if l.get("allergens"):
        overline("Allergens")
        st.markdown(" ".join(
            f'<span class="badge badge-urgent" style="margin-right:6px;">{a}</span>'
            for a in l["allergens"].split(",") if a
        ), unsafe_allow_html=True)
    if l.get("dietary"):
        overline("Dietary")
        st.markdown(" ".join(
            f'<span class="badge badge-success" style="margin-right:6px;">{a}</span>'
            for a in l["dietary"].split(",") if a
        ), unsafe_allow_html=True)
    if l.get("description"):
        overline("Notes")
        st.write(l["description"])

    st.markdown("---")

    if is_owner:
        st.markdown("##### Pickup PIN (give to recipient)")
        st.markdown(f'<div class="pin">{l["pickup_pin"]}</div>', unsafe_allow_html=True)
    elif user["role"] == "recipient" and l["status"] == "active":
        if not user.get("verified"):
            st.error("Your organization is pending verification — claiming is locked.")
        else:
            with st.form("req_form"):
                st.markdown("##### Request this listing")
                qty = st.number_input(
                    f"Quantity ({l['unit']})",
                    min_value=0.1,
                    max_value=float(l["remaining_quantity"]),
                    value=min(1.0, float(l["remaining_quantity"])),
                    step=0.5,
                )
                note = st.text_area("Note (optional)", placeholder="ETA, vehicle, anything helpful…")
                if st.form_submit_button("Send request", type="primary", use_container_width=True):
                    ok, msg = create_request(user, l["id"], qty, note)
                    if ok:
                        st.success("Request sent — donor will review shortly.")
                        st.switch_page("pages/3_Requests.py")
                    else:
                        st.error(msg)
    else:
        st.info(f"Status: {l['status']}")
