import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api, { formatApiError } from "@/lib/api";
import { toast } from "sonner";
import { ArrowLeft, ArrowUpRight } from "lucide-react";

const CATEGORIES = ["produce", "bakery", "prepared_meals", "dairy", "pantry", "beverages", "other"];
const STORAGE = ["ambient", "refrigerated", "frozen", "hot"];
const UNITS = ["servings", "kg", "items", "loaves", "trays"];
const ALLERGENS = ["gluten", "dairy", "nuts", "eggs", "soy", "shellfish"];
const DIETARY = ["vegetarian", "vegan", "gluten-free", "halal", "kosher"];

const SAMPLE_IMG = "https://images.unsplash.com/photo-1542838132-92c53300491e?auto=format&fit=crop&q=80&w=1000";

export default function NewListing() {
  const nav = useNavigate();
  const now = new Date();
  const fmtDT = (d) => new Date(d).toISOString().slice(0, 16);
  const [form, setForm] = useState({
    name: "",
    description: "",
    category: "produce",
    quantity: 5,
    unit: "servings",
    storage_condition: "ambient",
    photo_url: SAMPLE_IMG,
    pickup_address: "",
    allergens: [],
    dietary: [],
    pickup_start: fmtDT(new Date(now.getTime() + 60 * 60 * 1000)),
    pickup_end: fmtDT(new Date(now.getTime() + 4 * 60 * 60 * 1000)),
    expiry_time: fmtDT(new Date(now.getTime() + 8 * 60 * 60 * 1000)),
    safety_acknowledged: true,
  });
  const [loading, setLoading] = useState(false);

  const set = (k) => (e) => setForm({ ...form, [k]: e.target.value });
  const toggleArr = (k, v) => () =>
    setForm({ ...form, [k]: form[k].includes(v) ? form[k].filter((x) => x !== v) : [...form[k], v] });

  const submit = async (e) => {
    e.preventDefault();
    if (!form.safety_acknowledged) {
      toast.error("Please confirm food-safety acknowledgement.");
      return;
    }
    setLoading(true);
    try {
      const payload = {
        ...form,
        quantity: Number(form.quantity),
        pickup_start: new Date(form.pickup_start).toISOString(),
        pickup_end: new Date(form.pickup_end).toISOString(),
        expiry_time: new Date(form.expiry_time).toISOString(),
      };
      const { data } = await api.post("/listings", payload);
      toast.success("Listing published — recipients will see it now.");
      nav(`/listings/${data.id}`);
    } catch (err) {
      toast.error(formatApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8" data-testid="new-listing-page">
      <button onClick={() => nav(-1)} className="btn-ghost !px-0 text-sm">
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <header>
        <span className="overline">Create a listing</span>
        <h1 className="font-serif text-4xl sm:text-5xl mt-2 leading-tight">List today&apos;s surplus</h1>
        <p className="text-[#695A62] mt-2">A clear listing leads to faster pickups.</p>
      </header>

      <form onSubmit={submit} className="space-y-6" data-testid="listing-form">
        <div className="card !p-8 space-y-4">
          <div>
            <label className="label">What are you offering?</label>
            <input required value={form.name} onChange={set("name")} className="input" placeholder="e.g. Sourdough loaves & morning pastries" data-testid="form-name" />
          </div>
          <div>
            <label className="label">Description (optional)</label>
            <textarea value={form.description} onChange={set("description")} rows={3} className="input resize-none" placeholder="Anything recipients should know — condition, prep, storage…" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Category</label>
              <select value={form.category} onChange={set("category")} className="input" data-testid="form-category">
                {CATEGORIES.map((c) => <option key={c} value={c}>{c.replace("_", " ")}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Quantity</label>
              <input type="number" min={1} step="0.1" required value={form.quantity} onChange={set("quantity")} className="input" data-testid="form-quantity" />
            </div>
            <div>
              <label className="label">Unit</label>
              <select value={form.unit} onChange={set("unit")} className="input" data-testid="form-unit">
                {UNITS.map((u) => <option key={u} value={u}>{u}</option>)}
              </select>
            </div>
          </div>
          <div>
            <label className="label">Storage condition</label>
            <div className="flex flex-wrap gap-2">
              {STORAGE.map((s) => (
                <button type="button" key={s} onClick={() => setForm({ ...form, storage_condition: s })}
                  className={`px-4 py-2 rounded-full text-sm transition-colors ${form.storage_condition === s ? "bg-[#2A1B24] text-[#FDFBF7]" : "bg-white border border-[#2A1B24]/10"}`}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="card !p-8 space-y-4">
          <div>
            <label className="label">Pickup address</label>
            <input required value={form.pickup_address} onChange={set("pickup_address")} className="input" placeholder="Your venue address" data-testid="form-address" />
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="label">Pickup window starts</label>
              <input type="datetime-local" required value={form.pickup_start} onChange={set("pickup_start")} className="input" data-testid="form-pickup-start" />
            </div>
            <div>
              <label className="label">Pickup window ends</label>
              <input type="datetime-local" required value={form.pickup_end} onChange={set("pickup_end")} className="input" data-testid="form-pickup-end" />
            </div>
            <div>
              <label className="label">Expires at</label>
              <input type="datetime-local" required value={form.expiry_time} onChange={set("expiry_time")} className="input" data-testid="form-expiry" />
            </div>
          </div>
        </div>

        <div className="card !p-8 space-y-4">
          <div>
            <label className="label">Allergens present</label>
            <div className="flex flex-wrap gap-2">
              {ALLERGENS.map((a) => (
                <button type="button" key={a} onClick={toggleArr("allergens", a)}
                  className={`px-3 py-1.5 rounded-full text-sm transition-colors ${form.allergens.includes(a) ? "bg-[#D97D3A]/15 text-[#D97D3A] border border-[#D97D3A]/30" : "bg-white border border-[#2A1B24]/10"}`}>
                  {a}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Dietary tags</label>
            <div className="flex flex-wrap gap-2">
              {DIETARY.map((d) => (
                <button type="button" key={d} onClick={toggleArr("dietary", d)}
                  className={`px-3 py-1.5 rounded-full text-sm transition-colors ${form.dietary.includes(d) ? "bg-[#6B705C]/15 text-[#6B705C] border border-[#6B705C]/30" : "bg-white border border-[#2A1B24]/10"}`}>
                  {d}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="label">Photo URL (optional)</label>
            <input value={form.photo_url} onChange={set("photo_url")} className="input" />
          </div>
        </div>

        <div className="card !p-8 flex items-start gap-3 bg-[#F4EFE6]">
          <input
            id="safety"
            type="checkbox"
            checked={form.safety_acknowledged}
            onChange={(e) => setForm({ ...form, safety_acknowledged: e.target.checked })}
            className="mt-1 accent-[#C85A40] w-4 h-4"
            data-testid="form-safety"
          />
          <label htmlFor="safety" className="text-sm text-[#2A1B24]">
            I confirm this food is safe for consumption at pickup time, has been handled
            according to standard food-safety guidelines, and is clearly labeled with relevant allergens.
          </label>
        </div>

        <div className="flex items-center justify-end gap-3">
          <button type="button" onClick={() => nav(-1)} className="btn-secondary" data-testid="form-cancel">Cancel</button>
          <button type="submit" disabled={loading} className="btn-primary" data-testid="form-submit">
            {loading ? "Publishing…" : "Publish listing"}
            <ArrowUpRight className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
}
