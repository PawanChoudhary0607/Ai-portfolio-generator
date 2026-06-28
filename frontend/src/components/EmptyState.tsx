import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
  className?: string;
}

/**
 * A calm, intentional "nothing here yet" panel — replaces bare blank
 * sections across the dashboard, gallery, and history views.
 */
export function EmptyState({ icon, title, description, action, className = "" }: EmptyStateProps) {
  return (
    <div className={`flex flex-col items-center gap-3 px-6 py-10 text-center ${className}`}>
      {icon && (
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-ink-100 text-ink-500">
          {icon}
        </div>
      )}
      <div>
        <p className="text-sm font-medium text-ink-900">{title}</p>
        {description && <p className="mt-1 max-w-sm text-sm text-ink-500">{description}</p>}
      </div>
      {action}
    </div>
  );
}
