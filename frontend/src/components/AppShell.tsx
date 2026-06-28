import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Logo } from "@/components/Logo";
import { useAuth } from "@/context/AuthContext";

interface NavItem {
  to: string;
  label: string;
  icon: string;
}

const navItems: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: "□" },
  { to: "/upload", label: "New portfolio", icon: "↑" },
  { to: "/themes", label: "Theme gallery", icon: "◇" },
];

const secondaryNavItems: NavItem[] = [
  { to: "/support", label: "Support development", icon: "♥" },
  { to: "/settings", label: "Settings", icon: "⚙" },
];

function NavRow({ item }: { item: NavItem }) {
  return (
    <NavLink
      to={item.to}
      className={({ isActive }) =>
        `flex items-center gap-2.5 rounded-md px-2.5 py-2 text-sm font-medium transition-colors ${
          isActive ? "bg-accent-50 text-accent-700" : "text-ink-700 hover:bg-ink-100"
        }`
      }
    >
      <span className="w-4 text-center font-mono text-xs">{item.icon}</span>
      {item.label}
    </NavLink>
  );
}

export function AppShell() {
  const { user, logOut } = useAuth();
  const [navOpen, setNavOpen] = useState(false);
  const location = useLocation();
  const drawerRef = useRef<HTMLDivElement>(null);
  const menuButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    setNavOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    if (!navOpen) return;
    drawerRef.current?.focus();
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setNavOpen(false);
        menuButtonRef.current?.focus();
      }
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [navOpen]);

  const sidebarContent = (
    <>
      <div className="px-2 pb-6">
        <Logo />
      </div>

      <nav className="flex flex-1 flex-col gap-1">
        {navItems.map((item) => (
          <NavRow key={item.label} item={item} />
        ))}

        <div className="mt-4 border-t border-ink-200 pt-4">
          {secondaryNavItems.map((item) => (
            <NavRow key={item.label} item={item} />
          ))}
        </div>
      </nav>

      <div className="border-t border-ink-200 pt-4">
        <div className="flex items-center gap-2.5 px-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-ink-900 text-xs font-medium text-white">
            {user?.full_name?.slice(0, 1).toUpperCase()}
          </div>
          <div className="flex-1 overflow-hidden">
            <p className="truncate text-sm font-medium text-ink-900">{user?.full_name}</p>
            <p className="truncate text-xs text-ink-500">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logOut}
          className="mt-3 w-full rounded-md px-2.5 py-1.5 text-left text-sm text-ink-500 transition-colors hover:bg-ink-100 hover:text-ink-900"
        >
          Sign out
        </button>
      </div>
    </>
  );

  return (
    <div className="flex min-h-screen flex-col bg-white lg:flex-row">
      <div className="flex items-center justify-between border-b border-ink-200 px-4 py-3 lg:hidden">
        <Logo />
        <button
          ref={menuButtonRef}
          onClick={() => setNavOpen(true)}
          aria-label="Open navigation menu"
          className="flex h-9 w-9 items-center justify-center rounded-md text-ink-700 hover:bg-ink-100"
        >
          <span className="font-mono text-base" aria-hidden="true">
            ☰
          </span>
        </button>
      </div>

      {navOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-ink-900/30" onClick={() => setNavOpen(false)} aria-hidden="true" />
          <aside
            ref={drawerRef}
            tabIndex={-1}
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
            className="absolute inset-y-0 left-0 flex w-72 flex-col bg-white px-4 py-5 shadow-lift focus:outline-none"
          >
            <button
              onClick={() => setNavOpen(false)}
              aria-label="Close navigation menu"
              className="absolute right-3 top-3 flex h-8 w-8 items-center justify-center rounded-md text-ink-500 hover:bg-ink-100"
            >
              x
            </button>
            {sidebarContent}
          </aside>
        </div>
      )}

      <aside className="hidden w-60 flex-shrink-0 flex-col border-r border-ink-200 px-4 py-5 lg:flex">
        {sidebarContent}
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
