import { Link } from "react-router-dom";
import { Radio, Search, ShieldCheck, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

export function LandingPage() {
    const { user } = useAuth();

    return (
        <main className="mx-auto max-w-3xl px-4 py-16 sm:px-6 sm:py-24">
            <div className="flex flex-col items-center text-center">
                <div className="inline-flex items-center gap-2 rounded-full border border-slate-light px-3 py-1 dark:border-white/10">
                    <Radio size={14} strokeWidth={2.25} className="text-signal" />
                    <span className="font-mono text-xs text-slate dark:text-slate-400">
                        Live from Stripe, GitLab, Figma, Robinhood, Asana
                    </span>
                </div>

                <h1 className="mt-6 font-display text-3xl font-bold tracking-tight text-ink dark:text-mist sm:text-5xl">
                    Job hunting, tracked like a signal.
                </h1>
                <p className="mt-4 max-w-xl text-base text-slate dark:text-slate-300">
                    IntelliScrape watches company career pages continuously and surfaces real openings —
                    searchable by role, location, experience level, and tech stack — the moment they're
                    posted.
                </p>

                <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                    {user ? (
                        <Link
                            to="/jobs"
                            className="rounded-lg bg-signal px-5 py-2.5 text-sm font-semibold text-ink
                         transition-colors hover:bg-signal-bright"
                        >
                            Go to jobs
                        </Link>
                    ) : (
                        <>
                            <Link
                                to="/register"
                                className="rounded-lg bg-signal px-5 py-2.5 text-sm font-semibold text-ink
                           transition-colors hover:bg-signal-bright"
                            >
                                Get started
                            </Link>
                            <Link
                                to="/login"
                                className="rounded-lg border border-slate-light px-5 py-2.5 text-sm font-semibold
                           text-ink transition-colors hover:bg-slate-light/50
                           dark:border-white/10 dark:text-mist dark:hover:bg-white/5"
                            >
                                Sign in
                            </Link>
                        </>
                    )}
                </div>
            </div>

            <div className="mt-20 grid gap-6 sm:grid-cols-3">
                <div className="rounded-xl border border-slate-light p-5 dark:border-white/10">
                    <Search size={18} strokeWidth={2} className="text-signal" />
                    <h3 className="mt-3 font-display text-sm font-semibold text-ink dark:text-mist">
                        Real filters
                    </h3>
                    <p className="mt-1.5 text-sm text-slate dark:text-slate-400">
                        Search by role and location, then narrow by experience level and tech stack.
                    </p>
                </div>
                <div className="rounded-xl border border-slate-light p-5 dark:border-white/10">
                    <Sparkles size={18} strokeWidth={2} className="text-signal" />
                    <h3 className="mt-3 font-display text-sm font-semibold text-ink dark:text-mist">
                        Freshness signal
                    </h3>
                    <p className="mt-1.5 text-sm text-slate dark:text-slate-400">
                        Every listing shows exactly how recently it was posted or updated.
                    </p>
                </div>
                <div className="rounded-xl border border-slate-light p-5 dark:border-white/10">
                    <ShieldCheck size={18} strokeWidth={2} className="text-signal" />
                    <h3 className="mt-3 font-display text-sm font-semibold text-ink dark:text-mist">
                        Straight to the source
                    </h3>
                    <p className="mt-1.5 text-sm text-slate dark:text-slate-400">
                        Every posting links directly to the company's real application page.
                    </p>
                </div>
            </div>
        </main>
    );
}