import { useState } from "react";
import { useAuth } from "@/contexts/AuthContext";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { ShieldCheck, Mail, MapPin, Phone, User2 } from "lucide-react";

export default function Profile() {
  const { user, refreshMe } = useAuth();
  const [form, setForm] = useState({
    name: user.name || "",
    org_name: user.org_name || "",
    phone: user.phone || "",
    address: user.address || "",
  });
  const [busy, setBusy] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const save = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api.patch("/auth/profile", form);
      toast.success("Profile updated");
      refreshMe();
    } catch (e) {
      toast.error(formatApiError(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8" data-testid="profile-page">
      <header>
        <span className="overline">Profile</span>
        <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">Your account</h1>
      </header>

      <div className="card !p-8 grid grid-cols-1 sm:grid-cols-3 gap-6 items-center">
        <div className="w-20 h-20 rounded-full bg-[#C85A40] text-white flex items-center justify-center font-serif text-3xl italic">
          {(user.org_name || user.name || user.email).charAt(0).toUpperCase()}
        </div>
        <div className="sm:col-span-2">
          <div className="text-xs uppercase tracking-wider text-[#695A62]">{user.role}</div>
          <div className="font-serif text-2xl mt-1">{user.org_name || user.name}</div>
          <div className="text-sm text-[#695A62]">{user.email}</div>
          <div className="mt-2">
            {user.verified ? (
              <span className="badge bg-[#6B705C]/15 text-[#6B705C]"><ShieldCheck className="w-3 h-3" /> Verified</span>
            ) : user.role === "recipient" ? (
              <span className="badge bg-[#D97D3A]/15 text-[#D97D3A]">Pending verification</span>
            ) : null}
          </div>
        </div>
      </div>

      <form onSubmit={save} className="card !p-8 space-y-4" data-testid="profile-form">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="label">Name</label>
            <input value={form.name} onChange={set("name")} className="input" data-testid="profile-name" />
          </div>
          <div>
            <label className="label">Organization</label>
            <input value={form.org_name} onChange={set("org_name")} className="input" data-testid="profile-org" />
          </div>
          <div>
            <label className="label">Phone</label>
            <input value={form.phone} onChange={set("phone")} className="input" />
          </div>
          <div>
            <label className="label">Address</label>
            <input value={form.address} onChange={set("address")} className="input" />
          </div>
        </div>
        <div className="flex justify-end">
          <button type="submit" disabled={busy} className="btn-primary" data-testid="profile-save">
            {busy ? "Saving…" : "Save changes"}
          </button>
        </div>
      </form>
    </div>
  );
}
