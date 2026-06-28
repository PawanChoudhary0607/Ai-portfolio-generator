export function Skeleton({ className = "" }: { className?: string }) {
  return <div className={`skeleton animate-shimmer rounded-md ${className}`} aria-hidden="true" />;
}

/** A row-shaped skeleton matching the list rows used on the dashboard. */
export function SkeletonRow() {
  return (
    <div className="flex items-center justify-between px-5 py-3">
      <Skeleton className="h-4 w-40" />
      <div className="flex items-center gap-3">
        <Skeleton className="h-4 w-16" />
        <Skeleton className="h-4 w-10" />
      </div>
    </div>
  );
}

/** A card-shaped skeleton for theme/portfolio gallery grids. */
export function SkeletonCard() {
  return (
    <div className="rounded-xl border border-ink-200 bg-white p-4">
      <Skeleton className="h-32 w-full rounded-lg" />
      <Skeleton className="mt-4 h-4 w-2/3" />
      <Skeleton className="mt-2 h-3 w-full" />
      <Skeleton className="mt-1 h-3 w-5/6" />
    </div>
  );
}
