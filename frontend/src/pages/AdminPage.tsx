import { useState } from "react";
import { RefreshCw, ShieldCheck } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ApiError, triggerAdminScrape } from "../lib/api";

type ScrapeState =
    | { status: "idle" }
    | { status: "loading" }
    | { status: "success"; companiesProcessed: number; jobsProcessed: number }
    | { status: "error"; message: string };

export function AdminPage() {
    const { accessToken } = useAuth();
    const [scrapeState, setScrapeState] = useState<ScrapeState>({ status: "idle" });

    async function handleRefreshJobs() {
        setScrapeState({ status: "loading" });
        try {
            const result = await triggerAdminScrape(accessToken ?? undefined);
            setScrapeState({
                status: "success",
                companiesProcessed: result.companies_processed,
                jobsProcessed: result.jobs_processed,
            });
        } catch (err) {
            setScrapeState({
                status: "error",
                message: err instanceof ApiError ? err.message : "Something went wrong.",
            });
        }
    }

    const isLoading = scrapeState.status === "loading";

    return (
        <main className="mx-auto max-w-2xl px-4 py-10 sm:px-6">
            <div className="mb-6 flex items-center gap-2">
                <ShieldCheck size={22} strokeWidth={2.25} className="text-signal" />
                <h1 className="font-display text-2xl font-semibold tracking-tight text-ink dark:text-mist">
                    Admin dashboard
                </h1>
            </div>

            <div className="rounded-xl border border-slate-light bg-white p-5 dark:border-white/10 dark:bg-panel">
                <h2 className="font-display text-base font-semibold text-ink dark:text-mist">
                    Job data
                </h2>
                <p className="mt-1 text-sm text-slate dark:text-slate-400">
                    Manually trigger a Greenhouse scrape. Runs synchronously and blocks until finished --
                    fine for today's company list, see the backend's admin endpoint docstring for why this
                    isn't meant to scale indefinitely without moving back to the Celery path.
                </p>

                <button
                    type="button"
                    onClick={handleRefreshJobs}
                    disabled={isLoading}
                    className="mt-4 inline-flex items-center gap-2 rounded-lg bg-signal px-4 py-2.5 text-sm
                     font-semibold text-ink transition-colors hover:bg-signal-bright
                     disabled:cursor-not-allowed disabled:opacity-60"
                >
                    <RefreshCw size={16} strokeWidth={2.5} className={isLoading ? "animate-spin" : ""} />
                    {isLoading ? "Refreshing…" : "Refresh Jobs"}
                </button>

                {scrapeState.status === "success" && (
                    <p className="mt-3 text-sm text-signal dark:text-signal-bright">
                        Done — {scrapeState.companiesProcessed}{" "}
                        {scrapeState.companiesProcessed === 1 ? "company" : "companies"} processed,{" "}
                        {scrapeState.jobsProcessed} {scrapeState.jobsProcessed === 1 ? "job" : "jobs"}{" "}
                        ingested.
                    </p>
                )}

                {scrapeState.status === "error" && (
                    <p className="mt-3 text-sm text-red-500">{scrapeState.message}</p>
                )}
            </div>
        </main>
    );
}