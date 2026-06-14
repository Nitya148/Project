import { useEffect, useState } from "react";
import api from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { Sparkles, TrendingUp, Leaf, Users } from "lucide-react";
import { LineChart, Line, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

export default function Impact() {
  const { user } = useAuth();
  const [me, setMe] = useState(null);
  const [global, setGlobal] = useState(null);
  const [leaders, setLeaders] = useState([]);

  useEffect(() => {
    Promise.all([api.get("/impact/me"), api.get("/impact/global"), api.get("/leaderboard")]).then(([a, b, c]) => {
      setMe(a.data);
      setGlobal(b.data);
      setLeaders(c.data);
    });
  }, []);

  return (
    <div className="space-y-10" data-testid="impact-page">
      <header>
        <span className="overline">Impact dashboard</span>
        <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">
          Every pickup, <em className="text-[#C85A40]">a measurable good.</em>
        </h1>
      </header>

      {/* Personal stats */}
      <section>
        <h2 className="font-serif text-2xl mb-4">{user.role === "admin" ? "Network impact" : "Your contribution"}</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <BigStat icon={Sparkles} label="Pickups" value={me?.total_pickups ?? 0} accent />
          <BigStat icon={TrendingUp} label="Meals served" value={me?.total_meals ?? 0} />
          <BigStat icon={Leaf} label="kg of food" value={me?.total_kg ?? 0} />
          <BigStat icon={Leaf} label="kg CO₂ avoided" value={me?.total_co2_kg ?? 0} />
        </div>
      </section>

      {/* Chart */}
      <section className="card !p-8">
        <h2 className="font-serif text-2xl">Meals over time</h2>
        <div className="h-72 mt-6">
          {(me?.by_day || []).length === 0 ? (
            <div className="h-full flex items-center justify-center text-[#695A62] text-sm">
              No completed pickups yet — your chart will appear here.
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={me.by_day} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(42,27,36,0.08)" />
                <XAxis dataKey="date" stroke="#695A62" fontSize={12} tickLine={false} />
                <YAxis stroke="#695A62" fontSize={12} tickLine={false} />
                <Tooltip contentStyle={{ background: "#FDFBF7", border: "1px solid rgba(42,27,36,0.1)", borderRadius: 16 }} />
                <Line type="monotone" dataKey="meals" stroke="#C85A40" strokeWidth={2.5} dot={{ fill: "#C85A40", r: 4 }} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </section>

      {/* Global + Leaderboard */}
      <section className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card !p-8 lg:col-span-2">
          <span className="overline">Network total</span>
          <h2 className="font-serif text-2xl mt-2">Together we&apos;ve rescued</h2>
          <div className="grid grid-cols-3 gap-6 mt-6">
            <div>
              <div className="font-serif text-4xl text-[#C85A40]">{(global?.total_meals ?? 0).toLocaleString()}</div>
              <div className="text-xs uppercase tracking-wider text-[#695A62] mt-1">meals</div>
            </div>
            <div>
              <div className="font-serif text-4xl">{(global?.total_kg ?? 0).toLocaleString()}</div>
              <div className="text-xs uppercase tracking-wider text-[#695A62] mt-1">kg of food</div>
            </div>
            <div>
              <div className="font-serif text-4xl">{(global?.total_co2_kg ?? 0).toLocaleString()}</div>
              <div className="text-xs uppercase tracking-wider text-[#695A62] mt-1">kg CO₂ avoided</div>
            </div>
          </div>
        </div>

        <div className="card !p-8">
          <div className="flex items-center justify-between">
            <h2 className="font-serif text-xl">Top donors</h2>
            <Users className="w-5 h-5 text-[#C85A40]" />
          </div>
          <div className="mt-4 space-y-3 text-sm">
            {leaders.length === 0 && <div className="text-[#695A62]">No data yet.</div>}
            {leaders.slice(0, 7).map((l, i) => (
              <div key={l.id} className="flex items-center justify-between">
                <span className="flex items-center gap-3">
                  <span className="font-serif italic text-[#695A62] w-5">{i + 1}</span>
                  <span className="font-medium">{l.org_name || l.name}</span>
                </span>
                <span className="text-[#C85A40] font-bold">{l.points} pts</span>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}

function BigStat({ icon: Icon, label, value, accent }) {
  return (
    <div className={`rounded-3xl p-6 border ${accent ? "bg-[#C85A40] text-white border-transparent" : "bg-white border-[#2A1B24]/5"}`}>
      <div className="flex items-center justify-between">
        <Icon className={`w-5 h-5 ${accent ? "text-white" : "text-[#C85A40]"}`} strokeWidth={1.5} />
      </div>
      <div className={`font-serif text-4xl mt-4 ${accent ? "" : "text-[#2A1B24]"}`}>{value}</div>
      <div className={`text-xs uppercase tracking-[0.2em] mt-1 ${accent ? "text-white/70" : "text-[#695A62]"}`}>{label}</div>
    </div>
  );
}
