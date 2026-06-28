import type { ReactNode } from "react";

export interface SupportMethod {
  name: string;
  description: string;
  href: string;
  cta: string;
}

export interface UpiConfig {
  /** Your UPI VPA, e.g. "yourname@upi" — used to build the upi:// deep link. */
  vpa: string;
  payeeName: string;
  /** Path to a pre-generated QR code image for this VPA, if you have one. */
  qrImageSrc?: string;
}

interface SupportSectionProps {
  title?: string;
  intro?: ReactNode;
  methods: SupportMethod[];
  upi?: UpiConfig;
  footerNote?: ReactNode;
}

/**
 * A free-standing, configurable "support development" section — every
 * method here just opens an external link or deep link. No payment logic
 * lives in this app; this component only ever renders <a> tags. Pass in
 * your own `methods`/`upi` to reuse this across other projects.
 */
export function SupportSection({
  title = "Support development",
  intro,
  methods,
  upi,
  footerNote,
}: SupportSectionProps) {
  const upiHref = upi
    ? `upi://pay?pa=${encodeURIComponent(upi.vpa)}&pn=${encodeURIComponent(upi.payeeName)}&cu=INR`
    : undefined;

  return (
    <div>
      <h1 className="text-xl font-semibold text-ink-900">{title}</h1>
      {intro && <div className="mt-2 text-sm leading-relaxed text-ink-500">{intro}</div>}

      <div className="mt-8 grid gap-4 sm:grid-cols-2">
        {methods.map((link) => (
          <a
            key={link.name}
            href={link.href}
            target="_blank"
            rel="noopener noreferrer"
            className="group flex flex-col justify-between rounded-xl border border-ink-200 bg-white p-5 transition-colors hover:border-accent-400 hover:bg-accent-50/30"
          >
            <div>
              <p className="text-sm font-semibold text-ink-900">{link.name}</p>
              <p className="mt-1 text-sm text-ink-500">{link.description}</p>
            </div>
            <span className="mt-4 text-sm font-medium text-accent-600 group-hover:text-accent-700">
              {link.cta} →
            </span>
          </a>
        ))}
      </div>

      {upi && (
        <div className="mt-6 rounded-xl border border-ink-200 bg-surface p-5">
          <p className="text-sm font-semibold text-ink-900">UPI</p>
          <p className="mt-1 text-sm text-ink-500">
            Scan with any UPI app, or open directly if you're on your phone.
          </p>
          <div className="mt-4 flex flex-wrap items-center gap-4">
            <div className="flex h-32 w-32 flex-shrink-0 items-center justify-center rounded-lg border border-dashed border-ink-300 bg-white">
              {upi.qrImageSrc ? (
                <img src={upi.qrImageSrc} alt={`UPI QR code for ${upi.vpa}`} className="h-full w-full rounded-lg object-contain" />
              ) : (
                <span className="eyebrow px-2 text-center text-ink-500">QR — add a generated code for {upi.vpa}</span>
              )}
            </div>
            <a
              href={upiHref}
              className="text-sm font-medium text-accent-600 hover:text-accent-700"
            >
              Open in UPI app →
            </a>
          </div>
        </div>
      )}

      {footerNote && <div className="mt-8 text-xs text-ink-500">{footerNote}</div>}
    </div>
  );
}
