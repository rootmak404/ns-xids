import { Routes, Route } from "react-router-dom";
import Sidebar from "./components/Sidebar.jsx";
import { api } from "./api/client.js";
import { usePolling } from "./hooks/usePolling.js";

import Overview from "./pages/Overview.jsx";
import LiveMonitoring from "./pages/LiveMonitoring.jsx";
import Alerts from "./pages/Alerts.jsx";
import Explainability from "./pages/Explainability.jsx";
import Analytics from "./pages/Analytics.jsx";
import TestData from "./pages/TestData.jsx";

export default function App() {
  const { data: status } = usePolling(() => api.monitoringStatus(), 5000);

  return (
    <div className="flex h-screen bg-bg text-text">
      <Sidebar monitoringStatus={status?.status} />
      <main className="flex-1 overflow-y-auto px-8 py-6">
        <Routes>
          <Route path="/" element={<Overview />} />
          <Route path="/live" element={<LiveMonitoring />} />
          <Route path="/alerts" element={<Alerts />} />
          <Route path="/explainability" element={<Explainability />} />
          <Route path="/explainability/:eventId" element={<Explainability />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/test-data" element={<TestData />} />
        </Routes>
      </main>
    </div>
  );
}
