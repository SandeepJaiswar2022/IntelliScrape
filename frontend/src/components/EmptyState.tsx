import { RadioTower, TriangleAlert } from "lucide-react";

interface EmptyStateProps {
  hasActiveFilters: boolean;
  onClearFilters: () => void;
}

/**
 * Shown when a query returns zero results. Copy follows the design
 * skill's guidance: this is an invitation to act, not an apology --
 * it says what happened and gives the one relevant next step.
 */
export function EmptyState({ hasActiveFilters, onClearFilters }: EmptyStateProps) {
  return (
    <div
      className="flex flex-col items-center gap-3 rounded-xl border border-dashed
                 border-slate-light py-16 text-center dark:border-white/10"
    >
      <RadioTower size={28} strokeWidth={1.75} className="text-slate dark:text-slate-400" />
      <div>
        <p className="font-display text-base font-semibold text-ink dark:text-mist">
          No signals match your filters
        </p>
        <p className="mt-1 text-sm text-slate dark:text-slate-400">
          Try a broader role or location.
        </p>
      </div>
      {hasActiveFilters && (
        <button
          type="button"
          onClick={onClearFilters}
          className="mt-1 rounded-lg border border-slate-light px-3.5 py-1.5 text-sm font-medium
                     text-ink transition-colors hover:bg-slate-light/50
                     dark:border-white/10 dark:text-mist dark:hover:bg-white/5"
        >
          Clear filters
        </button>
      )}
    </div>
  );
}

/** Shown when the jobs request itself fails (network error, backend down, etc.). */
export function ErrorState({ message }: { message: string }) {
  return (
    <div
      className="flex flex-col items-center gap-3 rounded-xl border border-dashed
                 border-red-300 py-16 text-center dark:border-red-500/30"
    >
      <TriangleAlert size={28} strokeWidth={1.75} className="text-red-500" />
      <div>
        <p className="font-display text-base font-semibold text-ink dark:text-mist">
          Couldn't load jobs
        </p>
        <p className="mt-1 text-sm text-slate dark:text-slate-400">{message}</p>
      </div>
    </div>
  );
}
