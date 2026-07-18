import { ArrowUpRight, Building2, MapPin } from "lucide-react";
import type { Job } from "../types/job";
import { FRESHNESS_BAR_CLASSES, formatRelativeTime, getFreshnessTier } from "../lib/freshness";

export function JobCard({ job }: { job: Job }) {
  const tier = getFreshnessTier(job.source_updated_at);
  const barClasses = FRESHNESS_BAR_CLASSES[tier];

  return (
    <a
      href={job.absolute_url}
      target="_blank"
      rel="noopener noreferrer"
      className="group relative flex overflow-hidden rounded-xl border border-slate-light
                 bg-white transition-all hover:border-signal/50 hover:shadow-md
                 dark:border-white/10 dark:bg-panel dark:hover:border-signal/40"
    >
      {/* The signature element: freshness-coded signal bar. */}
      <div className={`w-1 shrink-0 ${barClasses}`} aria-hidden="true" />

      <div className="flex flex-1 flex-col gap-2 p-4 sm:p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="truncate font-display text-base font-semibold text-ink dark:text-mist sm:text-lg">
              {job.title}
            </h3>
            <div className="mt-1 flex items-center gap-1.5 text-sm text-slate dark:text-slate-300">
              <Building2 size={14} strokeWidth={2} className="shrink-0" />
              <span className="truncate">{job.company_name}</span>
            </div>
          </div>

          <ArrowUpRight
            size={18}
            strokeWidth={2}
            className="mt-0.5 shrink-0 text-slate opacity-0 transition-opacity
                       group-hover:opacity-100 dark:text-slate-300"
            aria-hidden="true"
          />
        </div>

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 font-mono text-xs text-slate dark:text-slate-400">
          {job.location && (
            <span className="inline-flex items-center gap-1">
              <MapPin size={12} strokeWidth={2} />
              {job.location}
            </span>
          )}
          {job.department && (
            <span
              className="rounded-full border border-slate-light px-2 py-0.5
                         dark:border-white/10"
            >
              {job.department}
            </span>
          )}
          <span
            className={
              tier === "hot"
                ? "text-signal dark:text-signal-bright"
                : "text-slate dark:text-slate-400"
            }
          >
            {formatRelativeTime(job.source_updated_at)}
          </span>
        </div>
      </div>
    </a>
  );
}
