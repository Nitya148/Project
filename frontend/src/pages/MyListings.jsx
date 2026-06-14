import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api from "@/lib/api";
import { Plus, PackageOpen } from "lucide-react";
import { ListingCard } from "@/pages/Discover";

const TABS = [
  { v: "active", l: "Active" },
  { v: "completed", l: "Completed" },
  { v: "expired", l: "Expired" },
  { v: "cancelled", l: "Cancelled" },
];

export default function MyListings() {
  const [items, setItems] = useState([]);
  const [tab, setTab] = useState("active");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    api.get("/listings", { params: { mine: true } }).then((r) => {
      setItems(r.data);
      setLoading(false);
    });
  }, []);

  const filtered = items.filter((l) => l.status === tab);

  return (
    <div className="space-y-8" data-testid="my-listings-page">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="overline">Your kitchen</span>
          <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">Your listings</h1>
          <p className="text-[#695A62] mt-2">Manage active surplus and review history.</p>
        </div>
        <Link to="/listings/new" className="btn-primary" data-testid="new-listing-btn">
          <Plus className="w-4 h-4" /> New listing
        </Link>
      </header>

      <div className="flex flex-wrap gap-2">
        {TABS.map((t) => (
          <button
            key={t.v}
            onClick={() => setTab(t.v)}
            data-testid={`tab-${t.v}`}
            className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
              tab === t.v ? "bg-[#2A1B24] text-[#FDFBF7]" : "bg-[#F4EFE6] text-[#2A1B24]/70 hover:text-[#2A1B24]"
            }`}
          >
            {t.l}{" "}
            <span className="opacity-60">({items.filter((l) => l.status === t.v).length})</span>
          </button>
        ))}
      </div>

      {loading ? (
        <div className="text-center py-20 text-[#695A62]">Loading…</div>
      ) : filtered.length === 0 ? (
        <div className="card text-center !p-16">
          <PackageOpen className="w-8 h-8 mx-auto text-[#C85A40]" strokeWidth={1.5} />
          <h2 className="font-serif text-2xl mt-4">No {tab} listings</h2>
          <p className="text-[#695A62] mt-2 mb-6">Create your first listing — it takes about a minute.</p>
          <Link to="/listings/new" className="btn-primary text-sm !py-2.5">
            <Plus className="w-4 h-4" /> Create listing
          </Link>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((l) => <ListingCard key={l.id} l={l} />)}
        </div>
      )}
    </div>
  );
}
