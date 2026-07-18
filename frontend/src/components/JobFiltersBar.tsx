import { MapPin, Search } from "lucide-react";

interface JobFiltersBarProps {
  titleInput: string;
  locationInput: string;
  onTitleChange: (value: string) => void;
  onLocationChange: (value: string) => void;
}

export function JobFiltersBar({
  titleInput,
  locationInput,
  onTitleChange,
  onLocationChange,
}: JobFiltersBarProps) {
  return (
    <div className="flex flex-col gap-3 sm:flex-row">
      <label className="relative flex-1">
        <span className="sr-only">Filter by role</span>
        <Search
          size={16}
          strokeWidth={2}
          className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate dark:text-slate-400"
        />
        <input
          type="text"
          value={titleInput}
          onChange={(e) => onTitleChange(e.target.value)}
          placeholder="Search roles — e.g. backend engineer"
          className="w-full rounded-lg border border-slate-light bg-white py-2.5 pl-10 pr-3.5
                     text-sm text-ink placeholder:text-slate/70
                     focus:border-signal
                     dark:border-white/10 dark:bg-panel dark:text-mist dark:placeholder:text-slate-400"
        />
      </label>

      <label className="relative flex-1">
        <span className="sr-only">Filter by location</span>
        <MapPin
          size={16}
          strokeWidth={2}
          className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate dark:text-slate-400"
        />
        <input
          type="text"
          value={locationInput}
          onChange={(e) => onLocationChange(e.target.value)}
          placeholder="Location — e.g. remote, NYC"
          className="w-full rounded-lg border border-slate-light bg-white py-2.5 pl-10 pr-3.5
                     text-sm text-ink placeholder:text-slate/70
                     focus:border-signal
                     dark:border-white/10 dark:bg-panel dark:text-mist dark:placeholder:text-slate-400"
        />
      </label>
    </div>
  );
}
