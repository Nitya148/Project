import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import api from "@/lib/api";
import { ArrowUpRight, Sparkles, Inbox, PackageOpen, Compass, Gift, ShieldCheck, Trophy } from "lucide-react";

export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState([]);
  const [listings, setListings] = useState([]);
  const [leaders, setLeaders] = useState([]);
  const [admin, setAdmin] = useState(null);

  useEffect(() => {
    if (user.role === "admin") {
      api.get("/admin/stats").then((r) => setAdmin(r.data)).catch(() => {});
    } else {
      api.get("/impact/me").then((r) => setStats(r.data)).catch(() => {});
      api.get("/requests").then((r) => setRequests(r.data)).catch(() => {});
      api.get("/leaderboard").then((r) => setLeaders(r.data)).catch(() => {});
      if (user.role === "donor") {
        api.get("/listings", { params: { mine: true } }).then((r) => setListings(r.data)).catch(() => {});
      }
    }
  }, [user.role]);

  if (user.role === "admin") return <AdminDashboard stats={admin} />;

  const active = listings.filter((l) => l.status === "active");
  const pendingRequests = requests.filter((r) => r.status === "pending");
  const greeting = user.role === "donor" ? "Welcome back" : "Hello,";
  const sub = user.role === "donor"
    ? "Here's what's happening with your surplus today."
    : (user.verified ? "Nearby food is ready for you." : "Your verification is pending — admin will review shortly.");

  return (
    <div className="space-y-10" data-testid="dashboard">
      <header className="animate-fade-up">
        <span className="overline">{greeting}</span>
        <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">
          {user.org_name || user.name}
        </h1>
        <p className="text-[#695A62] mt-2 max-w-2xl">{sub}</p>
      </header>

      {/* STAT GRID */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Reward points" value={user.points || 0} accent data-testid="stat-points" />
        <StatCard label="Total pickups" value={stats?.total_pickups ?? 0} />
        <StatCard label="Meals contributed" value={stats?.total_meals ?? 0} />
        <StatCard label="CO₂ avoided (kg)" value={stats?.total_co2_kg ?? 0} />
      </div>

      {/* MAIN GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {user.role === "donor" ? (
          <>
            <ActionTile to="/listings/new" icon={PackageOpen} title="Create a listing" desc="Add today's surplus in under a minute." />
            <ActionTile to="/requests" icon={Inbox} title="Pending requests" desc={`${pendingRequests.length} awaiting your review`} badge={pendingRequests.length} />
            <ActionTile to="/rewards" icon={Gift} title="Redeem rewards" desc="Trade your points with local partners." />
          </>
        ) : (
          <>
            <ActionTile to="/discover" icon={Compass} title="Discover nearby" desc="Browse active surplus around you." />
            <ActionTile to="/requests" icon={Inbox} title="My requests" desc={`${pendingRequests.length} pending`} badge={pendingRequests.length} />
            <ActionTile to="/impact" icon={Sparkles} title="See your impact" desc="Meals, kg saved, and CO₂ avoided." />
          </>
        )}
      </div>

      {/* SPLIT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {user.role === "donor" && (
          <div className="card lg:col-span-2 !p-8">
            <div className="flex items-center justify-between">
              <h2 className="font-serif text-2xl">Your active listings</h2>
              <Link to="/listings" className="btn-ghost text-sm">View all</Link>
            </div>
            <div className="mt-6 divide-y divide-[#2A1B24]/5">
              {active.length === 0 && (
                <EmptyState
                  text="No active listings yet."
                  cta={<Link to="/listings/new" className="btn-primary text-sm !py-2.5">Create your first listing <ArrowUpRight className="w-4 h-4" /></Link>}
                />
              )}
              {active.slice(0, 4).map((l) => (
                <Link to={`/listings/${l.id}`} key={l.id} className="block py-4 group" data-testid={`listing-row-${l.id}`}>
                  <div className="flex items-center justify-between gap-4">
                    <div>
                      <div className="font-medium group-hover:text-[#C85A40] transition-colors">{l.name}</div>
                      <div className="text-xs text-[#695A62] uppercase tracking-wider mt-1">
                        {l.quantity} {l.unit} · {l.category.replace("_", " ")}
                      </div>
                    </div>
                    <ArrowUpRight className="w-4 h-4 text-[#695A62] group-hover:text-[#C85A40]" />
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
        {user.role === "recipient" && (
          <div className="card lg:col-span-2 !p-8">
            <h2 className="font-serif text-2xl">Verification status</h2>
            <div className="mt-6 flex items-center gap-4 bg-white rounded-2xl p-4 border border-[#2A1B24]/5">
              <div className={`w-10 h-10 rounded-full flex items-center justify-center ${user.verified ? "bg-[#6B705C]/15 text-[#6B705C]" : "bg-[#D97D3A]/15 text-[#D97D3A]"}`}>
                <ShieldCheck className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="font-medium">
                  {user.verified ? "Organization verified" : "Pending admin verification"}
                </div>
                <div className="text-sm text-[#695A62]">
                  {user.verified
                    ? "You can browse and claim listings."
                    : "An admin will review and verify your organization. You can still browse listings, but claiming is locked."}
                </div>
              </div>
            </div>
            <div className="mt-6">
              <Link to="/discover" className="btn-primary text-sm !py-2.5">
                Browse nearby surplus <ArrowUpRight className="w-4 h-4" />
              </Link>
            </div>
          </div>
        )}

        <div className="card !p-8">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-2xl">Top donors</h2>
            <Trophy className="w-5 h-5 text-[#C85A40]" strokeWidth={1.5} />
          </div>
          <div className="mt-6 space-y-3">
            {leaders.length === 0 && <div className="text-sm text-[#695A62]">No data yet.</div>}
            {leaders.slice(0, 5).map((l, idx) => (
              <div key={l.id} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-3">
                  <span className="font-serif text-xl italic text-[#695A62] w-5">{idx + 1}</span>
                  <span className="font-medium">{l.org_name || l.name}</span>
                </div>
                <span className="text-[#C85A40] font-bold">{l.points} pts</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function AdminDashboard({ stats }) {
  return (
    <div className="space-y-10" data-testid="admin-dashboard">
      <header>
        <span className="overline">Administrator</span>
        <h1 className="font-serif text-4xl sm:text-5xl mt-2">Platform Overview</h1>
      </header>
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard label="Total users" value={stats?.users ?? 0} />
        <StatCard label="Donors" value={stats?.donors ?? 0} />
        <StatCard label="Recipients" value={stats?.recipients ?? 0} />
        <StatCard label="Pending verifications" value={stats?.pending_verifications ?? 0} accent />
        <StatCard label="Active listings" value={stats?.active_listings ?? 0} />
        <StatCard label="Completed pickups" value={stats?.completed_pickups ?? 0} />
      </div>
      <div className="card !p-8">
        <h2 className="font-serif text-2xl">Review verifications</h2>
        <p className="text-[#695A62] mt-2 text-sm">Verify new recipient organizations to let them start claiming food.</p>
        <div className="mt-6"><Link to="/admin" className="btn-primary text-sm !py-2.5">Open Admin Console <ArrowUpRight className="w-4 h-4" /></Link></div>
      </div>
    </div>
  );
}

function StatCard({ label, value, accent }) {
  return (
    <div className={`rounded-3xl p-6 border ${accent ? "bg-[#C85A40] text-white border-transparent" : "bg-white border-[#2A1B24]/5"}`}>
      <div className={`text-xs uppercase tracking-[0.2em] font-bold ${accent ? "text-white/70" : "text-[#695A62]"}`}>{label}</div>
      <div className={`font-serif text-4xl mt-2 ${accent ? "" : "text-[#2A1B24]"}`}>{value}</div>
    </div>
  );
}

function ActionTile({ to, icon: Icon, title, desc, badge }) {
  return (
    <Link to={to} className="card !p-7 hover:-translate-y-1 hover:shadow-[0_12px_32px_rgba(42,27,36,0.08)] transition-all duration-300 group" data-testid={`tile-${title.toLowerCase().replace(/\s+/g, "-")}`}>
      <div className="flex items-start justify-between">
        <div className="w-11 h-11 rounded-full bg-[#C85A40]/10 flex items-center justify-center">
          <Icon className="w-5 h-5 text-[#C85A40]" strokeWidth={1.5} />
        </div>
        {badge > 0 && <span className="badge bg-[#D97D3A]/10 text-[#D97D3A]">{badge}</span>}
      </div>
      <h3 className="font-serif text-2xl mt-6 group-hover:text-[#C85A40] transition-colors">{title}</h3>
      <p className="text-sm text-[#695A62] mt-1.5">{desc}</p>
    </Link>
  );
}

function EmptyState({ text, cta }) {
  return (
    <div className="text-center py-8">
      <p className="text-[#695A62]">{text}</p>
      {cta && <div className="mt-4">{cta}</div>}
    </div>
  );
}
