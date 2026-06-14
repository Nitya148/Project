import { Outlet, NavLink, useNavigate, Link } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";
import {
  LayoutDashboard,
  Compass,
  PackageOpen,
  Inbox,
  Gift,
  Sparkles,
  ShieldCheck,
  LogOut,
  User2,
  Plus,
} from "lucide-react";

const navByRole = {
  donor: [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/listings", label: "Listings", icon: PackageOpen },
    { to: "/requests", label: "Requests", icon: Inbox },
    { to: "/rewards", label: "Rewards", icon: Gift },
    { to: "/impact", label: "Impact", icon: Sparkles },
  ],
  recipient: [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/discover", label: "Discover", icon: Compass },
    { to: "/requests", label: "Requests", icon: Inbox },
    { to: "/impact", label: "Impact", icon: Sparkles },
  ],
  admin: [
    { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { to: "/admin", label: "Admin", icon: ShieldCheck },
    { to: "/impact", label: "Impact", icon: Sparkles },
  ],
};

export default function Layout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const items = navByRole[user.role] || [];

  const handleLogout = async () => {
    await logout();
    nav("/");
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-[#2A1B24]">
      <header
        className="sticky top-0 z-40 backdrop-blur-xl bg-[#FDFBF7]/85 border-b border-[#2A1B24]/5"
        data-testid="app-header"
      >
        <div className="max-w-7xl mx-auto px-6 md:px-10 h-16 flex items-center justify-between">
          <Link to="/dashboard" className="flex items-center gap-2" data-testid="logo-link">
            <div className="w-8 h-8 rounded-full bg-[#C85A40] flex items-center justify-center text-white font-serif italic text-lg leading-none">R</div>
            <span className="font-serif text-xl tracking-tight">
              Re<span className="italic text-[#C85A40]">Plate</span>
            </span>
          </Link>

          <nav className="hidden md:flex items-center gap-1">
            {items.map((it) => (
              <NavLink
                key={it.to}
                to={it.to}
                data-testid={`nav-${it.label.toLowerCase()}`}
                className={({ isActive }) =>
                  `inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-[#2A1B24] text-[#FDFBF7]"
                      : "text-[#2A1B24]/70 hover:text-[#2A1B24] hover:bg-[#2A1B24]/5"
                  }`
                }
              >
                <it.icon className="w-4 h-4" strokeWidth={1.6} />
                {it.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            {user.role === "donor" && (
              <Link to="/listings/new" className="hidden sm:inline-flex btn-primary !py-2 !px-4 text-sm" data-testid="header-new-listing">
                <Plus className="w-4 h-4" />
                New Listing
              </Link>
            )}
            <Link to="/profile" className="btn-ghost !px-3" data-testid="profile-link" title={user.email}>
              <User2 className="w-4 h-4" strokeWidth={1.8} />
              <span className="hidden sm:inline text-sm">
                {(user.org_name || user.name || "").split(" ")[0]}
              </span>
            </Link>
            <button onClick={handleLogout} className="btn-ghost !px-3" data-testid="logout-btn" title="Log out">
              <LogOut className="w-4 h-4" strokeWidth={1.8} />
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        <nav className="md:hidden flex items-center gap-1 overflow-x-auto px-4 pb-3">
          {items.map((it) => (
            <NavLink
              key={it.to}
              to={it.to}
              className={({ isActive }) =>
                `whitespace-nowrap inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium ${
                  isActive
                    ? "bg-[#2A1B24] text-[#FDFBF7]"
                    : "text-[#2A1B24]/70 bg-[#F4EFE6]"
                }`
              }
            >
              <it.icon className="w-3.5 h-3.5" />
              {it.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-6 md:px-10 py-8 md:py-12">
        <Outlet />
      </main>

      <footer className="border-t border-[#2A1B24]/5 mt-16 py-8 text-center text-sm text-[#695A62]">
        <span className="font-serif italic">RePlate</span> — rescuing surplus, feeding community.
      </footer>
    </div>
  );
}
