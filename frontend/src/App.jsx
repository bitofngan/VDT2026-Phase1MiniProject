import { useState } from "react";
import { APIProvider } from "@vis.gl/react-google-maps";

import Sidebar from "./components/Sidebar";
import StationMap from "./components/StationMap";
import RiskForecastTable from "./components/RiskForecastTable";
import useStationData from "./hooks/useStationData";

const GOOGLE_MAPS_API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

export default function App() {
  const [activePage, setActivePage] = useState("overview");

  const stationData = useStationData();

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

          {activePage === "disasters" && (
            <BlankPage
              title="Disaster Events"
              description="This page will manage storms, floods, affected provinces, and impacted telecom stations."
            />
          )}

          {activePage === "forecast" && (
            <RiskForecastTable
              stations={stationData.forecastStations}
              lastUpdated={stationData.lastUpdated}
              isRefreshing={stationData.isRefreshing}
              onRefresh={stationData.refreshNow}
            />
          )}
        </main>
      </div>
    </APIProvider>
  );
}

function BlankPage({ title, description }) {
  return (
    <div className="blank-page">
      <h1>{title}</h1>
      <p>{description}</p>
    </div>
  );
}