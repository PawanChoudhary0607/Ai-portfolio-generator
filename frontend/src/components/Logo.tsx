export function Logo({ className = "" }: { className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2 font-semibold text-ink-900 ${className}`}>
      <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent-600 font-mono text-xs text-white">
        P
      </span>
      Portfolio<span className="text-accent-600">AI</span>
    </span>
  );
}
