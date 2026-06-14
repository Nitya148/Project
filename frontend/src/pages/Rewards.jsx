import { useEffect, useState } from "react";
import api, { formatApiError } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { toast } from "sonner";
import { Gift, Sparkles, Copy, Check } from "lucide-react";

export default function Rewards() {
  const { user, refreshMe } = useAuth();
  const [vouchers, setVouchers] = useState([]);
  const [redemptions, setRedemptions] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [busy, setBusy] = useState(null);
  const [copied, setCopied] = useState(null);

  const load = async () => {
    const [v, r, t] = await Promise.all([
      api.get("/vouchers"),
      api.get("/redemptions"),
      api.get("/points/transactions"),
    ]);
    setVouchers(v.data);
    setRedemptions(r.data);
    setTransactions(t.data);
  };

  useEffect(() => { load(); }, []);

  const redeem = async (v) => {
    if ((user.points || 0) < v.points_cost) {
      toast.error("Not enough points yet.");
      return;
    }
    if (!window.confirm(`Redeem ${v.title} for ${v.points_cost} points?`)) return;
    setBusy(v.id);
    try {
      const { data } = await api.post("/vouchers/redeem", { voucher_id: v.id });
      toast.success(`Redeemed! Code: ${data.code}`);
      refreshMe();
      load();
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusy(null);
    }
  };

  const copy = (code) => {
    navigator.clipboard.writeText(code);
    setCopied(code);
    setTimeout(() => setCopied(null), 1500);
  };

  return (
    <div className="space-y-10" data-testid="rewards-page">
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <span className="overline">Reward catalog</span>
          <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">
            Points that <em className="text-[#C85A40]">give back.</em>
          </h1>
          <p className="text-[#695A62] mt-2 max-w-xl">Redeem your rescue points with our local partners.</p>
        </div>
        <div className="rounded-3xl bg-[#C85A40] text-white p-6 min-w-[200px]">
          <div className="text-xs uppercase tracking-[0.2em] text-white/70">Your balance</div>
          <div className="font-serif text-5xl mt-1" data-testid="points-balance">{user.points || 0}</div>
          <div className="text-xs text-white/70 mt-1">reward points</div>
        </div>
      </header>

      <section>
        <h2 className="font-serif text-2xl mb-4">Available vouchers</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {vouchers.map((v) => {
            const can = (user.points || 0) >= v.points_cost;
            return (
              <div key={v.id} className="card !p-0 overflow-hidden" data-testid={`voucher-${v.id}`}>
                <div className="aspect-[4/3] bg-[#EAE2D3] relative">
                  {v.image_url && <img src={v.image_url} alt={v.title} className="w-full h-full object-cover" />}
                  <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-bold text-[#C85A40]">
                    {v.points_cost} pts
                  </div>
                </div>
                <div className="p-6">
                  <div className="text-xs uppercase tracking-[0.18em] text-[#695A62]">{v.partner}</div>
                  <h3 className="font-serif text-xl mt-1.5 leading-tight">{v.title}</h3>
                  <p className="text-sm text-[#695A62] mt-2 leading-relaxed">{v.description}</p>
                  <button
                    onClick={() => redeem(v)}
                    disabled={!can || busy === v.id}
                    className={`mt-4 w-full ${can ? "btn-primary" : "btn-secondary opacity-60"}`}
                    data-testid={`redeem-${v.id}`}
                  >
                    {busy === v.id ? "Redeeming…" : can ? (<><Sparkles className="w-4 h-4" /> Redeem</>) : `Need ${v.points_cost - (user.points || 0)} more`}
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {redemptions.length > 0 && (
        <section>
          <h2 className="font-serif text-2xl mb-4">Your redemptions</h2>
          <div className="space-y-3">
            {redemptions.map((r) => (
              <div key={r.id} className="card-light flex items-center justify-between gap-4 flex-wrap" data-testid={`redemption-${r.id}`}>
                <div>
                  <div className="text-xs uppercase tracking-wider text-[#695A62]">{r.partner}</div>
                  <div className="font-medium mt-1">{r.voucher_title}</div>
                  <div className="text-xs text-[#695A62] mt-1">{new Date(r.created_at).toLocaleString()}</div>
                </div>
                <button onClick={() => copy(r.code)} className="flex items-center gap-2 bg-[#2A1B24] text-[#FDFBF7] px-4 py-2 rounded-full font-mono text-sm">
                  {r.code}
                  {copied === r.code ? <Check className="w-4 h-4" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>
            ))}
          </div>
        </section>
      )}

      {transactions.length > 0 && (
        <section>
          <h2 className="font-serif text-2xl mb-4">Point history</h2>
          <div className="divide-y divide-[#2A1B24]/5 bg-white rounded-3xl border border-[#2A1B24]/5">
            {transactions.slice(0, 20).map((t) => (
              <div key={t.id} className="flex items-center justify-between px-6 py-4">
                <div>
                  <div className="font-medium">{t.reason}</div>
                  <div className="text-xs text-[#695A62] mt-0.5">{new Date(t.created_at).toLocaleString()}</div>
                </div>
                <div className={`font-bold ${t.amount > 0 ? "text-[#6B705C]" : "text-[#C85A40]"}`}>
                  {t.amount > 0 ? "+" : ""}{t.amount}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {vouchers.length === 0 && (
        <div className="card text-center !p-16">
          <Gift className="w-8 h-8 mx-auto text-[#C85A40]" strokeWidth={1.5} />
          <h2 className="font-serif text-2xl mt-4">Catalog coming soon</h2>
        </div>
      )}
    </div>
  );
}
