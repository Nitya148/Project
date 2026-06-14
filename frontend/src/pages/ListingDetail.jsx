import { useEffect, useState } from "react";
import { useParams, Link, useNavigate } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { ArrowLeft, MapPin, Clock, Package, Thermometer, AlertCircle, Leaf, Send, X } from "lucide-react";
import { timeUntil } from "@/pages/Discover";
import MapView from "@/components/MapView";

export default function ListingDetail() {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showRequest, setShowRequest] = useState(false);
  const [qty, setQty] = useState(1);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    try {
      const { data } = await api.get(`/listings/${id}`);
      setListing(data);
      setQty(Math.min(1, data.remaining_quantity));
    } catch {
      toast.error("Listing not found");
      nav(-1);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [id]);

  if (loading || !listing) return <div className="text-center py-20 text-[#695A62]">Loading…</div>;

  const isOwner = listing.donor_id === user.id;
  const expires = timeUntil(listing.expiry_time);
  const canRequest = user.role === "recipient" && listing.status === "active" && !isOwner && user.verified;

  const submitRequest = async () => {
    setBusy(true);
    try {
      await api.post("/requests", { listing_id: listing.id, requested_quantity: Number(qty), note });
      toast.success("Request sent — the donor will review shortly.");
      setShowRequest(false);
      nav("/requests");
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  const cancelListing = async () => {
    if (!window.confirm("Cancel this listing?")) return;
    try {
      await api.delete(`/listings/${listing.id}`);
      toast.success("Listing cancelled");
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-8" data-testid="listing-detail">
      <button onClick={() => nav(-1)} className="btn-ghost !px-0 text-sm" data-testid="back-listing">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-8">
        <div className="lg:col-span-3 space-y-4">
          <div className="relative aspect-[4/3] rounded-3xl overflow-hidden bg-[#EAE2D3]">
            {listing.photo_url && <img src={listing.photo_url} alt={listing.name} className="w-full h-full object-cover" />}
            <div className="absolute top-4 left-4 flex gap-2">
              <span className="badge bg-white/95 !text-[#2A1B24]">{listing.category.replace("_", " ")}</span>
              <span className={`badge ${listing.status === "active" ? "bg-[#6B705C]/90 !text-white" : "bg-[#695A62]/80 !text-white"}`}>
                {listing.status}
              </span>
            </div>
          </div>

          {listing.lat != null && listing.lng != null && (
            <div data-testid="listing-map">
              <div className="overline mb-3 flex items-center gap-2">
                <MapPin className="w-3.5 h-3.5" /> Pickup location
              </div>
              <MapView
                listings={[listing]}
                origin={user.lat != null && user.lng != null ? { lat: user.lat, lng: user.lng, label: user.org_name || "You" } : null}
                height={320}
                interactive={true}
              />
            </div>
          )}
        </div>

        <div className="lg:col-span-2 space-y-6">
          <div>
            <div className="text-xs uppercase tracking-[0.22em] text-[#695A62]">{listing.donor_name}</div>
            <h1 className="font-serif text-4xl mt-2 leading-tight">{listing.name}</h1>
          </div>

          <div className="space-y-3 text-sm">
            <Row icon={Package} label={`${listing.remaining_quantity} ${listing.unit} available (of ${listing.quantity})`} />
            <Row icon={Thermometer} label={`Storage: ${listing.storage_condition}`} />
            <Row icon={Clock} label={`Pickup: ${formatRange(listing.pickup_start, listing.pickup_end)}`} />
            <Row icon={AlertCircle} label={`Expires in ${expires.label}`} accent={expires.totalMinutes <= 240} />
            <Row icon={MapPin} label={listing.pickup_address || "Address shared after approval"} />
          </div>

          {listing.allergens?.length > 0 && (
            <div>
              <div className="overline mb-2">Allergens</div>
              <div className="flex flex-wrap gap-1.5">
                {listing.allergens.map((a) => <span key={a} className="badge bg-[#D97D3A]/10 !text-[#D97D3A]">{a}</span>)}
              </div>
            </div>
          )}
          {listing.dietary?.length > 0 && (
            <div>
              <div className="overline mb-2">Dietary</div>
              <div className="flex flex-wrap gap-1.5">
                {listing.dietary.map((d) => <span key={d} className="badge bg-[#6B705C]/10 !text-[#6B705C]"><Leaf className="w-3 h-3" />{d}</span>)}
              </div>
            </div>
          )}

          {listing.description && (
            <div>
              <div className="overline mb-2">Notes</div>
              <p className="text-sm text-[#2A1B24]/90 leading-relaxed">{listing.description}</p>
            </div>
          )}

          {/* PIN — visible to recipient only after approval */}
          {listing.pickup_pin && !isOwner && (
            <div className="card-light !p-5 bg-[#C85A40]/8 border border-[#C85A40]/15">
              <div className="overline">Your pickup PIN</div>
              <div className="font-serif text-4xl mt-1 tracking-widest text-[#C85A40]" data-testid="pickup-pin">{listing.pickup_pin}</div>
              <div className="text-xs text-[#695A62] mt-2">Share with the donor at pickup, then confirm in-app.</div>
            </div>
          )}
          {listing.pickup_pin && isOwner && (
            <div className="card-light !p-5 border border-[#2A1B24]/10">
              <div className="overline">Pickup PIN (give to recipient)</div>
              <div className="font-serif text-4xl mt-1 tracking-widest" data-testid="donor-pin">{listing.pickup_pin}</div>
            </div>
          )}

          <div className="flex flex-wrap gap-3">
            {canRequest && (
              <button onClick={() => setShowRequest(true)} className="btn-primary" data-testid="request-btn">
                <Send className="w-4 h-4" />
                Request this listing
              </button>
            )}
            {user.role === "recipient" && !user.verified && !isOwner && (
              <div className="text-sm text-[#D97D3A] bg-[#D97D3A]/10 px-4 py-3 rounded-2xl">
                Verification pending — claiming locked.
              </div>
            )}
            {isOwner && listing.status === "active" && (
              <button onClick={cancelListing} className="btn-secondary" data-testid="cancel-listing-btn">
                <X className="w-4 h-4" />
                Cancel listing
              </button>
            )}
            <Link to="/requests" className="btn-ghost text-sm">View your requests</Link>
          </div>
        </div>
      </div>

      {/* Request modal */}
      {showRequest && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2A1B24]/70 backdrop-blur-sm p-4 overflow-y-auto" onClick={() => setShowRequest(false)}>
          <div className="bg-[#FDFBF7] rounded-3xl p-8 max-w-md w-full shadow-2xl my-auto" onClick={(e) => e.stopPropagation()} data-testid="request-modal">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="font-serif text-3xl leading-tight">Request listing</h2>
                <p className="text-sm text-[#695A62] mt-1">How much can you collect?</p>
              </div>
              <button onClick={() => setShowRequest(false)} className="btn-ghost !p-2 !px-2 -mr-2 -mt-2" aria-label="Close">
                <X className="w-4 h-4" />
              </button>
            </div>
            <div className="mt-6 space-y-4">
              <div>
                <label className="label">Quantity ({listing.unit})</label>
                <input type="number" min={0.1} max={listing.remaining_quantity} step="0.1" value={qty} onChange={(e) => setQty(e.target.value)} className="input" data-testid="req-qty" />
                <div className="text-xs text-[#695A62] mt-1">Up to {listing.remaining_quantity} {listing.unit} available.</div>
              </div>
              <div>
                <label className="label">Note (optional)</label>
                <textarea rows={3} value={note} onChange={(e) => setNote(e.target.value)} className="input resize-none" placeholder="Pickup vehicle, ETA, anything helpful…" />
              </div>
            </div>
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => setShowRequest(false)} className="btn-secondary" data-testid="req-cancel">Cancel</button>
              <button onClick={submitRequest} disabled={busy} className="btn-primary" data-testid="req-submit">
                {busy ? "Sending…" : "Send request"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ icon: Icon, label, accent }) {
  return (
    <div className={`flex items-start gap-3 ${accent ? "text-[#D97D3A] font-medium" : "text-[#2A1B24]"}`}>
      <Icon className="w-4 h-4 mt-0.5 shrink-0" strokeWidth={1.5} />
      <span>{label}</span>
    </div>
  );
}

function formatRange(a, b) {
  const fmt = (s) => new Date(s).toLocaleString(undefined, { weekday: "short", hour: "2-digit", minute: "2-digit" });
  return `${fmt(a)} → ${fmt(b)}`;
}
