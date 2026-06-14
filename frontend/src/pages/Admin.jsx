import { useEffect, useState } from "react";
import api from "@/lib/api";
import { toast } from "sonner";
import { Check, ShieldCheck, ShieldOff, Users } from "lucide-react";

export default function Admin() {
  const [stats, setStats] = useState(null);
  const [recipients, setRecipients] = useState([]);
  const [tab, setTab] = useState("pending");

  const load = async () => {
    const [s, r] = await Promise.all([
      api.get("/admin/stats"),
      api.get("/admin/recipients"),
    ]);
    setStats(s.data);
    setRecipients(r.data);
  };
  useEffect(() => { load(); }, []);

  const verify = async (id) => {
    await api.post(`/admin/verify/${id}`);
    toast.success("Recipient verified");
    load();
  };
  const unverify = async (id) => {
    await api.post(`/admin/unverify/${id}`);
    toast("Verification revoked");
    load();
  };

  const filtered = tab === "pending" ? recipients.filter((r) => !r.verified) : recipients.filter((r) => r.verified);

  return (
    <div className="space-y-10" data-testid="admin-page">
      <header>
        <span className="overline">Admin console</span>
        <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">Verification & moderation</h1>
        <p className="text-[#695A62] mt-2">Verify recipient organizations to grant claim access.</p>
      </header>

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <Stat label="Pending verifications" value={stats?.pending_verifications ?? 0} accent />
        <Stat label="Active listings" value={stats?.active_listings ?? 0} />
        <Stat label="Completed pickups" value={stats?.completed_pickups ?? 0} />
        <Stat label="Total users" value={stats?.users ?? 0} />
      </section>

      <div className="flex gap-2">
        <button onClick={() => setTab("pending")} className={`px-4 py-2 rounded-full text-sm font-medium ${tab === "pending" ? "bg-[#2A1B24] text-[#FDFBF7]" : "bg-[#F4EFE6] text-[#2A1B24]/70"}`} data-testid="admin-tab-pending">
          Pending ({recipients.filter((r) => !r.verified).length})
        </button>
        <button onClick={() => setTab("verified")} className={`px-4 py-2 rounded-full text-sm font-medium ${tab === "verified" ? "bg-[#2A1B24] text-[#FDFBF7]" : "bg-[#F4EFE6] text-[#2A1B24]/70"}`} data-testid="admin-tab-verified">
          Verified ({recipients.filter((r) => r.verified).length})
        </button>
      </div>

      {filtered.length === 0 ? (
        <div className="card !p-12 text-center">
          <Users className="w-7 h-7 mx-auto text-[#C85A40]" />
          <h2 className="font-serif text-2xl mt-3">No {tab} recipients</h2>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((r) => (
            <div key={r.id} className="card-light flex items-center justify-between gap-4 flex-wrap" data-testid={`recipient-${r.id}`}>
              <div>
                <div className="text-xs uppercase tracking-wider text-[#695A62]">{r.org_type?.replace("_", " ") || "—"}</div>
                <div className="font-serif text-xl mt-1">{r.org_name || r.name}</div>
                <div className="text-sm text-[#695A62]">{r.email} {r.phone && `· ${r.phone}`}</div>
                {r.address && <div className="text-sm text-[#695A62]">{r.address}</div>}
              </div>
              <div className="flex items-center gap-2">
                {r.verified ? (
                  <>
                    <span className="badge bg-[#6B705C]/15 text-[#6B705C]"><ShieldCheck className="w-3 h-3" /> verified</span>
                    <button onClick={() => unverify(r.id)} className="btn-secondary !py-2 !px-3 text-sm" data-testid={`unverify-${r.id}`}>
                      <ShieldOff className="w-4 h-4" /> Revoke
                    </button>
                  </>
                ) : (
                  <button onClick={() => verify(r.id)} className="btn-primary !py-2 !px-3 text-sm" data-testid={`verify-${r.id}`}>
                    <Check className="w-4 h-4" /> Verify
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, accent }) {
  return (
    <div className={`rounded-3xl p-6 border ${accent ? "bg-[#C85A40] text-white border-transparent" : "bg-white border-[#2A1B24]/5"}`}>
      <div className={`text-xs uppercase tracking-[0.2em] font-bold ${accent ? "text-white/70" : "text-[#695A62]"}`}>{label}</div>
      <div className="font-serif text-4xl mt-2">{value}</div>
    </div>
  );
}
