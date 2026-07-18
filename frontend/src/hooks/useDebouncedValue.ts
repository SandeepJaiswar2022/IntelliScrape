import { useEffect, useState } from "react";

/**
 * Returns a debounced copy of `value` that only updates after `delayMs`
 * has passed without `value` changing again. Used on the search/filter
 * inputs so we don't fire an API request on every single keystroke --
 * only once the user pauses typing.
 */
export function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    // If `value` changes again before the timer fires, this cleanup
    // cancels the stale timer -- standard debounce-via-useEffect pattern.
    return () => clearTimeout(timer);
  }, [value, delayMs]);

  return debounced;
}
