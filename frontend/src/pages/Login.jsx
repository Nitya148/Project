import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { ArrowLeft, ArrowUpRight } from "lucide-react";

export default function Login() {
  const { login, error } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const nav = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    const ok = await login(email, password);
    setLoading(false);
    if (ok) nav("/dashboard");
  };

  const fill = (em, pw) => {
    setEmail(em);
    setPassword(pw);
  };

  return (
    <div className="min-h-screen grid grid-cols-1 md:grid-cols-2" data-testid="login-page">
      <div className="hidden md:block relative">
        <img
          src="https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=1400"
          alt=""
          className="absolute inset-0 w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-tr from-[#2A1B24]/70 via-[#2A1B24]/20 to-transparent"></div>
        <div className="absolute bottom-12 left-12 right-12 text-white">
          <span className="overline !text-[#FDFBF7]/80">Welcome back</span>
          <h2 className="font-serif text-5xl mt-4 leading-tight">
            Tonight&apos;s surplus is <em className="text-[#D97D3A]">already on the table.</em>
          </h2>
        </div>
      </div>

      <div className="flex items-center justify-center p-8 md:p-16 bg-[#FDFBF7]">
        <div className="w-full max-w-md">
          <Link to="/" className="btn-ghost !px-0 text-sm" data-testid="back-home">
            <ArrowLeft className="w-4 h-4" /> Back home
          </Link>
          <h1 className="font-serif text-4xl mt-6 leading-tight">Sign in</h1>
          <p className="text-[#695A62] mt-2">Continue your food rescue work.</p>

          <form onSubmit={submit} className="mt-10 space-y-4" data-testid="login-form">
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="input"
                placeholder="you@kitchen.com"
                data-testid="login-email"
              />
            </div>
            <div>
              <label className="label">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="input"
                placeholder="••••••••"
                data-testid="login-password"
              />
            </div>
            {error && (
              <div className="text-sm text-[#C85A40] bg-[#C85A40]/10 rounded-2xl px-4 py-3" data-testid="login-error">
                {error}
              </div>
            )}
            <button type="submit" disabled={loading} className="btn-primary w-full !py-3.5" data-testid="login-submit">
              {loading ? "Signing in…" : "Sign in"}
              <ArrowUpRight className="w-4 h-4" />
            </button>
          </form>

          <div className="mt-8 text-sm text-[#695A62]">
            New to Food Xchange?{" "}
            <Link to="/register" className="text-[#C85A40] font-medium underline-offset-4 hover:underline" data-testid="link-register">
              Create an account
            </Link>
          </div>

          <div className="mt-10 border-t border-[#2A1B24]/10 pt-6">
            <div className="overline mb-3">Demo accounts</div>
            <div className="grid grid-cols-1 gap-2 text-sm">
              <button onClick={() => fill("luma@cafeluma.app", "Demo123!")} className="text-left bg-[#F4EFE6] hover:bg-[#EAE2D3] rounded-2xl px-4 py-3" data-testid="demo-donor">
                <div className="font-medium">Donor — Café Luma</div>
                <div className="text-[#695A62] text-xs">luma@cafeluma.app · Demo123!</div>
              </button>
              <button onClick={() => fill("harbor@harborkitchen.app", "Demo123!")} className="text-left bg-[#F4EFE6] hover:bg-[#EAE2D3] rounded-2xl px-4 py-3" data-testid="demo-recipient">
                <div className="font-medium">Recipient — Harbor Community Kitchen <span className="badge bg-[#6B705C]/10 !text-[#6B705C] !py-0.5 ml-2">verified</span></div>
                <div className="text-[#695A62] text-xs">harbor@harborkitchen.app · Demo123!</div>
              </button>
              <button onClick={() => fill("admin@foodxchange.app", "Admin123!")} className="text-left bg-[#F4EFE6] hover:bg-[#EAE2D3] rounded-2xl px-4 py-3" data-testid="demo-admin">
                <div className="font-medium">Admin</div>
                <div className="text-[#695A62] text-xs">admin@foodxchange.app · Admin123!</div>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
