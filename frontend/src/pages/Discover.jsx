import { useEffect, useState, useMemo } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Clock, MapPin, Filter, Compass, ShieldAlert } from "lucide-react";

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

  useEffect(() => {
    setLoading(true);
    api
      .get("/listings/discover", { params: { radius_km: radius, category: category || undefined } })
      .then((r) => setItems(r.data))
      .finally(() => setLoading(false));
  }, [radius, category]);

  return (
    <div className="space-y-8" data-testid="discover-page">
      <header className="flex items-end justify-between flex-wrap gap-4">
        <div>
          <span className="overline">Discover</span>
          <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">Surplus near you</h1>
          <p className="text-[#695A62] mt-2">Real-time listings sorted by distance and urgency.</p>
        </div>
        <div className="flex items-center gap-2">
          <Compass className="w-5 h-5 text-[#C85A40]" />
          <span className="text-sm text-[#695A62]">{items.length} listings available</span>
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
