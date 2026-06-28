export function ProgressBar({ percent }: { percent: number }) {
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-100">
      <div
        className="h-full rounded-full bg-accent-600 transition-all duration-200"
        style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
      />
    </div>
  );
}
