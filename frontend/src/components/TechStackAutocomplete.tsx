import { useEffect, useMemo, useRef, useState } from "react";
import { Search, X } from "lucide-react";

interface TechStackAutocompleteProps {
  options: string[];
  selected: string[];
  onChange: (tags: string[]) => void;
}

const MAX_SUGGESTIONS_SHOWN = 8;

/**
 * A searchable multi-select tag input: type to filter a (potentially
 * large) list of options, click a suggestion to add it as a removable
 * chip. Built from scratch rather than pulling in a component library
 * -- the interaction is simple enough (filter + select + remove) that
 * a dedicated dependency isn't justified for one field.
 */
export function TechStackAutocomplete({ options, selected, onChange }: TechStackAutocompleteProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Close the suggestion dropdown when clicking anywhere outside this
  // component -- standard autocomplete behavior, implemented via a
  // document-level listener since the click could land anywhere.
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const suggestions = useMemo(() => {
    const lowerQuery = query.trim().toLowerCase();
    return options
      .filter((option) => !selected.includes(option))
      .filter((option) => (lowerQuery ? option.toLowerCase().includes(lowerQuery) : true))
      .slice(0, MAX_SUGGESTIONS_SHOWN);
  }, [options, selected, query]);

  function addTag(tag: string) {
    onChange([...selected, tag]);
    setQuery("");
    // Deliberately keep the dropdown open after selecting -- picking
    // several tags in a row (a very likely use case here) shouldn't
    // require re-clicking the input each time.
  }

  function removeTag(tag: string) {
    onChange(selected.filter((t) => t !== tag));
  }

  return (
    <div ref={containerRef} className="relative flex-1">
      <div className="relative">
        <Search
          size={16}
          strokeWidth={2}
          className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-slate dark:text-slate-400"
        />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onFocus={() => setIsOpen(true)}
          onKeyDown={(e) => {
            if (e.key === "Escape") setIsOpen(false);
          }}
          placeholder="Tech stack — e.g. Python, React"
          className="w-full rounded-lg border border-slate-light bg-white py-2.5 pl-10 pr-3.5
                     text-sm text-ink placeholder:text-slate/70
                     focus:border-signal
                     dark:border-white/10 dark:bg-panel dark:text-mist dark:placeholder:text-slate-400"
        />
      </div>

      {isOpen && suggestions.length > 0 && (
        <ul
          className="absolute z-10 mt-1.5 w-full overflow-hidden rounded-lg border border-slate-light
                     bg-white shadow-lg
                     dark:border-white/10 dark:bg-panel"
        >
          {suggestions.map((option) => (
            <li key={option}>
              <button
                type="button"
                onClick={() => addTag(option)}
                className="w-full px-3.5 py-2 text-left font-mono text-sm text-ink
                           hover:bg-slate-light/50
                           dark:text-mist dark:hover:bg-white/5"
              >
                {option}
              </button>
            </li>
          ))}
        </ul>
      )}

      {selected.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5">
          {selected.map((tag) => (
            <span
              key={tag}
              className="inline-flex items-center gap-1 rounded-full border border-signal/30
                         bg-signal/10 px-2.5 py-1 font-mono text-xs text-ink
                         dark:border-signal-bright/30 dark:bg-signal-bright/10 dark:text-mist"
            >
              {tag}
              <button
                type="button"
                onClick={() => removeTag(tag)}
                aria-label={`Remove ${tag} filter`}
                className="text-slate hover:text-ink dark:text-slate-400 dark:hover:text-mist"
              >
                <X size={12} strokeWidth={2.5} />
              </button>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
