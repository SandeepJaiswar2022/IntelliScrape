/** Pulse-animated placeholder cards, shown while the initial jobs query loads. */
export function LoadingSkeleton() {
  return (
    <div className="flex flex-col gap-3" role="status" aria-label="Loading jobs">
      {Array.from({ length: 6 }).map((_, index) => (
        <div
          key={index}
          className="flex overflow-hidden rounded-xl border border-slate-light bg-white
                     dark:border-white/10 dark:bg-panel"
        >
          <div className="w-1 shrink-0 animate-pulse bg-slate-light dark:bg-white/10" />
          <div className="flex flex-1 flex-col gap-3 p-4 sm:p-5">
            <div className="h-4 w-2/3 animate-pulse rounded bg-slate-light dark:bg-white/10" />
            <div className="h-3 w-1/3 animate-pulse rounded bg-slate-light dark:bg-white/10" />
            <div className="h-3 w-1/2 animate-pulse rounded bg-slate-light dark:bg-white/10" />
          </div>
        </div>
      ))}
    </div>
  );
}
