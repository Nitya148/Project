# RePlate — Real-time Food Rescue (Streamlit edition)

> Connect surplus food donors with verified community kitchens, NGOs and food banks. Hyderabad demo seeded out of the box.

A self-contained **Streamlit + SQLite + bcrypt** version of the RePlate platform — designed for one-click deployment to **Streamlit Community Cloud**.

## Features

- **Two roles**: Donors (restaurants, cafés, bakeries) list surplus; Recipients (NGOs, kitchens, food banks) claim it.
- **Real-time discovery** with distance + category filters.
- **Interactive Leaflet map** (Folium) of nearby surplus across Hyderabad.
- **PIN-based pickup confirmation** that awards reward points to donors.
- **Reward catalog** with redeemable partner vouchers.
- **Impact dashboard** with personal + global stats and a Plotly line chart.
- **Admin console** for verifying recipient organizations.
- **Seeded Hyderabad demo data**: Café Niloufer, Karachi Bakery, Paradise, Chutneys, Pista House, Bawarchi, Ohri's, Almond House, Conçu Patisserie + 7 NGOs/kitchens + 12 active listings + 120 historical pickups (≈ 3,000+ meals, 500 kg food, 2,000 kg CO₂).

---

## Quickstart (local)

```bash
git clone <your-repo-url>
cd replate_streamlit

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

streamlit run streamlit_app.py
```

Open <http://localhost:8501>. The SQLite database (`replate.db`) is created and seeded automatically on first launch.

---

## Deploy to Streamlit Cloud

1. **Push to GitHub.** Create a new repo and push this folder:
   ```bash
   git init
   git add .
   git commit -m "RePlate — Streamlit edition"
   git branch -M main
   git remote add origin https://github.com/<you>/replate-streamlit.git
   git push -u origin main
   ```

2. **Deploy.** Go to <https://share.streamlit.io> → **New app** → pick your repo, set the entry file to **`streamlit_app.py`**, and click **Deploy**.

3. **(Optional) Override admin credentials.** In the app's Streamlit Cloud settings → **Secrets**, add:
   ```toml
   REPLATE_ADMIN_EMAIL = "admin@yourdomain.app"
   REPLATE_ADMIN_PASSWORD = "your-secure-admin-pw"
   ```
   These are read at startup from env vars (Streamlit Cloud injects secrets as env vars).

That's it — the app will be live at `https://<your-app>.streamlit.app`.

> **Note on persistence**: Streamlit Cloud's filesystem is **ephemeral** — the SQLite DB resets whenever the app sleeps or redeploys. The seeded demo data is re-created automatically on cold start, so the demo is always populated. For real production use with persistent storage, swap `replate/db.py` to use a hosted Postgres (e.g., Neon, Supabase) or MongoDB Atlas connection string from `st.secrets`.

---

## Demo accounts (seeded automatically)

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@replate.app` | `Admin123!` |
| Donor — Café Niloufer | `niloufer@replate.app` | `Demo123!` |
| Donor — Paradise Restaurant | `paradise@replate.app` | `Demo123!` |
| Donor — Karachi Bakery | `karachi@replate.app` | `Demo123!` |
| Donor — Pista House, Bawarchi, Ohri's, Almond House, Conçu, Chutneys | `…@replate.app` | `Demo123!` |
| Recipient (verified) — Akshaya Patra | `akshaya@replate.app` | `Demo123!` |
| Recipient (verified) — Goonj, Feeding India, Helping Hand, Aasara, Bhumi | `…@replate.app` | `Demo123!` |
| Recipient (PENDING admin verification) | `robinhood@replate.app` | `Demo123!` |

Use the **Demo accounts** tab on the home page to sign in with one click.

---

## Project structure

```
replate_streamlit/
├── streamlit_app.py             # Entry point (home + auth)
├── requirements.txt
├── .streamlit/config.toml       # Theme & server config
├── replate/
│   ├── __init__.py
│   ├── auth.py                  # bcrypt + session_state auth
│   ├── db.py                    # SQLite schema + helpers
│   ├── seed.py                  # Demo data (Hyderabad)
│   ├── services.py              # Listings/requests/rewards/impact logic
│   ├── maps.py                  # Folium map renderer
│   └── utils.py                 # Distance, formatting, custom CSS
└── pages/
    ├── 1_Discover.py
    ├── 2_My_Listings.py
    ├── 3_Requests.py
    ├── 4_Listing.py             # Listing detail (selected via session_state)
    ├── 5_Impact.py
    ├── 6_Rewards.py
    └── 7_Admin.py
```

---

## Customizing

- **Brand colors** live in two places:
  - `.streamlit/config.toml` (Streamlit theme)
  - `replate/utils.py` → `inject_style()` (custom CSS overrides)
- **Demo data** lives in `replate/seed.py`. Tweak donors/recipients/listings or set `random.seed(...)` differently to reshape the historical impact numbers.
- **Reward catalog** is in `replate/seed.py` → `SAMPLE_VOUCHERS`.

---

## Differences from the original React + FastAPI app

- **Storage**: SQLite (local file) instead of MongoDB.
- **Auth**: Session-based (`st.session_state`) instead of JWT cookies. Logs out on browser refresh, which is fine for demo / single-tenant use.
- **UI**: Streamlit's native components styled with custom CSS — close to the editorial palette but with Streamlit's component constraints (no fully custom modals, sidebar nav instead of top-nav).
- **Maps**: Folium via `streamlit-folium` — same Carto Voyager tiles, click-to-navigate works.
- **Deployment**: One-click on Streamlit Cloud, no separate backend/frontend processes.

Everything else (donor/recipient flow, PIN pickup, rewards, impact, admin verification) works identically.

---

## License

MIT — feel free to fork and adapt.
