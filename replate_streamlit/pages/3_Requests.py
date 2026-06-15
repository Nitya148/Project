"""Requests — both incoming (donor) and outgoing (recipient)."""
import streamlit as st

from replate.auth import require_login, refresh_user
from replate.services import requests_for, approve_request, reject_request, confirm_pickup, get_listing
from replate.utils import inject_style, overline, logo_header

st.set_page_config(page_title="Requests · RePlate", page_icon="📨", layout="wide")
inject_style()
user = require_login()

with st.sidebar:
    logo_header()

overline("Requests")
st.title("Pickup requests" if user["role"] == "donor" else "Your claims")

if user["role"] == "donor":
    tabs = st.tabs(["Incoming", "Outgoing (yours)"])
    roles = ["incoming", "outgoing"]
else:
    tabs = st.tabs(["My claims"])
    roles = ["outgoing"]

STATUS_COLORS = {
    "pending": "#D97D3A",
    "approved": "#6B705C",
    "completed": "#2A1B24",
    "rejected": "#695A62",
    "cancelled": "#695A62",
}


def render_request(r, role):
    color = STATUS_COLORS.get(r["status"], "#695A62")
    counterparty = r["recipient_name"] if role == "incoming" else r["donor_name"]
    with st.container():
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown(
                f"""<div style="background:white;border:1px solid rgba(42,27,36,0.08);border-radius:14px;padding:16px;margin-bottom:12px;">
                <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.18em;color:#695A62;">{counterparty}</div>
                <div style="font-family:'Cormorant Garamond',serif;font-size:20px;margin-top:4px;">{r['listing_name']}</div>
                <div style="color:#695A62;font-size:13px;margin-top:6px;">{r['requested_quantity']} {r['unit']} · {r['created_at'][:16].replace('T',' ')}</div>
                {f'<div style="margin-top:8px;font-style:italic;color:#695A62;">&ldquo;{r["note"]}&rdquo;</div>' if r.get("note") else ''}
                <div style="margin-top:10px;">
                    <span style="background:{color}22;color:{color};padding:3px 10px;border-radius:999px;font-size:11px;text-transform:uppercase;font-weight:700;letter-spacing:0.1em;">{r['status']}</span>
                </div>
            </div>""",
                unsafe_allow_html=True,
            )
        with c2:
            if role == "incoming" and r["status"] == "pending":
                ca, cb = st.columns(2)
                with ca:
                    if st.button("Reject", key=f"rej_{r['id']}", type="secondary", use_container_width=True):
                        reject_request(r["id"])
                        st.rerun()
                with cb:
                    if st.button("Approve", key=f"app_{r['id']}", type="primary", use_container_width=True):
                        approve_request(r["id"])
                        st.success("Approved.")
                        st.rerun()
            elif role == "outgoing" and r["status"] == "approved":
                # Recipient confirms pickup with PIN — PIN is visible from listing detail
                listing = get_listing(r["listing_id"])
                pin = st.text_input(
                    "Enter pickup PIN",
                    key=f"pin_{r['id']}",
                    max_chars=4,
                    placeholder="4-digit PIN",
                    help=f"Hint (demo): {listing['pickup_pin']}" if listing else "",
                )
                if st.button("Confirm pickup", key=f"conf_{r['id']}", type="primary", use_container_width=True):
                    ok, msg, data = confirm_pickup(r["id"], pin)
                    if ok:
                        st.success(msg)
                        refresh_user()
                        st.rerun()
                    else:
                        st.error(msg)
            else:
                st.write("")


for idx, role in enumerate(roles):
    items = requests_for(user, role)
    with tabs[idx]:
        if not items:
            st.info("No requests yet.")
        else:
            for r in items:
                render_request(r, role)
