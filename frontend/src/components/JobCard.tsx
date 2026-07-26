import { Link } from "react-router-dom";
import { ArrowUpRight, Building2, MapPin } from "lucide-react";
import type { Job } from "../types/job";
import { FRESHNESS_BAR_CLASSES, formatRelativeTime, getFreshnessTier } from "../lib/freshness";

const MAX_TECH_TAGS_SHOWN = 4;

export function JobCard({ job }: { job: Job }) {
  const tier = getFreshnessTier(job.source_updated_at);
  const barClasses = FRESHNESS_BAR_CLASSES[tier];

  const visibleTags = job.tech_stack.slice(0, MAX_TECH_TAGS_SHOWN);
  const hiddenTagCount = job.tech_stack.length - visibleTags.length;

  return (
    <div
      className="group relative flex overflow-hidden rounded-xl border border-slate-light
                 bg-white transition-all hover:border-signal/50 hover:shadow-md
                 dark:border-white/10 dark:bg-panel dark:hover:border-signal/40"
    >
      {/* The signature element: freshness-coded signal bar. */}
      <div className={`w-1 shrink-0 ${barClasses}`} aria-hidden="true" />

      <div className="flex flex-1 flex-col gap-2.5 p-4 sm:p-5">
        {/*
          The card's "main content" area (title/company/meta) links
          internally to the detail page -- separate from the external
          "Apply" link at the bottom, since a card can't nest two
          different <a> targets. This is the click target most people
          will use to read more before deciding to apply.
        */}
        <Link to={`/jobs/${job.id}`} className="min-w-0">
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
              className="mt-0.5 shrink-0 -rotate-45 text-slate opacity-0 transition-opacity
                         group-hover:opacity-100 dark:text-slate-300"
              aria-hidden="true"
            />
          </div>
        </Link>

        {job.description_preview && (
          <p className="line-clamp-2 text-sm text-slate dark:text-slate-300">
            {job.description_preview}
          </p>
        )}

        <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 font-mono text-xs text-slate dark:text-slate-400">
          {job.location && (
            <span className="inline-flex items-center gap-1">
              <MapPin size={12} strokeWidth={2} />
              {job.location}
            </span>
          )}
          {job.department && (
            <span className="rounded-full border border-slate-light px-2 py-0.5 dark:border-white/10">
              {job.department}
            </span>
          )}
          {job.experience_level && (
            <span className="rounded-full border border-slate-light px-2 py-0.5 dark:border-white/10">
              {job.experience_level}
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

        {visibleTags.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            {visibleTags.map((tag) => (
              <span
                key={tag}
                className="rounded-full bg-slate-light/60 px-2 py-0.5 font-mono text-xs text-ink
                           dark:bg-white/10 dark:text-mist"
              >
                {tag}
              </span>
            ))}
            {hiddenTagCount > 0 && (
              <span className="font-mono text-xs text-slate dark:text-slate-400">
                +{hiddenTagCount} more
              </span>
            )}
          </div>
        )}

        <div className="mt-1 flex items-center justify-between border-t border-slate-light pt-3 dark:border-white/10">
          <Link
            to={`/jobs/${job.id}`}
            className="text-xs font-medium text-slate hover:text-ink dark:text-slate-400 dark:hover:text-mist"
          >
            View full details
          </Link>
          <a
            href={job.absolute_url}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 rounded-lg bg-signal px-3 py-1.5 text-xs
                       font-semibold text-ink transition-colors hover:bg-signal-bright"
          >
            Apply
            <ArrowUpRight size={12} strokeWidth={2.5} />
          </a>
        </div>
      </div>
    </div>
  );
}
