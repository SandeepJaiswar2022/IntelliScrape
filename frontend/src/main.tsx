import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";
import { ThemeProvider } from "./context/ThemeContext";
import "./index.css";

// One shared QueryClient for the whole app. Defaults tuned for a job
// board specifically: postings don't change second-to-second, so
// there's no reason to refetch on every window focus (React Query's
// default) -- that would just be extra load against the backend for
// data that's realistically fresh for minutes at a time.
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000, // 1 minute -- cached results are reused without refetching within this window
      refetchOnWindowFocus: false,
    },
  },
});

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found in index.html");
}

createRoot(rootElement).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </QueryClientProvider>
  </StrictMode>
);
