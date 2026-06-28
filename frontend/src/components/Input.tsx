import type { InputHTMLAttributes } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  hint?: string;
}

export function Input({ label, error, hint, id, className = "", ...rest }: InputProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, "-");
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={inputId} className="text-sm font-medium text-ink-700">
        {label}
      </label>
      <input
        id={inputId}
        aria-invalid={!!error}
        aria-describedby={errorId ?? hintId}
        className={`h-10 rounded-md border px-3 text-sm text-ink-900 outline-none transition-colors placeholder:text-ink-500 focus:border-accent-500 focus:ring-1 focus:ring-accent-500 ${
          error ? "border-danger" : "border-ink-200"
        } ${className}`}
        {...rest}
      />
      {hint && !error && (
        <span id={hintId} className="text-xs text-ink-500">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} className="text-xs text-danger">
          {error}
        </span>
      )}
    </div>
  );
}
