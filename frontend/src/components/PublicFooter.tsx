import { Link } from "react-router-dom";
import { Logo } from "@/components/Logo";

export function PublicFooter() {
  return (
    <footer className="border-t border-ink-200 bg-surface">
      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex flex-col items-start justify-between gap-6 md:flex-row md:items-center">
          <Logo />
          <nav className="flex flex-wrap gap-6 text-sm text-ink-500">
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
              Support development
            </Link>
            <Link to="/signup" className="hover:text-ink-900">
              Get started
            </Link>
          </nav>
        </div>
        <p className="mt-8 text-xs text-ink-500">
          Resumes are processed by a local AI engine and never sent to a third-party AI API.
          Generation is, and will always be, free.
        </p>
      </div>
    </footer>
  );
}
