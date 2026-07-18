import { useContext } from "react";
import { ThemeContext } from "../context/ThemeContext";

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    // A clear, actionable error for a mistake a developer would make
    // (using the hook outside the provider) -- fails loudly at the
    // point of misuse instead of silently returning undefined.
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
}
