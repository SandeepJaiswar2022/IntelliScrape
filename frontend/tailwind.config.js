/** @type {import('tailwindcss').Config} */
export default {
  // Class-based dark mode: we toggle a `dark` class on <html> ourselves
  // (see src/context/ThemeContext.tsx) instead of relying purely on
  // the OS-level `prefers-color-scheme` media query -- this is what
  // lets a user's manual toggle override their system setting and
  // persist across visits.
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      // --- Design tokens ---
      // Named per the design plan: a "market signal" visual language
      // for a job-intelligence product. Deliberately not the generic
      // cream+serif or black+neon defaults -- see design notes in
      // src/index.css for the full rationale.
      colors: {
        ink: "#12151C", // primary text, light mode
        canvas: "#F7F8FA", // page background, light mode
        slate: {
          DEFAULT: "#5B6472", // muted text / borders, light mode
          light: "#E4E7EC", // hairline dividers, light mode
          300: "#B4BAC5", // secondary text, dark mode
          400: "#8A93A3", // muted text, dark mode
        },
        midnight: "#0B0D12", // page background, dark mode
        panel: "#151922", // card/surface background, dark mode
        mist: "#EDEFF3", // primary text, dark mode
        signal: {
          DEFAULT: "#F2A93B", // the one accent color -- "signal amber"
          bright: "#FFB443", // slightly boosted for dark-mode contrast
        },
      },
      fontFamily: {
        // Display face: distinctive, geometric, used for headings only
        display: ["'Space Grotesk'", "sans-serif"],
        // Body face: quiet, highly readable for dense listings
        sans: ["'Inter'", "sans-serif"],
        // Utility/data face: ties tags, counts, and timestamps to the
        // product's "market signal / data feed" identity
        mono: ["'IBM Plex Mono'", "monospace"],
      },
    },
  },
  plugins: [],
};
