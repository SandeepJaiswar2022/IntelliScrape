import { Radio } from "lucide-react";
import { ThemeToggle } from "./ThemeToggle";

export function Navbar() {
  return (
    <header
      className="sticky top-0 z-10 border-b border-slate-light bg-canvas/80
                 backdrop-blur-md dark:border-white/10 dark:bg-midnight/80"
    >
      <div className="mx-auto flex max-w-3xl items-center justify-between px-4 py-4 sm:px-6">
        <div className="flex items-center gap-2">
          {/* Radio icon doubles as the "signal" motif from the design
              language -- a live feed of postings, not a static list. */}
          <Radio size={20} strokeWidth={2.25} className="text-signal" />
          <span className="font-display text-lg font-semibold tracking-tight">
            IntelliScrape
          </span>
        </div>
        <ThemeToggle />
      </div>
    </header>
  );
}
