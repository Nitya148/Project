import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Clock, MapPin, Filter, Compass, ShieldAlert, LayoutGrid, Map as MapIcon } from "lucide-react";
import MapView from "@/components/MapView";

const CATEGORIES = [
  { v: "", l: "All categories" },
  { v: "produce", l: "Produce" },
  { v: "bakery", l: "Bakery" },
  { v: "prepared_meals", l: "Prepared meals" },
  { v: "dairy", l: "Dairy" },
  { v: "pantry", l: "Pantry" },
  { v: "beverages", l: "Beverages" },
  { v: "other", l: "Other" },
];

export default function Discover() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [radius, setRadius] = useState(50);
  const [category, setCategory] = useState("");
  const [view, setView] = useState("list");

  useEffect(() => {
    setLoading(true);
    api
      .get("/listings/discover", { params: { radius_km: radius, category: category || undefined } })
      .then((r) => setItems(r.data))
      .finally(() => setLoading(false));
  }, [radius, category]);

  const origin = user.lat != null && user.lng != null
    ? { lat: user.lat, lng: user.lng, label: user.org_name || "You" }
    : null;

  return (
    <div className="space-y-8" data-testid="discover-page">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <span className="overline">Discover</span>
          <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">Surplus near you</h1>
          <p className="text-[#695A62] mt-2">Real-time listings sorted by distance and urgency.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Compass className="w-5 h-5 text-[#C85A40]" />
            <span className="text-sm text-[#695A62]">{items.length} listings available</span>
          </div>
          <div className="flex bg-[#F4EFE6] rounded-full p-1" data-testid="view-toggle">
            <button
              onClick={() => setView("list")}
              data-testid="view-list"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                view === "list" ? "bg-[#2A1B24] text-[#FDFBF7]" : "text-[#2A1B24]/70"
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              List
            </button>
            <button
              onClick={() => setView("map")}
              data-testid="view-map"
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                view === "map" ? "bg-[#2A1B24] text-[#FDFBF7]" : "text-[#2A1B24]/70"
              }`}
            >
              <MapIcon className="w-3.5 h-3.5" />
              Map
            </button>
          </div>
        </div>
      </header>

      {!user.verified && (
        <div className="rounded-2xl bg-[#D97D3A]/10 border border-[#D97D3A]/20 p-5 flex items-start gap-4" data-testid="unverified-warning">
          <ShieldAlert className="w-5 h-5 text-[#D97D3A] mt-0.5" />
          <div className="text-sm">
            <div className="font-medium text-[#2A1B24]">Verification pending</div>
            <div className="text-[#695A62] mt-1">
              You can browse all listings, but claiming is locked until an admin verifies your organization.
            </div>
          </div>
        </div>
      )}

      <div className="card !p-5 flex flex-wrap items-center gap-4">
        <Filter className="w-4 h-4 text-[#695A62]" />
        <div className="flex items-center gap-2">
          <label className="text-xs uppercase tracking-wider text-[#695A62]">Category</label>
          <select value={category} onChange={(e) => setCategory(e.target.value)} className="bg-white rounded-full border border-[#2A1B24]/10 px-3 py-1.5 text-sm" data-testid="filter-category">
            {CATEGORIES.map((c) => <option key={c.v} value={c.v}>{c.l}</option>)}
          </select>
        </div>
        <div className="flex items-center gap-2 ml-auto">
          <label className="text-xs uppercase tracking-wider text-[#695A62]">Radius</label>
          <input type="range" min="1" max="200" value={radius} onChange={(e) => setRadius(Number(e.target.value))} className="accent-[#C85A40]" data-testid="filter-radius" />
          <span className="text-sm font-medium w-12 text-right">{radius} km</span>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-[#695A62]">Loading nearby surplus…</div>
      ) : items.length === 0 ? (
        <div className="card text-center !p-16">
          <Compass className="w-8 h-8 mx-auto text-[#C85A40]" strokeWidth={1.5} />
          <h2 className="font-serif text-2xl mt-4">Nothing nearby right now</h2>
          <p className="text-[#695A62] mt-2">Try expanding the radius or check back in a bit — new listings drop throughout the day.</p>
        </div>
      ) : view === "map" ? (
        <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
          <div className="lg:col-span-3" data-testid="discover-map">
            <MapView listings={items} origin={origin} height={560} />
          </div>
          <div className="lg:col-span-2 space-y-3 max-h-[560px] overflow-y-auto pr-1">
            {items.map((l, idx) => (
              <Link
                to={`/listings/${l.id}`}
                key={l.id}
                className="card-light flex gap-4 hover:-translate-y-0.5 hover:shadow-[0_8px_20px_rgba(42,27,36,0.06)] transition-all"
                data-testid={`map-row-${l.id}`}
              >
                <div className="w-7 h-7 rounded-full bg-[#C85A40] text-white text-xs font-bold flex items-center justify-center shrink-0">
                  {idx + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-[10px] uppercase tracking-[0.18em] text-[#695A62]">{l.donor_name}</div>
                  <div className="font-serif text-lg leading-tight mt-1 truncate">{l.name}</div>
                  <div className="flex items-center justify-between mt-1 text-xs text-[#695A62]">
                    <span>{l.remaining_quantity} {l.unit}</span>
                    {l.distance_km != null && <span className="text-[#C85A40] font-semibold">{l.distance_km} km</span>}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {items.map((l) => <ListingCard key={l.id} l={l} />)}
        </div>
      )}
    </div>
  );
}

export function ListingCard({ l }) {
  const expiresIn = useMemo(() => timeUntil(l.expiry_time), [l.expiry_time]);
  const urgent = expiresIn.totalMinutes <= 240;
  return (
    <Link to={`/listings/${l.id}`} className="card !p-0 overflow-hidden group hover:-translate-y-1 hover:shadow-[0_12px_32px_rgba(42,27,36,0.08)] transition-all" data-testid={`discover-card-${l.id}`}>
      <div className="relative aspect-[4/3] bg-[#EAE2D3]">
        {l.photo_url && <img src={l.photo_url} alt={l.name} className="absolute inset-0 w-full h-full object-cover" />}
        <div className="absolute inset-0 bg-gradient-to-t from-[#2A1B24]/60 via-transparent to-transparent"></div>
        <div className="absolute top-4 left-4 flex gap-2">
          <span className="badge bg-white/90 !text-[#2A1B24]">{(l.category || "").replace("_", " ")}</span>
          {urgent && <span className="badge bg-[#D97D3A] !text-white">Expires soon</span>}
        </div>
        {l.distance_km != null && (
          <div className="absolute bottom-4 left-4 text-white text-xs font-medium flex items-center gap-1.5">
            <MapPin className="w-3.5 h-3.5" />
            {l.distance_km} km away
          </div>
        )}
      </div>
      <div className="p-6">
        <div className="text-xs uppercase tracking-[0.18em] text-[#695A62]">{l.donor_name}</div>
        <h3 className="font-serif text-2xl mt-2 leading-tight group-hover:text-[#C85A40] transition-colors">{l.name}</h3>
        <div className="mt-4 flex items-center justify-between text-sm">
          <span className="text-[#2A1B24]"><strong>{l.remaining_quantity}</strong> {l.unit}</span>
          <span className={`inline-flex items-center gap-1 ${urgent ? "text-[#D97D3A]" : "text-[#695A62]"}`}>
            <Clock className="w-3.5 h-3.5" />
            {expiresIn.label}
          </span>
        </div>
      </div>
    </Link>
  );
}

export function timeUntil(iso) {
  const d = new Date(iso);
  const diff = d - new Date();
  const totalMinutes = Math.max(0, Math.round(diff / 60000));
  if (totalMinutes <= 0) return { label: "expired", totalMinutes: 0 };
  if (totalMinutes < 60) return { label: `${totalMinutes} min left`, totalMinutes };
  const hours = Math.round(totalMinutes / 60);
  if (hours < 24) return { label: `${hours}h left`, totalMinutes };
  return { label: `${Math.round(hours / 24)}d left`, totalMinutes };
}
