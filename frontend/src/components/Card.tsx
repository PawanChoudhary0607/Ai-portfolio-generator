import type { HTMLAttributes, ReactNode } from "react";

export function Card({ className = "", children, ...rest }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={`rounded-lg border border-ink-200 bg-white shadow-card ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}

const badgeStyles: Record<string, string> = {
  neutral: "bg-ink-100 text-ink-700",
  accent: "bg-accent-50 text-accent-700",
  success: "bg-green-50 text-success",
  warning: "bg-amber-50 text-warning",
  danger: "bg-red-50 text-danger",
};

export function Badge({
  tone = "neutral",
  children,
}: {
  tone?: keyof typeof badgeStyles;
  children: ReactNode;
}) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium font-mono ${badgeStyles[tone]}`}
    >
      {children}
    </span>
  );
}
