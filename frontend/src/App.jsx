import { useEffect, useState } from "react";
import { APIProvider } from "@vis.gl/react-google-maps";

import Sidebar from "./components/Sidebar";
import StationMap from "./components/StationMap";
import RiskForecastTable from "./components/RiskForecastTable";
import DisasterEventsPage from "./components/DisasterEventsPage";
import LoginPage from "./components/LoginPage";
import useStationData from "./hooks/useStationData";

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
const ACTIVE_PAGE_KEY = "viettelFloodRiskActivePage";

function getSavedActivePage() {
  return localStorage.getItem(ACTIVE_PAGE_KEY) || "overview";
}

export default function App() {
  const [activePage, setActivePage] = useState(getSavedActivePage);
  const [adminToken, setAdminToken] = useState(
    sessionStorage.getItem("adminToken")
  );

  const stationData = useStationData();

  useEffect(() => {
    localStorage.setItem(ACTIVE_PAGE_KEY, activePage);
  }, [activePage]);

  function handleLogout() {
    sessionStorage.removeItem("adminToken");
    setAdminToken(null);
  }

  return (
    <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
      <div className="app-shell">
        <Sidebar
          activePage={activePage}
          onPageChange={setActivePage}
          isAdminLoggedIn={Boolean(adminToken)}
          onLogout={handleLogout}
        />

        <main className="main-content">
          {activePage === "overview" && (
            <StationMap pageType="overview" {...stationData} />
          )}

          {activePage === "weather" && (
            <StationMap pageType="weather" {...stationData} />
          )}

          {activePage === "disasters" && <DisasterEventsPage />}

          {activePage === "forecast" && <RiskForecastTable />}

          {activePage === "admin" &&
            (adminToken ? (
              <AdminPage token={adminToken} onLogout={handleLogout} />
            ) : (
              <LoginPage onLogin={setAdminToken} />
            ))}
        </main>
      </div>
    </APIProvider>
  );
}

function AdminPage({ token, onLogout }) {
  async function callAdminEndpoint(endpoint) {
    const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.detail || "Admin action failed.");
      return;
    }

    alert(data.message || "Admin action completed.");
  }

  return (
    <div className="blank-page">
      <h1>Admin Tools</h1>
      <p>Run backend update tasks manually.</p>

      <div className="admin-actions">
        <button
          className="refresh-button"
          onClick={() => callAdminEndpoint("/api/admin/refresh-weather")}
        >
          Force Weather Update
        </button>

        <button
          className="refresh-button"
          onClick={() => callAdminEndpoint("/api/admin/refresh-disasters")}
        >
          Refresh Disaster Events
        </button>

        <button
          className="refresh-button"
          onClick={() => callAdminEndpoint("/api/admin/refresh-all")}
        >
          Refresh All Data
        </button>

        <button className="refresh-button logout-button" onClick={onLogout}>
          Logout
        </button>
      </div>
    </div>
  );
}