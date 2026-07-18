import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  page: number;
  totalPages: number;
  onPageChange: (page: number) => void;
}

export function Pagination({ page, totalPages, onPageChange }: PaginationProps) {
  if (totalPages <= 1) return null;

  const isFirstPage = page <= 1;
  const isLastPage = page >= totalPages;

  return (
    <div className="flex items-center justify-center gap-4 pt-2">
      <button
        type="button"
        onClick={() => onPageChange(page - 1)}
        disabled={isFirstPage}
        aria-label="Previous page"
        className="inline-flex h-9 w-9 items-center justify-center rounded-full border
                   border-slate-light text-ink transition-colors hover:bg-slate-light/50
                   disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent
                   dark:border-white/10 dark:text-mist dark:hover:bg-white/5"
      >
        <ChevronLeft size={16} strokeWidth={2} />
      </button>

      <span className="font-mono text-xs text-slate dark:text-slate-400">
        Page {page} of {totalPages}
      </span>

      <button
        type="button"
        onClick={() => onPageChange(page + 1)}
        disabled={isLastPage}
        aria-label="Next page"
        className="inline-flex h-9 w-9 items-center justify-center rounded-full border
                   border-slate-light text-ink transition-colors hover:bg-slate-light/50
                   disabled:cursor-not-allowed disabled:opacity-40 disabled:hover:bg-transparent
                   dark:border-white/10 dark:text-mist dark:hover:bg-white/5"
      >
        <ChevronRight size={16} strokeWidth={2} />
      </button>
    </div>
  );
}
