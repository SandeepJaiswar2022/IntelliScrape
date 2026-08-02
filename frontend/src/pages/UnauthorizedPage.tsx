import { Link } from "react-router-dom";
import { ShieldAlert } from "lucide-react";

export function UnauthorizedPage() {
    return (
        <main className="mx-auto flex max-w-md flex-col items-center px-4 py-24 text-center sm:px-6">
            <ShieldAlert size={32} strokeWidth={1.75} className="text-red-500" />
            <h1 className="mt-4 font-display text-xl font-semibold text-ink dark:text-mist">
                403 — Access denied
            </h1>
            <p className="mt-2 text-sm text-slate dark:text-slate-400">
                You don't have permission to view this page.
            </p>
            <Link
                to="/jobs"
                className="mt-6 rounded-lg bg-signal px-4 py-2.5 text-sm font-semibold text-ink
                   transition-colors hover:bg-signal-bright"
            >
                Back to jobs
            </Link>
        </main>
    );
}