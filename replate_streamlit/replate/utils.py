"""Utilities: distance, formatting, custom styles."""
from __future__ import annotations

import math
import streamlit as st
from datetime import datetime, timezone


def haversine_km(lat1, lng1, lat2, lng2) -> float:
    if None in (lat1, lng1, lat2, lng2):
        return 999.0
    R = 6371.0
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lng2 - lng1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * R * math.asin(math.sqrt(a))


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def time_until(iso: str) -> tuple[str, int]:
    d = parse_iso(iso)
    diff = (d - datetime.now(timezone.utc)).total_seconds() / 60
    if diff <= 0:
        return "expired", 0
    mins = int(diff)
    if mins < 60:
        return f"{mins} min left", mins
    hours = mins // 60
    if hours < 24:
        return f"{hours}h left", mins
    return f"{hours // 24}d left", mins


def fmt_qty(q: float) -> str:
    return str(int(q)) if float(q).is_integer() else f"{q:.1f}"


def inject_style() -> None:
    """Custom CSS to evoke the editorial terracotta / bone-white palette."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,500;0,600;1,500&family=Outfit:wght@300;400;500;600&display=swap');

        html, body, [class*="css"], .stApp {
            background: #FDFBF7 !important;
            color: #2A1B24 !important;
            font-family: 'Outfit', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif !important;
        }

        h1, h2, h3, .serif {
            font-family: 'Cormorant Garamond', Georgia, serif !important;
            font-weight: 500 !important;
            letter-spacing: -0.01em;
            color: #2A1B24 !important;
        }

        /* Overline */
        .overline {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.22em;
            text-transform: uppercase;
            color: #C85A40;
            margin-bottom: 8px;
        }

        /* Stat card */
        .stat-card {
            background: white;
            border-radius: 20px;
            padding: 24px;
            border: 1px solid rgba(42,27,36,0.08);
        }
        .stat-card .num {
            font-family: 'Cormorant Garamond', serif;
            font-size: 36px;
            color: #2A1B24;
            line-height: 1.1;
        }
        .stat-card .lbl {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: #695A62;
            margin-top: 4px;
        }
        .stat-card.accent { background: #C85A40; color: white; border-color: transparent; }
        .stat-card.accent .num { color: white; }
        .stat-card.accent .lbl { color: rgba(255,255,255,0.7); }

        /* Listing card */
        .listing-card {
            background: #F4EFE6;
            border-radius: 24px;
            padding: 0;
            border: 1px solid rgba(42,27,36,0.08);
            overflow: hidden;
            margin-bottom: 18px;
        }
        .listing-card .info { padding: 18px 22px; }
        .listing-card .donor {
            font-size: 11px;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: #695A62;
        }
        .listing-card .title {
            font-family: 'Cormorant Garamond', serif;
            font-size: 22px;
            margin-top: 4px;
            line-height: 1.2;
        }
        .listing-card .meta {
            display: flex;
            justify-content: space-between;
            margin-top: 12px;
            font-size: 13px;
            color: #695A62;
        }
        .listing-card .urgent { color: #D97D3A; font-weight: 600; }
        .listing-card img {
            width: 100%;
            aspect-ratio: 4/3;
            object-fit: cover;
            display: block;
        }

        .badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 10px;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            font-weight: 700;
        }
        .badge-bakery { background: rgba(217,125,58,0.12); color: #D97D3A; }
        .badge-success { background: rgba(107,112,92,0.15); color: #6B705C; }
        .badge-urgent { background: rgba(217,125,58,0.15); color: #D97D3A; }

        /* Buttons */
        .stButton > button[kind="primary"] {
            background-color: #C85A40 !important;
            color: white !important;
            border: none !important;
            border-radius: 999px !important;
            padding: 10px 22px !important;
            font-weight: 500 !important;
            font-family: 'Outfit', sans-serif !important;
        }
        .stButton > button[kind="primary"]:hover { background-color: #A64630 !important; }
        .stButton > button[kind="secondary"] {
            background-color: #F4EFE6 !important;
            color: #2A1B24 !important;
            border: 1px solid rgba(42,27,36,0.1) !important;
            border-radius: 999px !important;
            padding: 10px 22px !important;
            font-weight: 500 !important;
        }
        .stButton > button[kind="secondary"]:hover { background-color: #EAE2D3 !important; }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; }
        .stTabs [data-baseweb="tab"] {
            background: #F4EFE6;
            border-radius: 999px;
            padding: 6px 16px;
            color: #695A62;
        }
        .stTabs [aria-selected="true"] {
            background: #2A1B24 !important;
            color: #FDFBF7 !important;
        }

        /* Inputs */
        .stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox > div {
            border-radius: 12px !important;
        }

        /* Hide hamburger and footer */
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        /* PIN display */
        .pin {
            font-family: 'Cormorant Garamond', serif;
            font-size: 42px;
            letter-spacing: 0.4em;
            color: #C85A40;
            font-weight: 600;
        }

        /* Hero banner */
        .hero {
            padding: 60px 40px;
            background: linear-gradient(135deg, #FDFBF7 0%, #F4EFE6 100%);
            border-radius: 28px;
            margin-bottom: 28px;
            border: 1px solid rgba(42,27,36,0.06);
        }
        .hero h1 {
            font-family: 'Cormorant Garamond', serif !important;
            font-size: 60px !important;
            line-height: 1 !important;
            margin: 12px 0 16px !important;
            font-weight: 500 !important;
        }
        .hero h1 em { color: #C85A40; }
        .hero p { color: #695A62; font-size: 17px; line-height: 1.6; max-width: 540px; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def stat_card(label: str, value, accent: bool = False) -> None:
    klass = "stat-card accent" if accent else "stat-card"
    st.markdown(
        f"""<div class="{klass}">
            <div class="num">{value}</div>
            <div class="lbl">{label}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def overline(text: str) -> None:
    st.markdown(f'<div class="overline">{text}</div>', unsafe_allow_html=True)


def logo_header(subtitle: str | None = None) -> None:
    st.markdown(
        f"""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;">
            <div style="width:34px;height:34px;border-radius:999px;background:#C85A40;display:flex;align-items:center;justify-content:center;color:#FDFBF7;font-family:'Cormorant Garamond',serif;font-style:italic;font-size:22px;line-height:1;">R</div>
            <div style="font-family:'Cormorant Garamond',serif;font-size:26px;">Re<em style="color:#C85A40;font-style:italic;">Plate</em></div>
        </div>
        {f'<div style="color:#695A62;font-size:14px;margin-bottom:24px;">{subtitle}</div>' if subtitle else ''}
        """,
        unsafe_allow_html=True,
    )
