import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Logo } from "@/components/Logo";

export function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Link to="/">
            <Logo />
          </Link>
        </div>
        <div className="rounded-lg border border-ink-200 bg-white p-8 shadow-card">
          <h1 className="text-lg font-semibold text-ink-900">{title}</h1>
          <p className="mt-1 text-sm text-ink-500">{subtitle}</p>
          <div className="mt-6">{children}</div>
        </div>
      </div>
    </div>
  );
}
