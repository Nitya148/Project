"""Admin — verify recipient organizations."""
import streamlit as st

from replate.auth import require_role
from replate.services import admin_stats, all_recipients, verify_recipient, unverify_recipient
from replate.utils import inject_style, overline, logo_header, stat_card

st.set_page_config(page_title="Admin · RePlate", page_icon="🛡️", layout="wide")
inject_style()
user = require_role(["admin"])

with st.sidebar:
    logo_header()

overline("Admin console")
st.title("Verification & moderation")

stats = admin_stats()
c1, c2, c3, c4 = st.columns(4)
with c1:
    stat_card("Pending verifications", stats["pending_verifications"], accent=True)
with c2:
    stat_card("Active listings", stats["active_listings"])
with c3:
    stat_card("Completed pickups", stats["completed_pickups"])
with c4:
    stat_card("Total users", stats["users"])

st.markdown("---")

tabs = st.tabs(["Pending", "Verified"])
recipients = all_recipients()
pending = [r for r in recipients if not r["verified"]]
verified = [r for r in recipients if r["verified"]]


def render_row(r, is_verified):
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(
            f"<div style='background:white;border:1px solid rgba(42,27,36,0.08);border-radius:12px;padding:14px;margin-bottom:8px;'>"
            f"<div style='font-size:11px;color:#695A62;text-transform:uppercase;letter-spacing:0.18em;'>{(r['org_type'] or '').replace('_',' ')}</div>"
            f"<div style='font-family:Cormorant Garamond,serif;font-size:20px;margin-top:4px;'>{r['org_name'] or r['name']}</div>"
            f"<div style='font-size:13px;color:#695A62;'>{r['email']} · {r.get('phone','')}</div>"
            f"<div style='font-size:13px;color:#695A62;'>{r.get('address','')}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with c2:
        if is_verified:
            if st.button("Revoke", key=f"unv_{r['id']}", type="secondary", use_container_width=True):
                unverify_recipient(r["id"])
                st.rerun()
        else:
            if st.button("Verify ✓", key=f"v_{r['id']}", type="primary", use_container_width=True):
                verify_recipient(r["id"])
                st.success(f"{r['org_name']} verified.")
                st.rerun()


with tabs[0]:
    if not pending:
        st.info("No pending verifications.")
    else:
        for r in pending:
            render_row(r, False)

with tabs[1]:
    if not verified:
        st.info("No verified recipients yet.")
    else:
        for r in verified:
            render_row(r, True)
