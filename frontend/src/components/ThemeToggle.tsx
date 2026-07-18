import { Moon, Sun } from "lucide-react";
import { useTheme } from "../hooks/useTheme";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="inline-flex h-9 w-9 items-center justify-center rounded-full
                 border border-slate-light text-ink transition-colors
                 hover:bg-slate-light/50
                 dark:border-white/10 dark:text-mist dark:hover:bg-white/5"
    >
      {isDark ? <Sun size={16} strokeWidth={2} /> : <Moon size={16} strokeWidth={2} />}
    </button>
  );
}
