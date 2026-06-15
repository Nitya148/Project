"""Impact dashboard — personal + global stats with chart."""
import streamlit as st
import pandas as pd
import plotly.express as px

from replate.auth import require_login
from replate.services import impact_for_user, global_impact, leaderboard
from replate.utils import inject_style, overline, logo_header, stat_card

st.set_page_config(page_title="Impact · RePlate", page_icon="✨", layout="wide")
inject_style()
user = require_login()

with st.sidebar:
    logo_header()

overline("Impact dashboard")
st.title("Every pickup, a measurable good.")

me = impact_for_user(user)
g = global_impact()

st.subheader("Network impact" if user["role"] == "admin" else "Your contribution")
c1, c2, c3, c4 = st.columns(4)
with c1:
    stat_card("Pickups", f"{me['total_pickups']:,}", accent=True)
with c2:
    stat_card("Meals contributed", f"{me['total_meals']:,}")
with c3:
    stat_card("Kg of food", f"{me['total_kg']:,}")
with c4:
    stat_card("Kg CO₂ avoided", f"{me['total_co2_kg']:,}")

st.markdown("---")

st.subheader("Meals over time")
if me["by_day"]:
    df = pd.DataFrame(me["by_day"])
    fig = px.line(df, x="date", y="meals", markers=True, color_discrete_sequence=["#C85A40"])
    fig.update_layout(
        plot_bgcolor="#FDFBF7", paper_bgcolor="#FDFBF7",
        margin=dict(l=0, r=0, t=10, b=0),
        font=dict(family="Outfit, sans-serif", color="#2A1B24"),
    )
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(gridcolor="rgba(42,27,36,0.08)")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No completed pickups yet — your chart will appear here.")

st.markdown("---")

g_col, lb_col = st.columns([2, 1])
with g_col:
    overline("Network total")
    st.subheader("Together we've rescued")
    cA, cB, cC = st.columns(3)
    with cA:
        stat_card("Meals", f"{g['total_meals']:,}", accent=True)
    with cB:
        stat_card("Kg of food", f"{g['total_kg']:,}")
    with cC:
        stat_card("Kg CO₂ avoided", f"{g['total_co2_kg']:,}")

with lb_col:
    overline("Top donors")
    st.subheader("Leaderboard")
    leaders = leaderboard()
    for i, l in enumerate(leaders[:8]):
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid rgba(42,27,36,0.06);'>"
            f"<span><em style='color:#695A62;font-family:Cormorant Garamond,serif;font-size:18px;'>{i+1}</em> &nbsp; {l['org_name'] or l['name']}</span>"
            f"<span style='color:#C85A40;font-weight:700;'>{l['points']:,} pts</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
