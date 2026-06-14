import { Link } from "react-router-dom";
import { ArrowUpRight, Leaf, Sparkles, MapPin, Gift, Clock, ShieldCheck } from "lucide-react";
import { useEffect, useState } from "react";
import api from "@/lib/api";

export default function Landing() {
  const [stats, setStats] = useState({ total_meals: 0, total_kg: 0, total_co2_kg: 0 });

  useEffect(() => {
    api.get("/impact/global").then((r) => setStats(r.data)).catch(() => {});
  }, []);

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-[#2A1B24]" data-testid="landing-page">
      {/* NAV */}
      <header className="sticky top-0 z-40 backdrop-blur-xl bg-[#FDFBF7]/80 border-b border-[#2A1B24]/5">
        <div className="max-w-7xl mx-auto px-6 md:px-12 h-20 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2" data-testid="landing-logo">
            <div className="w-9 h-9 rounded-full bg-[#C85A40] flex items-center justify-center text-white font-serif italic text-xl leading-none">R</div>
            <span className="font-serif text-2xl tracking-tight">
              Re<span className="italic text-[#C85A40]">Plate</span>
            </span>
          </Link>
          <nav className="hidden md:flex items-center gap-2">
            <a href="#how" className="btn-ghost text-sm">How it works</a>
            <a href="#impact" className="btn-ghost text-sm">Impact</a>
            <a href="#rewards" className="btn-ghost text-sm">Rewards</a>
          </nav>
          <div className="flex items-center gap-2">
            <Link to="/login" className="btn-ghost text-sm" data-testid="landing-login-link">Sign in</Link>
            <Link to="/register" className="btn-primary text-sm !py-2.5 !px-5" data-testid="landing-cta-register">
              Join the network
              <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 -z-10">
          <img
            src="https://images.unsplash.com/photo-1495107334309-fcf20504a5ab?auto=format&fit=crop&q=80&w=1800"
            alt=""
            className="w-full h-full object-cover opacity-40"
          />
          <div className="absolute inset-0 bg-gradient-to-b from-[#FDFBF7]/40 via-[#FDFBF7]/70 to-[#FDFBF7]"></div>
        </div>

        <div className="max-w-7xl mx-auto px-6 md:px-12 pt-20 md:pt-32 pb-20 md:pb-40">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-10 items-end">
            <div className="md:col-span-8 animate-fade-up">
              <span className="overline" data-testid="hero-overline">Real-time food rescue · neighborhood network</span>
              <h1 className="font-serif text-5xl sm:text-7xl md:text-8xl leading-[0.95] tracking-tight font-medium mt-6 text-[#2A1B24]">
                Surplus food, <br />
                <span className="italic text-[#C85A40]">redistributed</span> <br className="hidden sm:block" />
                before it&apos;s gone.
              </h1>
              <p className="mt-8 max-w-xl text-lg text-[#695A62] leading-relaxed">
                Restaurants, cafés and bakeries list their daily surplus.
                Verified community kitchens, food banks and shelters claim
                it in real time. Everyone earns points for what they save.
              </p>
              <div className="mt-10 flex flex-wrap items-center gap-3">
                <Link to="/register" className="btn-primary text-base" data-testid="hero-cta-primary">
                  Start exchanging
                  <ArrowUpRight className="w-4 h-4" />
                </Link>
                <Link to="/login" className="btn-secondary text-base" data-testid="hero-cta-secondary">
                  I already have an account
                </Link>
              </div>
            </div>

            <div className="md:col-span-4 animate-fade-up delay-200">
              <div className="card-light !p-8 backdrop-blur-md bg-white/70">
                <div className="overline">Live network</div>
                <div className="font-serif text-4xl mt-2">
                  <span className="text-[#C85A40] italic">{(stats.total_meals || 0).toLocaleString()}</span>{" "}
                  <span className="text-[#2A1B24]">meals</span>
                </div>
                <div className="text-sm text-[#695A62] mt-1">
                  diverted from waste — and counting
                </div>
                <div className="mt-6 grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-2xl font-serif">{(stats.total_kg || 0).toLocaleString()}</div>
                    <div className="text-xs text-[#695A62] uppercase tracking-wider">kg saved</div>
                  </div>
                  <div>
                    <div className="text-2xl font-serif">{(stats.total_co2_kg || 0).toLocaleString()}</div>
                    <div className="text-xs text-[#695A62] uppercase tracking-wider">kg CO₂ avoided</div>
                  </div>
                </div>
                <div className="mt-5 pt-5 border-t border-[#2A1B24]/10 flex items-center gap-2 text-xs text-[#695A62]">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#C85A40] opacity-60"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#C85A40]"></span>
                  </span>
                  <span>{stats.total_pickups || 0} confirmed pickups · {stats.by_day?.length || 0} days of activity</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="max-w-2xl">
            <span className="overline">How it works</span>
            <h2 className="font-serif text-4xl sm:text-5xl leading-tight mt-4">
              A simple loop, designed for the <em className="text-[#C85A40]">last mile</em> of food.
            </h2>
          </div>

          <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
            {[
              {
                icon: PackageStep,
                step: "01",
                title: "Donors list surplus",
                body: "In under 30 seconds, a restaurant adds today's surplus — quantity, pickup window, expiry.",
              },
              {
                icon: MapPin,
                step: "02",
                title: "Recipients discover nearby",
                body: "Verified NGOs and community kitchens see it on a live, location-aware feed.",
              },
              {
                icon: ShieldCheck,
                step: "03",
                title: "Pickup. Points. Impact.",
                body: "A PIN confirms pickup. Donors earn reward points; everyone sees the impact in real time.",
              },
            ].map((s, i) => (
              <div key={s.step} className={`card !p-8 animate-fade-up delay-${(i + 1) * 100}`}>
                <div className="flex items-center justify-between">
                  <s.icon className="w-7 h-7 text-[#C85A40]" strokeWidth={1.5} />
                  <span className="font-serif text-2xl text-[#695A62] italic">{s.step}</span>
                </div>
                <h3 className="font-serif text-2xl mt-6">{s.title}</h3>
                <p className="text-[#695A62] mt-3 leading-relaxed">{s.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* IMPACT STRIP */}
      <section id="impact" className="bg-[#2A1B24] text-[#FDFBF7] py-24">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <span className="overline !text-[#D97D3A]">Why it matters</span>
          <div className="mt-6 grid grid-cols-1 md:grid-cols-12 gap-8 items-end">
            <h2 className="md:col-span-7 font-serif text-4xl sm:text-5xl leading-tight">
              One third of the food we grow is never eaten.<br />
              <em className="text-[#D97D3A]">We&apos;re changing that, plate by plate.</em>
            </h2>
            <p className="md:col-span-5 text-[#FDFBF7]/70 leading-relaxed">
              Every confirmed pickup avoids landfill methane, feeds someone in need, and earns the donor reward points redeemable with our local partners.
            </p>
          </div>

          <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-6">
            {[
              { v: "5 km", l: "Default discovery radius" },
              { v: "< 2 min", l: "From list to discoverable" },
              { v: "12 mo", l: "Reward point validity" },
              { v: "24/7", l: "Real-time matching" },
            ].map((s) => (
              <div key={s.l} className="border-t border-[#FDFBF7]/15 pt-6">
                <div className="font-serif text-4xl text-[#D97D3A]">{s.v}</div>
                <div className="text-sm text-[#FDFBF7]/60 mt-2">{s.l}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* REWARDS */}
      <section id="rewards" className="py-24 md:py-32">
        <div className="max-w-7xl mx-auto px-6 md:px-12 grid grid-cols-1 md:grid-cols-12 gap-10 items-center">
          <div className="md:col-span-6">
            <img
              src="https://images.unsplash.com/photo-1497935586351-b67a49e012bf?auto=format&fit=crop&q=80&w=1200"
              alt="Reward partner"
              className="rounded-3xl w-full object-cover aspect-[4/5]"
            />
          </div>
          <div className="md:col-span-6">
            <span className="overline">Reward Program</span>
            <h2 className="font-serif text-4xl sm:text-5xl leading-tight mt-4">
              Points that come back as <em className="text-[#C85A40]">a warm cup of coffee.</em>
            </h2>
            <p className="text-[#695A62] mt-6 leading-relaxed max-w-lg">
              Donors earn points on every confirmed pickup, scaled by quantity and category — redeemable with local partner businesses.
            </p>
            <div className="mt-10 space-y-4">
              {[
                { i: Gift, t: "Curated partner vouchers", d: "Coffee shops, grocers, bakeries — local-first." },
                { i: Clock, t: "Points valid for 12 months", d: "Plenty of time to redeem on what matters." },
                { i: Leaf, t: "Bonus for high-impact rescues", d: "Larger surplus and prepared meals earn more." },
              ].map((it) => (
                <div key={it.t} className="flex items-start gap-4">
                  <div className="w-10 h-10 rounded-full bg-[#F4EFE6] flex items-center justify-center shrink-0">
                    <it.i className="w-5 h-5 text-[#C85A40]" strokeWidth={1.5} />
                  </div>
                  <div>
                    <div className="font-medium">{it.t}</div>
                    <div className="text-sm text-[#695A62]">{it.d}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="pb-32">
        <div className="max-w-7xl mx-auto px-6 md:px-12">
          <div className="bg-[#F4EFE6] rounded-[2.5rem] p-10 md:p-20 text-center">
            <Sparkles className="w-8 h-8 text-[#C85A40] mx-auto" strokeWidth={1.5} />
            <h2 className="font-serif text-4xl sm:text-6xl mt-6 leading-tight">
              The food is ready.<br />
              <em className="text-[#C85A40]">Are you?</em>
            </h2>
            <div className="mt-10 flex flex-wrap justify-center gap-3">
              <Link to="/register" className="btn-primary text-base" data-testid="footer-cta-register">
                Create your account
                <ArrowUpRight className="w-4 h-4" />
              </Link>
              <Link to="/login" className="btn-secondary text-base">
                Sign in
              </Link>
            </div>
          </div>
        </div>
      </section>

      <footer className="border-t border-[#2A1B24]/10 py-10 text-center text-sm text-[#695A62]">
        <span className="font-serif italic">RePlate</span> · Built with care for the food we&apos;d otherwise lose.
      </footer>
    </div>
  );
}

function PackageStep(props) {
  return <Gift {...props} />;
}
