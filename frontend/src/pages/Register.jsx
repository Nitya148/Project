import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { ArrowLeft, ArrowUpRight, Utensils, HandHeart } from "lucide-react";

const ORG_TYPES = {
  donor: [
    { v: "restaurant", l: "Restaurant" },
    { v: "cafe", l: "Café" },
    { v: "bakery", l: "Bakery" },
    { v: "other", l: "Other food business" },
  ],
  recipient: [
    { v: "ngo", l: "NGO / Charity" },
    { v: "community_kitchen", l: "Community Kitchen" },
    { v: "food_bank", l: "Food Bank" },
    { v: "other", l: "Other" },
  ],
};

export default function Register() {
  const { register, error } = useAuth();
  const nav = useNavigate();
  const [role, setRole] = useState("donor");
  const [form, setForm] = useState({
    email: "",
    password: "",
    name: "",
    org_name: "",
    org_type: "restaurant",
    phone: "",
    address: "",
    lat: 40.7081,
    lng: -73.9571,
  });
  const [loading, setLoading] = useState(false);

  const onChange = (k) => (e) => setForm({ ...form, [k]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const ok = await register({ ...form, role });
    setLoading(false);
    if (ok) nav("/dashboard");
  };

  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2" data-testid="register-page">
      <div className="flex items-center justify-center p-8 md:p-16 bg-[#FDFBF7] order-2 md:order-1">
        <div className="w-full max-w-md">
          <Link to="/" className="btn-ghost !px-0 text-sm" data-testid="back-home-register">
            <ArrowLeft className="w-4 h-4" /> Back home
          </Link>
          <h1 className="font-serif text-4xl mt-6 leading-tight">Create your account</h1>
          <p className="text-[#695A62] mt-2">Join the food rescue network in minutes.</p>

          <div className="mt-6 grid grid-cols-2 gap-3">
            <RoleBtn active={role === "donor"} onClick={() => { setRole("donor"); setForm({ ...form, org_type: "restaurant" }); }} icon={Utensils} label="I'm a Donor" sub="Restaurant, café, bakery" testid="role-donor" />
            <RoleBtn active={role === "recipient"} onClick={() => { setRole("recipient"); setForm({ ...form, org_type: "ngo" }); }} icon={HandHeart} label="I'm a Recipient" sub="NGO, kitchen, food bank" testid="role-recipient" />
          </div>

          <form onSubmit={submit} className="mt-6 space-y-4" data-testid="register-form">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Your name</label>
                <input required value={form.name} onChange={onChange("name")} className="input" data-testid="reg-name" />
              </div>
              <div>
                <label className="label">Organization</label>
                <input required value={form.org_name} onChange={onChange("org_name")} className="input" data-testid="reg-org" />
              </div>
            </div>
            <div>
              <label className="label">Organization type</label>
              <select value={form.org_type} onChange={onChange("org_type")} className="input" data-testid="reg-orgtype">
                {ORG_TYPES[role].map((o) => (
                  <option key={o.v} value={o.v}>{o.l}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Email</label>
              <input type="email" required value={form.email} onChange={onChange("email")} className="input" data-testid="reg-email" />
            </div>
            <div>
              <label className="label">Password</label>
              <input type="password" required minLength={6} value={form.password} onChange={onChange("password")} className="input" data-testid="reg-password" />
            </div>
            <div>
              <label className="label">Pickup address</label>
              <input value={form.address} onChange={onChange("address")} className="input" placeholder="Street, City" data-testid="reg-address" />
            </div>

            {role === "recipient" && (
              <div className="text-xs text-[#695A62] bg-[#F4EFE6] rounded-2xl px-4 py-3">
                Recipient organizations require admin verification before they can claim food. We&apos;ll review your account shortly.
              </div>
            )}
            {error && <div className="text-sm text-[#C85A40] bg-[#C85A40]/10 rounded-2xl px-4 py-3" data-testid="reg-error">{error}</div>}

            <button type="submit" disabled={loading} className="btn-primary w-full !py-3.5" data-testid="reg-submit">
              {loading ? "Creating account…" : "Create account"}
              <ArrowUpRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-6 text-sm text-[#695A62]">
            Already have an account?{" "}
            <Link to="/login" className="text-[#C85A40] font-medium underline-offset-4 hover:underline">Sign in</Link>
          </div>
        </div>
      </div>

      <div className="hidden md:block relative order-1 md:order-2">
        <img src="https://images.unsplash.com/photo-1593113565687-cc2f464d1f2e?auto=format&fit=crop&q=80&w=1400" alt="" className="absolute inset-0 w-full h-full object-cover" />
        <div className="absolute inset-0 bg-gradient-to-tl from-[#2A1B24]/70 via-[#2A1B24]/20 to-transparent"></div>
        <div className="absolute bottom-12 left-12 right-12 text-white">
          <span className="overline !text-[#FDFBF7]/80">Hello, neighbor</span>
          <h2 className="font-serif text-5xl mt-4 leading-tight">
            Surplus is just dinner <em className="text-[#D97D3A]">waiting for the right hands.</em>
          </h2>
        </div>
      </div>
    </div>
  );
}

function RoleBtn({ active, onClick, icon: Icon, label, sub, testid }) {
  return (
    <button
      type="button"
      onClick={onClick}
      data-testid={testid}
      className={`text-left rounded-2xl p-4 border-2 transition-all ${
        active ? "border-[#C85A40] bg-[#C85A40]/5" : "border-[#2A1B24]/10 bg-white hover:bg-[#F4EFE6]"
      }`}
    >
      <Icon className={`w-5 h-5 ${active ? "text-[#C85A40]" : "text-[#2A1B24]"}`} strokeWidth={1.5} />
      <div className="font-medium mt-2 text-sm">{label}</div>
      <div className="text-xs text-[#695A62]">{sub}</div>
    </button>
  );
}
