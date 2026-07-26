import { EXPERIENCE_LEVELS } from "../types/job";

interface ExperienceLevelSelectProps {
  value: string;
  onChange: (value: string) => void;
}

/** Plain dropdown -- a fixed, small set of options doesn't need autocomplete. */
export function ExperienceLevelSelect({ value, onChange }: ExperienceLevelSelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="rounded-lg border border-slate-light bg-white px-3.5 py-2.5 text-sm text-ink
                 focus:border-signal
                 dark:border-white/10 dark:bg-panel dark:text-mist"
    >
      <option value="">Any experience level</option>
      {EXPERIENCE_LEVELS.map((level) => (
        <option key={level} value={level}>
          {level}
        </option>
      ))}
    </select>
  );
}
