import { useState } from "react";
import { useDebouncedValue } from "../hooks/useDebouncedValue";
import { useJobs } from "../hooks/useJobs";
import { useTechStackOptions } from "../hooks/useTechStackOptions";
import { JobFiltersBar } from "../components/JobFiltersBar";
import { JobCard } from "../components/JobCard";
import { LoadingSkeleton } from "../components/LoadingSkeleton";
import { EmptyState, ErrorState } from "../components/EmptyState";
import { Pagination } from "../components/Pagination";

const PAGE_SIZE = 20;
// How long to wait after the user stops typing before firing a
// request -- short enough to feel responsive, long enough to avoid
// firing a request on every keystroke while actively typing.
const SEARCH_DEBOUNCE_MS = 350;

export function JobsPage() {
  const [titleInput, setTitleInput] = useState("");
  const [locationInput, setLocationInput] = useState("");
  const [experienceLevel, setExperienceLevel] = useState("");
  const [techStack, setTechStack] = useState<string[]>([]);
  const [page, setPage] = useState(1);

  const debouncedTitle = useDebouncedValue(titleInput, SEARCH_DEBOUNCE_MS);
  const debouncedLocation = useDebouncedValue(locationInput, SEARCH_DEBOUNCE_MS);

  const { data: techStackOptions } = useTechStackOptions();

  const { data, isLoading, isError, error } = useJobs({
    title: debouncedTitle || undefined,
    location: debouncedLocation || undefined,
    experience_level: experienceLevel || undefined,
    tech_stack: techStack.length > 0 ? techStack : undefined,
    page,
    page_size: PAGE_SIZE,
  });

  const hasActiveFilters =
    titleInput.trim() !== "" ||
    locationInput.trim() !== "" ||
    experienceLevel !== "" ||
    techStack.length > 0;

  function handleTitleChange(value: string) {
    setTitleInput(value);
    setPage(1); // any filter change resets to page 1 -- staying on page 4 of a new, smaller result set would just show an empty page
  }

  function handleLocationChange(value: string) {
    setLocationInput(value);
    setPage(1);
  }

  function handleExperienceLevelChange(value: string) {
    setExperienceLevel(value);
    setPage(1);
  }

  function handleTechStackChange(tags: string[]) {
    setTechStack(tags);
    setPage(1);
  }

  function handleClearFilters() {
    setTitleInput("");
    setLocationInput("");
    setExperienceLevel("");
    setTechStack([]);
    setPage(1);
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-8 sm:px-6 sm:py-10">
      <div className="mb-6">
        <h1 className="font-display text-2xl font-semibold tracking-tight text-ink dark:text-mist sm:text-3xl">
          Live job signals
        </h1>
        <p className="mt-1.5 text-sm text-slate dark:text-slate-400">
          Real postings tracked from company career pages, refreshed automatically.
        </p>
      </div>

      <div className="mb-5">
        <JobFiltersBar
          titleInput={titleInput}
          locationInput={locationInput}
          experienceLevel={experienceLevel}
          techStack={techStack}
          techStackOptions={techStackOptions ?? []}
          onTitleChange={handleTitleChange}
          onLocationChange={handleLocationChange}
          onExperienceLevelChange={handleExperienceLevelChange}
          onTechStackChange={handleTechStackChange}
        />

        {data && (
          <p className="mt-3 font-mono text-xs text-slate dark:text-slate-400">
            {data.total} {data.total === 1 ? "signal" : "signals"} found
          </p>
        )}
      </div>

      {isLoading && <LoadingSkeleton />}

      {isError && (
        <ErrorState message={error instanceof Error ? error.message : "Something went wrong."} />
      )}

      {!isLoading && !isError && data && data.items.length === 0 && (
        <EmptyState hasActiveFilters={hasActiveFilters} onClearFilters={handleClearFilters} />
      )}

      {!isLoading && !isError && data && data.items.length > 0 && (
        <>
          <div className="flex flex-col gap-3">
            {data.items.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>

          <div className="mt-6">
            <Pagination page={data.page} totalPages={data.total_pages} onPageChange={setPage} />
          </div>
        </>
      )}
    </main>
  );
}
