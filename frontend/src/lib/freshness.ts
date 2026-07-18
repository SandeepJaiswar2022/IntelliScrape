/**
 * Powers the design's signature element: each job card's left edge is
 * a vertical bar whose color intensity encodes how recently the
 * posting was updated. This is the fastest way to scan "what's new"
 * across dozens of listings -- the visual encodes real information,
 * it isn't decoration.
 *
 * Three tiers, deliberately simple:
 *   - "hot"   (<= 3 days)  -- full-opacity signal amber, bar + dot
 *   - "warm"  (<= 14 days) -- medium-opacity amber
 *   - "cold"  (older, or no timestamp at all) -- muted neutral
 */

export type FreshnessTier = "hot" | "warm" | "cold";

export function getFreshnessTier(sourceUpdatedAt: string | null): FreshnessTier {
  if (!sourceUpdatedAt) return "cold";

  const updatedAt = new Date(sourceUpdatedAt).getTime();
  const daysAgo = (Date.now() - updatedAt) / (1000 * 60 * 60 * 24);

  if (daysAgo <= 3) return "hot";
  if (daysAgo <= 14) return "warm";
  return "cold";
}

/** Tailwind classes for the left-edge signal bar, keyed by tier. */
export const FRESHNESS_BAR_CLASSES: Record<FreshnessTier, string> = {
  hot: "bg-signal dark:bg-signal-bright",
  warm: "bg-signal/40 dark:bg-signal-bright/40",
  cold: "bg-slate-light dark:bg-white/10",
};

/**
 * Human-readable relative time for the "updated Xd ago" tag.
 * Deliberately coarse (days, not hours/minutes) -- for a job board,
 * "3 days ago" is meaningfully more scannable than "3 days, 4 hours
 * ago" and matches the granularity job seekers actually care about.
 */
export function formatRelativeTime(sourceUpdatedAt: string | null): string {
  if (!sourceUpdatedAt) return "Date unknown";

  const updatedAt = new Date(sourceUpdatedAt).getTime();
  const daysAgo = Math.floor((Date.now() - updatedAt) / (1000 * 60 * 60 * 24));

  if (daysAgo <= 0) return "Today";
  if (daysAgo === 1) return "1 day ago";
  if (daysAgo < 30) return `${daysAgo} days ago`;

  const monthsAgo = Math.floor(daysAgo / 30);
  if (monthsAgo === 1) return "1 month ago";
  return `${monthsAgo} months ago`;
}
