"""RePlate — Streamlit Cloud entry point."""
import streamlit as st

from replate.db import init_db
from replate.seed import seed_all
from replate.auth import current_user, login, register, logout
from replate.services import global_impact, leaderboard
from replate.utils import inject_style, overline, logo_header, stat_card

# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="RePlate — Real-time food rescue",
    page_icon="🍞",
    layout="wide",
    initial_sidebar_state="expanded",
)

init_db()
seed_all()
inject_style()


# ----------------------------- Sidebar -------------------------------------

with st.sidebar:
    logo_header()
    user = current_user()
    if user:
        st.markdown(
            f"""<div style="background:#F4EFE6;padding:14px;border-radius:14px;margin-bottom:12px;">
            <div style="font-size:11px;text-transform:uppercase;letter-spacing:0.18em;color:#695A62;">{user['role']}</div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:20px;margin-top:2px;">{user.get('org_name') or user.get('name')}</div>
            <div style="font-size:12px;color:#695A62;">{user['email']}</div>
            </div>""",
            unsafe_allow_html=True,
        )
        if user["role"] == "donor":
            st.metric("Reward points", user.get("points", 0))
        st.divider()
        if st.button("Sign out", use_container_width=True, type="secondary"):
            logout()
            st.rerun()
    else:
        st.info("Sign in below to access the full network.")


# ----------------------------- Home / Auth ---------------------------------

if not user:
    # Hero
    g = global_impact()
    st.markdown(
        f"""
        <div class="hero">
            <div class="overline">Real-time food rescue · neighborhood network</div>
            <h1>Surplus food,<br/><em>redistributed</em> before it's gone.</h1>
            <p>Restaurants, cafés and bakeries list their daily surplus. Verified community kitchens, food banks and shelters claim it in real time. Everyone earns points for what they save.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Live network stat block
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stat_card("Meals diverted", f"{g['total_meals']:,}", accent=True)
    with c2:
        stat_card("Kg of food saved", f"{g['total_kg']:,}")
    with c3:
        stat_card("Kg CO₂ avoided", f"{g['total_co2_kg']:,}")
    with c4:
        stat_card("Confirmed pickups", f"{g['total_pickups']:,}")

    st.markdown("---")

    # Auth tabs
    tab_in, tab_up, tab_demo = st.tabs(["Sign in", "Create account", "Demo accounts"])

    with tab_in:
        st.markdown("##### Welcome back")
        email = st.text_input("Email", key="login_email", placeholder="you@kitchen.com")
        password = st.text_input("Password", key="login_pw", type="password")
        if st.button("Sign in", type="primary", use_container_width=True, key="login_btn"):
            ok, msg = login(email, password)
            if ok:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    with tab_up:
        st.markdown("##### Join the rescue network")
        role = st.radio(
            "I am a…",
            ["donor", "recipient"],
            horizontal=True,
            help="Donors list surplus. Recipients claim it (admin verification required).",
            key="reg_role",
        )
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your name", key="reg_name")
            org_name = st.text_input("Organization name", key="reg_org")
            email_r = st.text_input("Email", key="reg_email")
        with col2:
            if role == "donor":
                org_type = st.selectbox("Organization type", ["restaurant", "cafe", "bakery", "other"], key="reg_orgtype_d")
            else:
                org_type = st.selectbox("Organization type", ["ngo", "community_kitchen", "food_bank", "other"], key="reg_orgtype_r")
            pw_r = st.text_input("Password (≥6 chars)", type="password", key="reg_pw")
            address = st.text_input("Pickup address", key="reg_addr", placeholder="Street, City")

        if role == "recipient":
            st.info("Recipient organizations require admin verification before claiming food.")

        if st.button("Create account", type="primary", use_container_width=True, key="reg_btn"):
            if not (name and org_name and email_r and pw_r and len(pw_r) >= 6):
                st.error("Please fill all fields. Password ≥ 6 characters.")
            else:
                ok, msg = register({
                    "email": email_r,
                    "password": pw_r,
                    "name": name,
                    "org_name": org_name,
                    "org_type": org_type,
                    "role": role,
                    "address": address,
                    "lat": 17.4239,
                    "lng": 78.4738,
                })
                if ok:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

    with tab_demo:
        st.markdown("##### Try a seeded account (Hyderabad demo)")
        demos = [
            ("Donor — Café Niloufer", "niloufer@replate.app", "Demo123!"),
            ("Donor — Paradise Restaurant", "paradise@replate.app", "Demo123!"),
            ("Recipient — Akshaya Patra (verified)", "akshaya@replate.app", "Demo123!"),
            ("Recipient — Robin Hood Army (PENDING)", "robinhood@replate.app", "Demo123!"),
            ("Admin", "admin@replate.app", "Admin123!"),
        ]
        for label, em, pw in demos:
            cols = st.columns([3, 1])
            with cols[0]:
                st.markdown(f"**{label}**  \n`{em}` · `{pw}`")
            with cols[1]:
                if st.button("Sign in →", key=f"demo_{em}"):
                    ok, _ = login(em, pw)
                    if ok:
                        st.rerun()

    # Leaderboard
    st.markdown("---")
    overline("Top donors")
    st.subheader("Who's rescuing the most surplus")
    leaders = leaderboard()
    if leaders:
        c1, c2, c3 = st.columns(3)
        cols = [c1, c2, c3]
        for i, l in enumerate(leaders[:9]):
            with cols[i % 3]:
                st.markdown(
                    f"""<div class="stat-card" style="margin-bottom:12px;">
                        <div style="font-size:12px;color:#695A62;">#{i+1}</div>
                        <div style="font-family:'Cormorant Garamond',serif;font-size:20px;color:#2A1B24;margin-top:2px;">{l['org_name'] or l['name']}</div>
                        <div style="color:#C85A40;font-weight:700;margin-top:6px;">{l['points']:,} pts</div>
                    </div>""",
                    unsafe_allow_html=True,
                )
    else:
        st.info("No completed pickups yet.")

else:
    # Logged in → show dashboard summary on home page
    st.markdown(
        f"""
        <div class="hero">
            <div class="overline">Welcome back</div>
            <h1>{user.get('org_name') or user.get('name')}</h1>
            <p>{"Here's what's happening with your surplus today." if user['role']=='donor' else "Nearby food is ready for you." if user.get('verified') else "Your verification is pending. You can browse listings but claiming is locked."}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    from replate.services import impact_for_user, requests_for, list_by_donor

    me = impact_for_user(user)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        stat_card("Reward points", f"{user.get('points',0):,}", accent=True)
    with c2:
        stat_card("Pickups", me["total_pickups"])
    with c3:
        stat_card("Meals contributed", me["total_meals"])
    with c4:
        stat_card("Kg CO₂ avoided", me["total_co2_kg"])

    st.markdown("---")

    pending_requests = [r for r in requests_for(user) if r["status"] == "pending"]
    cA, cB, cC = st.columns(3)
    with cA:
        st.markdown('<div class="overline">Up next</div>', unsafe_allow_html=True)
        if user["role"] == "donor":
            st.subheader("Create a listing")
            st.write("Add today's surplus in a minute.")
            st.page_link("pages/2_My_Listings.py", label="Go to listings →")
        else:
            st.subheader("Discover nearby")
            st.write("Browse active surplus around you.")
            st.page_link("pages/1_Discover.py", label="Open Discover →")
    with cB:
        st.markdown('<div class="overline">Inbox</div>', unsafe_allow_html=True)
        st.subheader(f"{len(pending_requests)} pending request{'' if len(pending_requests)==1 else 's'}")
        st.page_link("pages/3_Requests.py", label="View requests →")
    with cC:
        st.markdown('<div class="overline">Impact</div>', unsafe_allow_html=True)
        st.subheader("Your contribution")
        st.write(f"{me['total_meals']} meals · {me['total_kg']} kg saved.")
        st.page_link("pages/5_Impact.py", label="Open Impact →")
