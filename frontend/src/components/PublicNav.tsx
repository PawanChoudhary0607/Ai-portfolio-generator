import { Link } from "react-router-dom";
import { Logo } from "@/components/Logo";
import { Button } from "@/components/Button";
import { useAuth } from "@/context/AuthContext";

export function PublicNav() {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-30 border-b border-ink-200/70 bg-white/80 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link to="/" aria-label="Portfolio AI home">
          <Logo />
        </Link>
        <nav className="hidden items-center gap-7 text-sm font-medium text-ink-700 md:flex">
          <a href="#how-it-works" className="hover:text-ink-900">
            How it works
          </a>
          <a href="#themes" className="hover:text-ink-900">
            Themes
          </a>
          <a href="#faq" className="hover:text-ink-900">
            FAQ
          </a>
          <Link to="/support" className="hover:text-ink-900">
            Support
          </Link>
        </nav>
        <div className="flex items-center gap-3">
          {user ? (
            <Link to="/dashboard">
              <Button size="sm">Go to dashboard</Button>
            </Link>
          ) : (
            <>
              <Link to="/login" className="text-sm font-medium text-ink-700 hover:text-ink-900">
                Log in
              </Link>
              <Link to="/signup">
                <Button size="sm">Get started</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
