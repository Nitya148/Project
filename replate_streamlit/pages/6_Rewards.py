"""Rewards — voucher catalog + redemption history."""
import streamlit as st

from replate.auth import require_login, refresh_user
from replate.services import list_vouchers, redeem, my_redemptions, my_transactions
from replate.utils import inject_style, overline, logo_header, stat_card

st.set_page_config(page_title="Rewards · RePlate", page_icon="🎁", layout="wide")
inject_style()
user = require_login()

with st.sidebar:
    logo_header()

overline("Reward catalog")
st.title("Points that give back.")

stat_col1, stat_col2 = st.columns([1, 3])
with stat_col1:
    stat_card("Your balance", f"{user.get('points',0):,}", accent=True)
with stat_col2:
    st.write("Redeem your rescue points with our local partners. Donor accounts earn points on every confirmed pickup.")

st.markdown("---")

st.subheader("Available vouchers")
vouchers = list_vouchers()
cols = st.columns(3)
for i, v in enumerate(vouchers):
    with cols[i % 3]:
        can = user.get("points", 0) >= v["points_cost"]
        st.markdown(
            f"""<div class="listing-card">
            <img src="{v['image_url']}" alt=""/>
            <div class="info">
                <div class="donor">{v['partner']}</div>
                <div class="title">{v['title']}</div>
                <div style="font-size:13px;color:#695A62;margin-top:6px;line-height:1.5;">{v['description']}</div>
                <div style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;">
                    <span style="font-weight:700;color:#C85A40;">{v['points_cost']:,} pts</span>
                </div>
            </div>
            </div>""",
            unsafe_allow_html=True,
        )
        btn_label = "Redeem" if can else f"Need {v['points_cost'] - user.get('points',0):,} more"
        if st.button(btn_label, key=f"redeem_{v['id']}", disabled=not can, type="primary" if can else "secondary", use_container_width=True):
            ok, msg, code = redeem(user, v["id"])
            if ok:
                st.success(f"Redeemed! Code: **{code}**")
                refresh_user()
                st.rerun()
            else:
                st.error(msg)

# History
st.markdown("---")
red_col, tx_col = st.columns(2)
with red_col:
    st.subheader("Your redemptions")
    reds = my_redemptions(user["id"])
    if not reds:
        st.caption("No redemptions yet.")
    for r in reds:
        st.markdown(
            f"<div style='background:white;border:1px solid rgba(42,27,36,0.08);border-radius:12px;padding:12px 14px;margin-bottom:8px;'>"
            f"<div style='font-size:11px;color:#695A62;text-transform:uppercase;letter-spacing:0.18em;'>{r['partner']}</div>"
            f"<div style='margin-top:2px;'><strong>{r['voucher_title']}</strong></div>"
            f"<div style='margin-top:6px;font-family:monospace;background:#2A1B24;color:#FDFBF7;display:inline-block;padding:4px 10px;border-radius:999px;font-size:12px;'>{r['code']}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

with tx_col:
    st.subheader("Point history")
    txs = my_transactions(user["id"])
    if not txs:
        st.caption("No transactions yet.")
    for t in txs:
        color = "#6B705C" if t["amount"] > 0 else "#C85A40"
        sign = "+" if t["amount"] > 0 else ""
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid rgba(42,27,36,0.06);'>"
            f"<div><div>{t['reason']}</div><div style='font-size:11px;color:#695A62;'>{t['created_at'][:16].replace('T',' ')}</div></div>"
            f"<span style='color:{color};font-weight:700;'>{sign}{t['amount']:,}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
