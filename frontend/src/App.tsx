import { Route, Routes } from "react-router-dom";
import { Navbar } from "./components/Navbar";
import { JobsPage } from "./pages/JobsPage";
import { JobDetailPage } from "./pages/JobDetailPage";

export function App() {
  return (
    <div className="min-h-screen bg-canvas dark:bg-midnight">
      <Navbar />
      <Routes>
        <Route path="/" element={<JobsPage />} />
        <Route path="/jobs/:jobId" element={<JobDetailPage />} />
      </Routes>
    </div>
  );
}
