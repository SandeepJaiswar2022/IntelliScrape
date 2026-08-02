import { StrictMode, useState, type ReactNode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { QueryCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App } from "./App";
import { ThemeProvider } from "./context/ThemeContext";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ApiError } from "./lib/api";
import "./index.css";

/**
 * Constructs the QueryClient INSIDE a component (not at module scope)
 * specifically so it can close over `clearSession` from useAuth().
 * The global `onError` here is what makes an expired access token
 * (any query failing with a 401) automatically clear local auth state
 * -- which then sends the user back to /login on next render via the
 * route guards, with no separate polling/timer needed to notice the
 * token expired.
 */
function QueryProvider({ children }: { children: ReactNode }) {
  const { clearSession } = useAuth();

  const [queryClient] = useState(
    () =>
      new QueryClient({
        queryCache: new QueryCache({
          onError: (error) => {
            if (error instanceof ApiError && error.status === 401) {
              clearSession();
            }
          },
        }),
        defaultOptions: {
          queries: {
            staleTime: 60_000,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found in index.html");
}

createRoot(rootElement).render(
  <StrictMode>
    <BrowserRouter>
      <ThemeProvider>
        <AuthProvider>
          <QueryProvider>
            <App />
          </QueryProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  </StrictMode>
);