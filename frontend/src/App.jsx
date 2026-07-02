import { useEffect, useState } from "react";
import { APIProvider } from "@vis.gl/react-google-maps";

import Sidebar from "./components/Sidebar";
import StationMap from "./components/StationMap";
import RiskForecastTable from "./components/RiskForecastTable";
import DisasterEventsPage from "./components/DisasterEventsPage";
import useStationData from "./hooks/useStationData";

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;
const ACTIVE_PAGE_KEY = "viettelFloodRiskActivePage";

function getSavedActivePage() {
  return localStorage.getItem(ACTIVE_PAGE_KEY) || "overview";
}

export default function App() {
  const [activePage, setActivePage] = useState(getSavedActivePage);

  const stationData = useStationData();

  useEffect(() => {
    localStorage.setItem(ACTIVE_PAGE_KEY, activePage);
  }, [activePage]);

  return (
    <APIProvider apiKey={GOOGLE_MAPS_API_KEY}>
      <div className="app-shell">
        <Sidebar activePage={activePage} onPageChange={setActivePage} />

        <main className="main-content">
          {activePage === "overview" && (
            <StationMap pageType="overview" {...stationData} />
          )}

          {activePage === "weather" && (
            <StationMap pageType="weather" {...stationData} />
          )}

          {activePage === "disasters" && <DisasterEventsPage />}

          {activePage === "forecast" && <RiskForecastTable />}
        </main>
        {stationData.isBackendUpdating && (
          <div className="refresh-overlay">
            <div className="refresh-modal">
              <div className="refresh-spinner" />
              <h2>Please wait</h2>
              <p>{stationData.refreshMessage}</p>
            </div>
          </div>
        )}
      </div>
    </APIProvider>
  );
}