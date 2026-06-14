# Food Waste Exchange (Food Xchange) — PRD & Progress

## Original Problem Statement
> "make this whole app and it has to be aesthetically pleasing" — referring to the attached **Food Waste Exchange PRD** (`Food_Waste_Exchange_PRD.docx`).

The PRD describes a real-time, location-aware platform that connects surplus food donors (restaurants, cafés, bakeries) with verified recipients (NGOs, community kitchens, food banks), with reward points and admin verification.

## Tech Stack
- **Frontend**: React 19, React Router 7, Tailwind CSS, lucide-react, Recharts, sonner. Custom design system with Cormorant Garamond + Outfit fonts and an editorial terracotta / bone-white / aubergine palette.
- **Backend**: FastAPI, Motor (MongoDB async), bcrypt + PyJWT auth (httpOnly cookie + Bearer fallback).
- **Storage**: MongoDB collections — `users`, `listings`, `requests`, `vouchers`, `redemptions`, `point_transactions`, `impact_events`.

## User Personas
1. **Donor** — restaurant / café / bakery (verified by default). Creates listings, manages incoming requests, earns reward points.
2. **Recipient** — NGO / community kitchen / food bank (requires admin verification). Browses nearby surplus, claims listings, confirms pickup with PIN.
3. **Admin** — Platform operator. Verifies recipient organizations and views platform-wide stats.

## Implemented (initial MVP — built Jan 2026)
- JWT auth (register / login / logout / me / profile) with role-based access. Admin + multi-account seeding.
- Donor flow: create listing (full form with category, qty, unit, storage, allergens, dietary tags, pickup window, expiry, photo, safety acknowledgement). Manage own listings by status (active / completed / expired / cancelled). Approve / reject incoming requests.
- Recipient flow: discover view with distance + category filters and radius slider. Listing detail with sealed pickup PIN that is only revealed after request approval. Request modal with partial-quantity claiming.
- Pickup confirmation via 4-digit PIN entered by recipient. On confirmation: points awarded to donor, meals + CO₂ impact recorded, listing quantity decremented.
- Reward catalog (6 seeded partner vouchers: Café Niloufer pastry, Karachi Bakery, etc.) with redemption + redemption history + point-transaction ledger.
- Impact dashboard: personal + global stats (pickups, meals, kg saved, CO₂), Recharts line chart of meals over time, top-donor leaderboard.
- Admin console: pending vs verified recipients tabs, one-click verify / revoke, platform stats.
- Landing page: editorial hero with hero photo background, live impact counter, three-step "how it works", reward strip, dark "why it matters" section, CTA.
- Seeded demo data — **Hyderabad-based** (added Jan 2026):
  - 4 donors: Café Niloufer, Karachi Bakery, Paradise Restaurant, Chutneys.
  - 3 recipients: Akshaya Patra (verified), Helping Hand Foundation (verified), Robin Hood Army Hyd (pending).
  - 5 active listings covering bakery, prepared meals, beverages, South Indian breakfast prep.

## Architecture Notes
- All backend endpoints prefixed with `/api`; frontend reads `REACT_APP_BACKEND_URL`.
- UUID string IDs (not Mongo ObjectId) — JSON safe by default.
- Datetimes stored as ISO-8601 strings (UTC) for portability.
- httpOnly `access_token` cookie + `Authorization: Bearer …` header fallback (token returned in login/register body; frontend keeps it in localStorage as `fx_token`).
- Idempotent seed: admin upserts, sample listings only seeded if no `active` listings exist. Old-sample-data cleanup runs once on each startup.

## Testing
Iteration 1: 26/26 backend pytest cases passed + full Playwright e2e of all role flows. Report: `/app/test_reports/iteration_1.json`.

## Backlog / Future
- **P1**: Real map view (Mapbox / Leaflet) instead of just distance; live notifications (push + email/SMS).
- **P1**: Photo upload (S3 / Cloudinary) instead of URL paste.
- **P2**: Offline pickup-confirmation queue with sync on reconnect (PRD mention).
- **P2**: Recipient organization document upload + admin document review UI.
- **P2**: Email verification on register; password reset.
- **P2**: Donor-side surplus insights (recurring patterns by category/time).
- **P3**: Partner-business portal for managing voucher inventory.
