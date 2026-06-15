"""Discover — browse nearby surplus (recipients & all users)."""
import streamlit as st

from replate.auth import require_login
from replate.services import discover, get_listing, create_request
from replate.utils import inject_style, time_until, overline, logo_header, fmt_qty
from replate.maps import render_map

st.set_page_config(page_title="Discover · RePlate", page_icon="🧭", layout="wide")
inject_style()
user = require_login()

with st.sidebar:
    logo_header()

overline("Discover")
st.title("Surplus near you")
st.caption("Real-time listings sorted by distance and urgency.")

# Filters
col1, col2, col3 = st.columns([2, 2, 2])
with col1:
    category = st.selectbox(
        "Category",
        ["", "produce", "bakery", "prepared_meals", "dairy", "pantry", "beverages", "other"],
        format_func=lambda x: "All categories" if x == "" else x.replace("_", " ").title(),
    )
with col2:
    radius = st.slider("Radius (km)", 1, 200, 100)
with col3:
    view = st.radio("View", ["List", "Map"], horizontal=True, label_visibility="collapsed")

items = discover(user, radius_km=radius, category=category or None)

if not user.get("verified") and user["role"] == "recipient":
    st.warning("Your organization is pending admin verification — you can browse, but claiming is locked.")

st.markdown(f"**{len(items)}** listings available")

if not items:
    st.info("Nothing nearby right now. Try expanding the radius.")
    st.stop()

if view == "Map":
    origin = {"lat": user.get("lat"), "lng": user.get("lng"), "label": user.get("org_name", "You")}
    map_col, list_col = st.columns([3, 2])
    with map_col:
        render_map(items, origin=origin, height=560, key="discover-map")
    with list_col:
        for idx, l in enumerate(items, 1):
            label, mins = time_until(l["expiry_time"])
            urgent = mins <= 240
            with st.container():
                st.markdown(
                    f"""<div style="background:white;border:1px solid rgba(42,27,36,0.08);
                                    border-radius:14px;padding:12px 14px;margin-bottom:10px;">
                    <div style="display:flex;align-items:center;gap:10px;">
                        <div style="background:#C85A40;color:white;font-weight:700;font-size:11px;
                                    width:24px;height:24px;border-radius:999px;display:flex;
                                    align-items:center;justify-content:center;">{idx}</div>
                        <div>
                            <div style="font-size:10px;text-transform:uppercase;letter-spacing:0.18em;color:#695A62;">{l['donor_name']}</div>
                            <div style="font-family:'Cormorant Garamond',serif;font-size:17px;line-height:1.2;">{l['name']}</div>
                        </div>
                    </div>
                    <div style="display:flex;justify-content:space-between;margin-top:8px;font-size:12px;color:#695A62;">
                        <span>{fmt_qty(l['remaining_quantity'])} {l['unit']}</span>
                        <span style="color:{'#D97D3A' if urgent else '#695A62'};font-weight:600;">
                            {l.get('distance_km','—')} km · {label}
                        </span>
                    </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if st.button(f"View →", key=f"map_open_{l['id']}", use_container_width=True):
                    st.session_state["selected_listing"] = l["id"]
                    st.switch_page("pages/4_Listing.py")
else:
    cols = st.columns(3)
    for i, l in enumerate(items):
        with cols[i % 3]:
            label, mins = time_until(l["expiry_time"])
            urgent = mins <= 240
            urg_badge = '<span class="badge badge-urgent">Expires soon</span>' if urgent else ""
            st.markdown(
                f"""<div class="listing-card">
                    <img src="{l.get('photo_url','')}" alt=""/>
                    <div style="position:relative;">
                        <div style="position:absolute;top:-44px;left:14px;display:flex;gap:6px;">
                            <span class="badge badge-bakery">{l['category'].replace('_',' ')}</span>
                            {urg_badge}
                        </div>
                    </div>
                    <div class="info">
                        <div class="donor">{l['donor_name']}</div>
                        <div class="title">{l['name']}</div>
                        <div class="meta">
                            <span><strong>{fmt_qty(l['remaining_quantity'])}</strong> {l['unit']}</span>
                            <span class="{'urgent' if urgent else ''}">
                                {f"{l.get('distance_km')} km · " if l.get('distance_km') is not None else ""}{label}
                            </span>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button("Open listing", key=f"open_{l['id']}", use_container_width=True):
                st.session_state["selected_listing"] = l["id"]
                st.switch_page("pages/4_Listing.py")
