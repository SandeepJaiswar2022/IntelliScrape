import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LogIn } from "lucide-react";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../lib/api";

export function LoginPage() {
    const { login } = useAuth();
    const navigate = useNavigate();

    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [isSubmitting, setIsSubmitting] = useState(false);

    async function handleSubmit(event: FormEvent) {
        event.preventDefault();
        setError(null);
        setIsSubmitting(true);
        try {
            await login(email, password);
            navigate("/jobs");
        } catch (err) {
            setError(err instanceof ApiError ? err.message : "Something went wrong. Please try again.");
        } finally {
            setIsSubmitting(false);
        }
    }

    return (
        <main className="mx-auto flex max-w-sm flex-col px-4 py-16 sm:px-6">
            <div className="mb-6 flex items-center gap-2">
                <LogIn size={20} strokeWidth={2.25} className="text-signal" />
                <h1 className="font-display text-xl font-semibold text-ink dark:text-mist">Sign in</h1>
            </div>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
                <label className="flex flex-col gap-1.5">
                    <span className="text-sm font-medium text-ink dark:text-mist">Email</span>
                    <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                        className="rounded-lg border border-slate-light bg-white px-3.5 py-2.5 text-sm text-ink
                       focus:border-signal
                       dark:border-white/10 dark:bg-panel dark:text-mist"
                    />
                </label>

                <label className="flex flex-col gap-1.5">
                    <span className="text-sm font-medium text-ink dark:text-mist">Password</span>
                    <input
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        autoComplete="current-password"
                        className="rounded-lg border border-slate-light bg-white px-3.5 py-2.5 text-sm text-ink
                       focus:border-signal
                       dark:border-white/10 dark:bg-panel dark:text-mist"
                    />
                </label>

                {error && <p className="text-sm text-red-500">{error}</p>}

                <button
                    type="submit"
                    disabled={isSubmitting}
                    className="mt-2 rounded-lg bg-signal px-4 py-2.5 text-sm font-semibold text-ink
                     transition-colors hover:bg-signal-bright disabled:cursor-not-allowed disabled:opacity-60"
                >
                    {isSubmitting ? "Signing in…" : "Sign in"}
                </button>
            </form>

            <p className="mt-6 text-center text-sm text-slate dark:text-slate-400">
                Don't have an account?{" "}
                <Link to="/register" className="font-medium text-ink underline dark:text-mist">
                    Register
                </Link>
            </p>
        </main>
    );
}