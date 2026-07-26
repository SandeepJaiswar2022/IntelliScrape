import { MapPin, Search } from "lucide-react";
import { ExperienceLevelSelect } from "./ExperienceLevelSelect";
import { TechStackAutocomplete } from "./TechStackAutocomplete";

interface JobFiltersBarProps {
  titleInput: string;
  locationInput: string;
  experienceLevel: string;
  techStack: string[];
  techStackOptions: string[];
  onTitleChange: (value: string) => void;
  onLocationChange: (value: string) => void;
  onExperienceLevelChange: (value: string) => void;
  onTechStackChange: (tags: string[]) => void;
}

export function JobFiltersBar({
  titleInput,
  locationInput,
  experienceLevel,
  techStack,
  techStackOptions,
  onTitleChange,
  onLocationChange,
  onExperienceLevelChange,
  onTechStackChange,
}: JobFiltersBarProps) {
  return (
    <div className="flex flex-col gap-3">
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

      <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
        <ExperienceLevelSelect value={experienceLevel} onChange={onExperienceLevelChange} />
        <TechStackAutocomplete
          options={techStackOptions}
          selected={techStack}
          onChange={onTechStackChange}
        />
      </div>
    </div>
  );
}
