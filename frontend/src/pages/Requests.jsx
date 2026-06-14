import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { Check, X, Inbox, ArrowUpRight, KeyRound } from "lucide-react";

export default function Requests() {
  const { user, refreshMe } = useAuth();
  const [items, setItems] = useState([]);
  const [tab, setTab] = useState(user.role === "donor" ? "incoming" : "outgoing");
  const [loading, setLoading] = useState(true);
  const [confirmFor, setConfirmFor] = useState(null);
  const [pin, setPin] = useState("");
  const [busy, setBusy] = useState(false);

  const load = async () => {
    setLoading(true);
    const { data } = await api.get("/requests", { params: { role: tab } });
    setItems(data);
    setLoading(false);
  };

  useEffect(() => {
    load(); /* eslint-disable-next-line */
  }, [tab]);

  const approve = async (r) => {
    await api.post(`/requests/${r.id}/approve`);
    toast.success("Request approved. Recipient notified.");
    load();
  };
  const reject = async (r) => {
    await api.post(`/requests/${r.id}/reject`);
    toast("Request rejected.");
    load();
  };
  const confirmPickup = async () => {
    if (!confirmFor) return;
    setBusy(true);
    try {
      const { data } = await api.post(`/requests/${confirmFor.id}/confirm`, { pin });
      toast.success(`Pickup confirmed. ${data.points_awarded ? `+${data.points_awarded} points awarded.` : ""}`);
      setConfirmFor(null);
      setPin("");
      refreshMe();
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-8" data-testid="requests-page">
      <header>
        <span className="overline">Requests</span>
        <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">
          {user.role === "donor" ? "Pickup requests" : "Your claims"}
        </h1>
        <p className="text-[#695A62] mt-2">
          {user.role === "donor" ? "Approve or reject incoming requests for your listings." : "Track your requested pickups."}
        </p>
      </header>

      {user.role !== "admin" && (
        <div className="flex gap-2 flex-wrap">
          {user.role === "donor" && <Tab v="incoming" current={tab} onClick={setTab}>From recipients</Tab>}
          <Tab v="outgoing" current={tab} onClick={setTab}>
            {user.role === "donor" ? "(You'd not have any)" : "My requests"}
          </Tab>
        </div>
      )}

      {loading ? (
        <div className="text-center py-20 text-[#695A62]">Loading…</div>
      ) : items.length === 0 ? (
        <div className="card text-center !p-16">
          <Inbox className="w-8 h-8 mx-auto text-[#C85A40]" strokeWidth={1.5} />
          <h2 className="font-serif text-2xl mt-4">No requests yet</h2>
          <p className="text-[#695A62] mt-2">
            {user.role === "donor"
              ? "Once recipients claim your listings, they'll show up here."
              : "Browse the discover feed and claim a listing to get started."}
          </p>
          {user.role === "recipient" && (
            <Link to="/discover" className="btn-primary text-sm !py-2.5 mt-6 inline-flex">
              Browse listings <ArrowUpRight className="w-4 h-4" />
            </Link>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((r) => (
            <div key={r.id} className="card-light flex flex-wrap items-center gap-4 justify-between" data-testid={`request-row-${r.id}`}>
              <div className="flex-1 min-w-0">
                <div className="text-xs uppercase tracking-wider text-[#695A62]">
                  {user.role === "donor" ? r.recipient_name : r.donor_name}
                </div>
                <Link to={`/listings/${r.listing_id}`} className="font-serif text-xl mt-1 leading-tight hover:text-[#C85A40] transition-colors block">
                  {r.listing_name}
                </Link>
                <div className="text-sm text-[#695A62] mt-1">
                  {r.requested_quantity} {r.unit} · {new Date(r.created_at).toLocaleString()}
                </div>
                {r.note && <div className="text-sm mt-2 italic text-[#695A62]">&ldquo;{r.note}&rdquo;</div>}
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <StatusBadge status={r.status} />
                {tab === "incoming" && r.status === "pending" && (
                  <>
                    <button onClick={() => reject(r)} className="btn-secondary !py-2 !px-3 text-sm" data-testid={`reject-${r.id}`}>
                      <X className="w-4 h-4" /> Reject
                    </button>
                    <button onClick={() => approve(r)} className="btn-primary !py-2 !px-3 text-sm" data-testid={`approve-${r.id}`}>
                      <Check className="w-4 h-4" /> Approve
                    </button>
                  </>
                )}
                {tab === "outgoing" && r.status === "approved" && (
                  <button onClick={() => setConfirmFor(r)} className="btn-primary !py-2 !px-3 text-sm" data-testid={`confirm-${r.id}`}>
                    <KeyRound className="w-4 h-4" /> Confirm pickup
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* PIN modal */}
      {confirmFor && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#2A1B24]/40 p-4" onClick={() => setConfirmFor(null)}>
          <div className="bg-[#FDFBF7] rounded-3xl p-8 max-w-sm w-full" onClick={(e) => e.stopPropagation()} data-testid="confirm-modal">
            <KeyRound className="w-7 h-7 text-[#C85A40]" />
            <h2 className="font-serif text-2xl mt-4">Confirm pickup</h2>
            <p className="text-sm text-[#695A62] mt-1">Enter the 4-digit PIN the donor provided.</p>
            <input
              autoFocus
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="input mt-4 text-center text-2xl tracking-[0.5em] font-serif"
              maxLength={4}
              data-testid="confirm-pin-input"
            />
            <div className="mt-6 flex justify-end gap-2">
              <button onClick={() => setConfirmFor(null)} className="btn-secondary">Cancel</button>
              <button onClick={confirmPickup} disabled={busy || pin.length < 4} className="btn-primary" data-testid="confirm-submit">
                {busy ? "Confirming…" : "Confirm"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function Tab({ v, current, onClick, children }) {
  return (
    <button
      onClick={() => onClick(v)}
      data-testid={`req-tab-${v}`}
      className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
        current === v ? "bg-[#2A1B24] text-[#FDFBF7]" : "bg-[#F4EFE6] text-[#2A1B24]/70 hover:text-[#2A1B24]"
      }`}
    >
      {children}
    </button>
  );
}

function StatusBadge({ status }) {
  const map = {
    pending: "bg-[#D97D3A]/10 text-[#D97D3A]",
    approved: "bg-[#6B705C]/15 text-[#6B705C]",
    completed: "bg-[#2A1B24] text-[#FDFBF7]",
    rejected: "bg-[#695A62]/10 text-[#695A62]",
    cancelled: "bg-[#695A62]/10 text-[#695A62]",
  };
  return <span className={`badge ${map[status] || ""}`}>{status}</span>;
}
