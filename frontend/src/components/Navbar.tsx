import { Link, useNavigate } from "react-router-dom";
import { Radio } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";
import { useAuth } from "../context/AuthContext";
import { ROLE } from "../types/auth";

/**
 * Nav links change based on auth state, per spec:
 *   anonymous          -> Home, Sign In, Register
 *   authenticated USER -> Jobs, Logout
 *   authenticated ADMIN-> Jobs, Admin, Logout
 * This is UI-only, same caveat as AdminRoute -- the real access
 * control is enforced server-side and by the route guards, not by
 * which links happen to be visible here.
 */
export function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/");
  }

  return (
    <header
      className="sticky top-0 z-10 border-b border-slate-light bg-canvas/80
                 backdrop-blur-md dark:border-white/10 dark:bg-midnight/80"
    >
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 sm:px-6">
        <Link to="/" className="flex items-center gap-2">
          <Radio size={20} strokeWidth={2.25} className="text-signal" />
          <span className="font-display text-lg font-semibold tracking-tight text-ink dark:text-mist">
            IntelliScrape
          </span>
        </Link>

        <nav className="flex items-center gap-4">
          {!user && (
            <>
              <Link
                to="/login"
                className="text-sm font-medium text-slate hover:text-ink dark:text-slate-300 dark:hover:text-mist"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                className="text-sm font-medium text-slate hover:text-ink dark:text-slate-300 dark:hover:text-mist"
              >
                Register
              </Link>
            </>
          )}

          {user && (
            <>
              <Link
                to="/jobs"
                className="text-sm font-medium text-slate hover:text-ink dark:text-slate-300 dark:hover:text-mist"
              >
                Jobs
              </Link>
              {user.role === ROLE.ADMIN && (
                <Link
                  to="/admin"
                  className="text-sm font-medium text-slate hover:text-ink dark:text-slate-300 dark:hover:text-mist"
                >
                  Admin
                </Link>
              )}
              <button
                type="button"
                onClick={handleLogout}
                className="text-sm font-medium text-slate hover:text-ink dark:text-slate-300 dark:hover:text-mist"
              >
                Logout
              </button>
            </>
          )}

          <ThemeToggle />
        </nav>
      </div>
    </header>
  );
}