import { Navbar } from "./components/Navbar";
import { JobsPage } from "./pages/JobsPage";

export function App() {
  return (
    <div className="min-h-screen bg-canvas dark:bg-midnight">
      <Navbar />
      <JobsPage />
    </div>
  );
}
