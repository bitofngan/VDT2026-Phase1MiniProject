import { useMemo, useState } from "react";
import { Map as GoogleMap } from "@vis.gl/react-google-maps";

import StationToolbar from "./StationToolbar";
import StationInfoPanel from "./StationInfoPanel";
import AutoFitProvince from "./AutoFitProvince";
import ProvinceBoundary from "./ProvinceBoundary";
import ClusteredStationMarkers from "./ClusteredStationMarkers";
import FloodAffectedZones from "./FloodAffectedZones";

const RISK_ORDER = {
  HIGH: 4,
  MEDIUM: 3,
  LOW: 2,
  SAFE: 1,
  UNKNOWN: 0,
};

function normalizeProvinceName(text) {
  return String(text || "")
    .trim()
    .toLowerCase()
    .replace(/đ/g, "d")
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[-–—_.]/g, " ")
    .replace(/\s+/g, " ");
}

function cleanProvinceName(province) {
  const key = normalizeProvinceName(province);

  if (
    key === "thanh pho ho chi minh" ||
    key === "tp ho chi minh" ||
    key === "ho chi minh city" ||
    key === "ho chi minh" ||
    key === "hcmc"
  ) {
    return "TPHCM";
  }

  return province;
}

function getStationId(station) {
  return station.id || station.station_id || station.telecom_station_id;
}

function getRiskLevel(station) {
  return String(
    station.risk_level || station.flood_risk || station.risk || "UNKNOWN"
  ).toUpperCase();
}

function isAtRisk(station) {
  const risk = getRiskLevel(station);
  return risk === "LOW" || risk === "MEDIUM" || risk === "HIGH";
}

function getWorstForecastByStation(forecastStations) {
  const result = new Map();

  forecastStations.forEach((station) => {
    const id = getStationId(station);
    if (!id) return;

    const currentRisk = getRiskLevel(station);
    const existing = result.get(id);

    if (!existing) {
      result.set(id, station);
      return;
    }

    const existingRisk = getRiskLevel(existing);

    if ((RISK_ORDER[currentRisk] || 0) > (RISK_ORDER[existingRisk] || 0)) {
      result.set(id, station);
    }
  });

  return result;
}

export default function StationMap({
  pageType = "overview",
  currentStations = [],
  forecastStations = [],
  forecastTimes = [],
  lastUpdated,
  isRefreshing,
  refreshNow,
}) {
  const [selectedStation, setSelectedStation] = useState(null);

  const [mode, setMode] = useState("forecast");
  const [province, setProvince] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("ALL");
  const [selectedForecastTime, setSelectedForecastTime] = useState("WORST");

  const worstForecastByStation = useMemo(() => {
    return getWorstForecastByStation(forecastStations);
  }, [forecastStations]);

  const currentStationsWithRisk = useMemo(() => {
    return currentStations.map((station) => {
      const id = getStationId(station);
      const forecast = worstForecastByStation.get(id);

      if (!forecast) return station;

      return {
        ...station,
        risk_level: getRiskLevel(forecast),
        flood_risk: getRiskLevel(forecast),
        forecast_time_vn: forecast.forecast_time_vn,
        rain_3h_mm:
          forecast.rain_3h_mm ??
          forecast.rainfall_mm ??
          forecast.precipitation_mm,
        weather_station_name: forecast.weather_station_name,
      };
    });
  }, [currentStations, worstForecastByStation]);

  const stations =
    mode === "forecast" ? forecastStations : currentStationsWithRisk;

  const cleanedStations = useMemo(() => {
    return stations.map((station) => ({
      ...station,
      province: cleanProvinceName(station.province),
    }));
  }, [stations]);

  const provinces = useMemo(() => {
    return [
      ...new Set(
        cleanedStations.map((station) => station.province).filter(Boolean)
      ),
    ].sort();
  }, [cleanedStations]);

  const filteredStations = useMemo(() => {
    let result = cleanedStations;

    if (province !== "ALL") {
      result = result.filter((station) => station.province === province);
    }

    if (mode === "forecast" && selectedForecastTime !== "WORST") {
      result = result.filter(
        (station) => station.forecast_time_vn === selectedForecastTime
      );
    }

    if (riskFilter === "AT_RISK") {
      result = result.filter(isAtRisk);
    } else if (riskFilter !== "ALL") {
      result = result.filter((station) => getRiskLevel(station) === riskFilter);
    }

    return result;
  }, [cleanedStations, province, riskFilter, mode, selectedForecastTime]);

  const stats = useMemo(() => {
    const counts = {
      UNKNOWN: 0,
      SAFE: 0,
      LOW: 0,
      MEDIUM: 0,
      HIGH: 0,
    };

    cleanedStations.forEach((station) => {
      const risk = getRiskLevel(station);
      if (counts[risk] !== undefined) counts[risk] += 1;
      else counts.UNKNOWN += 1;
    });

    return {
      total: cleanedStations.length,
      visible: filteredStations.length,
      atRisk: counts.LOW + counts.MEDIUM + counts.HIGH,
      ...counts,
    };
  }, [cleanedStations, filteredStations]);

  return (
    <div className="dashboard-page">
      <header className="dashboard-header">
        <div>
          <h1>
            {pageType === "weather"
              ? "Weather Map"
              : "Viettel Flood Risk Dashboard"}
          </h1>
          <p>
            {pageType === "weather"
              ? "Large map view for monitoring weather and station conditions"
              : "Weather forecast and telecom station flood monitoring"}
          </p>
        </div>

        <div className="header-actions">
          <button
            className="refresh-button"
            onClick={refreshNow}
            disabled={isRefreshing}
          >
            {isRefreshing ? "Refreshing..." : "Refresh"}
          </button>

          <div className="backend-status">● Backend Connected</div>
        </div>
      </header>

      {pageType === "overview" && (
        <section className="stat-grid">
          <StatCard
            title="Total Stations"
            value={stats.total}
            subtitle={`${stats.visible} visible`}
          />
          <StatCard
            title="At-Risk Stations"
            value={stats.atRisk}
            subtitle="Low / Medium / High"
          />
          <StatCard
            title="High Risk"
            value={stats.HIGH}
            subtitle="Highest warning level"
          />
          <StatCard
            title="Medium Risk"
            value={stats.MEDIUM}
            subtitle="Monitor closely"
          />
          <StatCard
            title="Safe Stations"
            value={stats.SAFE}
            subtitle={`${stats.UNKNOWN} unknown`}
          />
        </section>
      )}

      <section
        className={
          pageType === "weather" ? "dashboard-grid map-only" : "dashboard-grid"
        }
      >
        <div className="map-card">
          <StationToolbar
            mode={mode}
            province={province}
            provinces={provinces}
            forecastTimes={forecastTimes}
            selectedForecastTime={selectedForecastTime}
            riskFilter={riskFilter}
            stationCount={filteredStations.length}
            lastUpdated={lastUpdated}
            onModeChange={(value) => {
              setMode(value);
              setSelectedStation(null);
              if (value === "current") setSelectedForecastTime("WORST");
            }}
            onProvinceChange={(value) => {
              setProvince(value);
              setSelectedStation(null);
            }}
            onRiskFilterChange={(value) => {
              setRiskFilter(value);
              setSelectedStation(null);
            }}
            onForecastTimeChange={(value) => {
              setSelectedForecastTime(value);
              setSelectedStation(null);
            }}
          />

          <div className="map-container">
            <GoogleMap
              defaultCenter={{ lat: 16.0544, lng: 108.2022 }}
              defaultZoom={6}
              mapId="telecom-flood-risk-map"
              style={{ width: "100%", height: "100%" }}
            >
              <ProvinceBoundary province={province} />
              <AutoFitProvince stations={filteredStations} province={province} />

              {mode === "forecast" && (
                <FloodAffectedZones stations={filteredStations} />
              )}

              <ClusteredStationMarkers
                stations={filteredStations}
                onStationClick={setSelectedStation}
                mode={mode}
              />
            </GoogleMap>
          </div>
        </div>

        {pageType === "overview" && (
          <aside className="details-card">
            <h2>Station Details</h2>
            <p>Select a station on the map</p>

            <StationInfoPanel
              station={selectedStation}
              mode={mode}
              onClose={() => setSelectedStation(null)}
            />

            <div className="risk-summary">
              <h3>Risk Summary</h3>
              <RiskRow label="High" value={stats.HIGH} />
              <RiskRow label="Medium" value={stats.MEDIUM} />
              <RiskRow label="Low" value={stats.LOW} />
              <RiskRow label="Safe" value={stats.SAFE} />
              <RiskRow label="Unknown" value={stats.UNKNOWN} />
            </div>
          </aside>
        )}
      </section>
    </div>
  );
}

function StatCard({ title, value, subtitle }) {
  return (
    <div className="stat-card">
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-subtitle">{subtitle}</div>
    </div>
  );
}

function RiskRow({ label, value }) {
  return (
    <div className="risk-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}