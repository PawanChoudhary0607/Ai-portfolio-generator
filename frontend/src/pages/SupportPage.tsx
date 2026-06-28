import { useMemo, useState } from "react";
import { Button } from "@/components/Button";

const PAYPAL_URL = import.meta.env.VITE_SUPPORT_PAYPAL_URL ?? "https://paypal.me/PawanChoudhary232";
const UPI_ID = import.meta.env.VITE_SUPPORT_UPI_ID ?? "p4wan@ptaxis";
const PAYEE_NAME = import.meta.env.VITE_SUPPORT_PAYEE_NAME ?? "Portfolio AI";
const UPI_QR_SRC = "/assets/payments/upi-qr.png";

export function SupportPage() {
  const [copied, setCopied] = useState(false);
  const upiLink = useMemo(
    () => `upi://pay?pa=${encodeURIComponent(UPI_ID)}&pn=${encodeURIComponent(PAYEE_NAME)}&cu=INR`,
    [],
  );

  async function copyUpi() {
    await navigator.clipboard.writeText(UPI_ID);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="mx-auto max-w-5xl px-6 py-8 sm:px-8">
      <section>
        <p className="eyebrow text-accent-600">Support development</p>
        <h1 className="mt-3 text-3xl font-semibold tracking-normal text-ink-900">Support Portfolio AI</h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-ink-600">
          Portfolio AI is completely free to use.
        </p>
        <p className="mt-2 max-w-2xl text-base leading-7 text-ink-600">
          If Portfolio AI helped you create your portfolio, save time, or prepare for your career, you
          can support future development.
        </p>

        <div className="mt-6 rounded-xl border border-ink-200 bg-surface p-5">
          <p className="text-sm font-semibold text-ink-900">Your support helps cover:</p>
          <ul className="mt-2 grid gap-1 text-sm leading-relaxed text-ink-600 sm:grid-cols-2">
            <li>• AI infrastructure</li>
            <li>• Hosting</li>
            <li>• Future improvements</li>
            <li>• Keeping Portfolio AI free for everyone</li>
          </ul>
        </div>

        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-ink-500">
          No features are locked behind donations. Everyone gets the same experience.
        </p>
      </section>

      <div className="mt-8 grid gap-8 lg:grid-cols-[360px_1fr] lg:items-start">
        <aside className="rounded-xl border border-accent-200 bg-accent-50 p-5 shadow-sm">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="eyebrow text-accent-600">Primary</p>
              <p className="mt-1 text-sm font-semibold text-ink-900">🇮🇳 UPI</p>
              <p className="mt-1 text-sm text-ink-600">Scan the QR or open your UPI app on mobile.</p>
            </div>
            {copied && (
              <span className="rounded-full bg-success/10 px-2 py-1 text-xs font-medium text-success">
                Copied
              </span>
            )}
          </div>

          <div className="mt-5 flex justify-center rounded-xl border border-ink-200 bg-white p-4">
            <img
              src={UPI_QR_SRC}
              alt={`UPI QR code for ${UPI_ID}`}
              className="h-56 w-56 rounded-lg bg-white object-contain"
            />
          </div>

          <div className="mt-4 rounded-lg bg-ink-100 px-3 py-2">
            <p className="eyebrow text-ink-500">UPI ID</p>
            <p className="mt-1 break-all font-mono text-sm text-ink-900">{UPI_ID}</p>
          </div>

          <div className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
            <Button variant="secondary" onClick={copyUpi}>
              Copy UPI ID
            </Button>
            <a
              href={upiLink}
              className="inline-flex h-10 items-center justify-center rounded-md bg-ink-900 px-4 text-sm font-medium text-white transition-colors hover:bg-ink-700"
            >
              Open UPI app
            </a>
          </div>
        </aside>

        <a
          href={PAYPAL_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="group rounded-xl border border-ink-200 bg-white p-5 shadow-sm transition-all hover:-translate-y-0.5 hover:border-ink-300 hover:shadow-lift"
        >
          <p className="eyebrow text-ink-500">Secondary</p>
          <p className="mt-1 text-sm font-semibold text-ink-900">🌍 PayPal</p>
          <p className="mt-2 text-sm leading-relaxed text-ink-500">
            A direct option for one-time contributions from supported countries.
          </p>
          <span className="mt-5 inline-flex h-10 items-center rounded-md border border-ink-200 px-4 text-sm font-medium text-ink-900 group-hover:bg-ink-100">
            Donate with PayPal
          </span>
        </a>
      </div>
    </div>
  );
}
