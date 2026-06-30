import { useEffect, useMemo, useState } from "react";
import { Map } from "@vis.gl/react-google-maps";

import StationToolbar from "./StationToolbar";
import StationInfoPanel from "./StationInfoPanel";
import AutoFitProvince from "./AutoFitProvince";
import ProvinceBoundary from "./ProvinceBoundary";
import ClusteredStationMarkers from "./ClusteredStationMarkers";
import FloodAffectedZones from "./FloodAffectedZones";

const AUTO_REFRESH_MS = 30 * 60 * 1000;
const MANUAL_REFRESH_COOLDOWN_MS = 2 * 60 * 1000;

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

export default function StationMap() {
  const [stations, setStations] = useState([]);
  const [selectedStation, setSelectedStation] = useState(null);

  const [mode, setMode] = useState("forecast");
  const [province, setProvince] = useState("ALL");

  const [forecastTimes, setForecastTimes] = useState([]);
  const [selectedForecastTime, setSelectedForecastTime] = useState("WORST");

  const [lastUpdated, setLastUpdated] = useState(null);
  const [lastManualRefresh, setLastManualRefresh] = useState(0);
  const [isRefreshing, setIsRefreshing] = useState(false);

  function fetchStations() {
    setIsRefreshing(true);

    let url = "http://127.0.0.1:8000/api/stations/current";

    if (mode === "forecast") {
      const params = new URLSearchParams();

      if (selectedForecastTime !== "WORST") {
        params.append("forecast_time_vn", selectedForecastTime);
      }

      url = `http://127.0.0.1:8000/api/stations/forecast?${params.toString()}`;
    }

    fetch(url)
      .then((res) => res.json())
      .then((data) => {
        setStations(data);
        setLastUpdated(new Date());
      })
      .catch((err) => console.error("Failed to load stations:", err))
      .finally(() => setIsRefreshing(false));
  }

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/forecast-times")
      .then((res) => res.json())
      .then((data) => setForecastTimes(data))
      .catch((err) => console.error("Failed to load forecast times:", err));
  }, []);

  useEffect(() => {
    fetchStations();

    const interval = setInterval(() => {
      fetchStations();
    }, AUTO_REFRESH_MS);

    return () => clearInterval(interval);
  }, [mode, selectedForecastTime]);

  function handleManualRefresh() {
    const now = Date.now();

    if (now - lastManualRefresh < MANUAL_REFRESH_COOLDOWN_MS) return;

    setLastManualRefresh(now);
    fetchStations();
  }

  function handleModeChange(newMode) {
    setMode(newMode);
    setSelectedStation(null);
  }

  function handleProvinceChange(newProvince) {
    setProvince(newProvince);
    setSelectedStation(null);
  }

  function handleForecastTimeChange(newTime) {
    setSelectedForecastTime(newTime);
    setSelectedStation(null);
  }

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
    if (province === "ALL") return cleanedStations;

    return cleanedStations.filter((station) => station.province === province);
  }, [cleanedStations, province]);

  const refreshDisabled =
    isRefreshing || Date.now() - lastManualRefresh < MANUAL_REFRESH_COOLDOWN_MS;

  return (
    <div style={{ height: "100vh", position: "relative" }}>
      <StationToolbar
        mode={mode}
        province={province}
        provinces={provinces}
        forecastTimes={forecastTimes}
        selectedForecastTime={selectedForecastTime}
        stationCount={filteredStations.length}
        isRefreshing={isRefreshing}
        refreshDisabled={refreshDisabled}
        lastUpdated={lastUpdated}
        onModeChange={handleModeChange}
        onProvinceChange={handleProvinceChange}
        onForecastTimeChange={handleForecastTimeChange}
        onRefresh={handleManualRefresh}
      />

      <StationInfoPanel
        station={selectedStation}
        mode={mode}
        onClose={() => setSelectedStation(null)}
      />

      <Map
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
      </Map>
    </div>
  );
}