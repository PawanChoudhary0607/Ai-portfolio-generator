import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "dark" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md";
  isLoading?: boolean;
  children: ReactNode;
}

const base =
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-colors duration-150 disabled:opacity-50 disabled:cursor-not-allowed focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent-500";

const variants: Record<string, string> = {
  primary: "bg-accent-600 text-white hover:bg-accent-700 active:bg-accent-700",
  dark: "bg-ink-900 text-white hover:bg-ink-700",
  secondary: "bg-white text-ink-900 border border-ink-200 hover:border-ink-300 hover:bg-ink-100",
  ghost: "bg-transparent text-ink-700 hover:bg-ink-100",
  danger: "bg-white text-danger border border-danger/30 hover:bg-danger/5",
};

const sizes: Record<string, string> = {
  sm: "h-8 px-3 text-sm",
  md: "h-10 px-4 text-sm",
};

export function Button({
  variant = "primary",
  size = "md",
  isLoading = false,
  className = "",
  children,
  disabled,
  ...rest
}: ButtonProps) {
  return (
    <button
      className={`${base} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled || isLoading}
      aria-busy={isLoading || undefined}
      {...rest}
    >
      {isLoading && (
        <span aria-hidden="true" className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-current border-t-transparent" />
      )}
      {children}
    </button>
  );
}
