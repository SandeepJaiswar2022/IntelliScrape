import { Link, useParams } from "react-router-dom";
import { ArrowLeft, ArrowUpRight, Building2, MapPin } from "lucide-react";
import { useJob } from "../hooks/useJob";
import { ApiError } from "../lib/api";
import { formatRelativeTime } from "../lib/freshness";

export function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>();
  const { data: job, isLoading, isError, error } = useJob(jobId);

  const isNotFound = error instanceof ApiError && error.status === 404;

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
      <Link
        to="/"
        className="mb-6 inline-flex items-center gap-1.5 text-sm text-slate hover:text-ink
                   dark:text-slate-400 dark:hover:text-mist"
      >
        <ArrowLeft size={16} strokeWidth={2} />
        Back to all jobs
      </Link>

      {isLoading && (
        <div className="animate-pulse space-y-4">
          <div className="h-7 w-2/3 rounded bg-slate-light dark:bg-white/10" />
          <div className="h-4 w-1/3 rounded bg-slate-light dark:bg-white/10" />
          <div className="h-32 w-full rounded bg-slate-light dark:bg-white/10" />
        </div>
      )}

      {isError && isNotFound && (
        <div className="rounded-xl border border-dashed border-slate-light py-16 text-center dark:border-white/10">
          <p className="font-display text-base font-semibold text-ink dark:text-mist">
            This job posting couldn't be found
          </p>
          <p className="mt-1 text-sm text-slate dark:text-slate-400">
            It may have been removed, or the link might be incorrect.
          </p>
        </div>
      )}

      {isError && !isNotFound && (
        <div className="rounded-xl border border-dashed border-red-300 py-16 text-center dark:border-red-500/30">
          <p className="font-display text-base font-semibold text-ink dark:text-mist">
            Couldn't load this job
          </p>
          <p className="mt-1 text-sm text-slate dark:text-slate-400">
            {error instanceof Error ? error.message : "Something went wrong."}
          </p>
        </div>
      )}

      {job && (
        <article>
          <header className="mb-6">
            <h1 className="font-display text-2xl font-semibold tracking-tight text-ink dark:text-mist sm:text-3xl">
              {job.title}
            </h1>

            <div className="mt-2 flex items-center gap-1.5 text-sm text-slate dark:text-slate-300">
              <Building2 size={15} strokeWidth={2} />
              {job.company_name}
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 font-mono text-xs text-slate dark:text-slate-400">
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
              <span>{formatRelativeTime(job.source_updated_at)}</span>
            </div>

            {job.tech_stack.length > 0 && (
              <div className="mt-3 flex flex-wrap items-center gap-1.5">
                {job.tech_stack.map((tag) => (
                  <span
                    key={tag}
                    className="rounded-full bg-slate-light/60 px-2 py-0.5 font-mono text-xs text-ink
                               dark:bg-white/10 dark:text-mist"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}

            <a
              href={job.absolute_url}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-5 inline-flex items-center gap-1.5 rounded-lg bg-signal px-4 py-2.5
                         text-sm font-semibold text-ink transition-colors hover:bg-signal-bright"
            >
              Apply on {job.company_name}
              <ArrowUpRight size={14} strokeWidth={2.5} />
            </a>
          </header>

          <div className="border-t border-slate-light pt-6 dark:border-white/10">
            {job.description_text ? (
              <p className="whitespace-pre-line text-sm leading-relaxed text-ink dark:text-mist">
                {job.description_text}
              </p>
            ) : (
              <p className="text-sm text-slate dark:text-slate-400">
                No description was provided for this posting.
              </p>
            )}
          </div>
        </article>
      )}
    </main>
  );
}
