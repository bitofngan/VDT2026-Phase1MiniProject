import { useCallback, useEffect, useRef, useState } from "react";

const AUTO_REFRESH_MS = 30 * 60 * 1000;
const MANUAL_REFRESH_COOLDOWN_MS = 10 * 60 * 1000;

function getErrorMessage(errorData) {
  if (!errorData) return "Unknown error.";

  if (typeof errorData.detail === "string") {
    return errorData.detail;
  }

  if (typeof errorData.detail === "object") {
    return errorData.detail.message || JSON.stringify(errorData.detail, null, 2);
  }

  if (typeof errorData.message === "string") {
    return errorData.message;
  }

  return JSON.stringify(errorData, null, 2);
}

export default function useStationData() {
  const [currentStations, setCurrentStations] = useState([]);
  const [forecastStations, setForecastStations] = useState([]);
  const [forecastTimes, setForecastTimes] = useState([]);

  const [lastUpdated, setLastUpdated] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isBackendUpdating, setIsBackendUpdating] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState("");

  const timerRef = useRef(null);
  const lastManualRefreshRef = useRef(0);

  const fetchFrontendData = useCallback(async () => {
    const [currentRes, forecastRes, timesRes] = await Promise.all([
      fetch("http://127.0.0.1:8000/api/stations/current"),
      fetch("http://127.0.0.1:8000/api/stations/forecast"),
      fetch("http://127.0.0.1:8000/api/forecast-times"),
    ]);

    const [currentData, forecastData, timesData] = await Promise.all([
      currentRes.json(),
      forecastRes.json(),
      timesRes.json(),
    ]);

    setCurrentStations(currentData);
    setForecastStations(forecastData);
    setForecastTimes(timesData);
    setLastUpdated(new Date());
  }, []);

  const refreshWeatherFromBackend = useCallback(async () => {
    setIsRefreshing(true);
    setIsBackendUpdating(true);
    setRefreshMessage("Please wait. Fetching latest weather data and recalculating flood risk...");

    try {
      const res = await fetch("http://127.0.0.1:8000/api/admin/refresh-weather", {
        method: "POST",
      });

      if (!res.ok) {
        const error = await res.json();
        throw new Error(getErrorMessage(error));
      }

      await fetchFrontendData();
      setRefreshMessage("Weather data updated successfully.");
    } catch (err) {
      console.error(err);
      setRefreshMessage(String(err.message || err));
    } finally {
      setIsRefreshing(false);

      setTimeout(() => {
        setIsBackendUpdating(false);
        setRefreshMessage("");
      }, 1200);
    }
  }, [fetchFrontendData]);

  const refreshNow = useCallback(() => {
    const now = Date.now();

    if (now - lastManualRefreshRef.current < MANUAL_REFRESH_COOLDOWN_MS) {
      const remaining = Math.ceil(
        (MANUAL_REFRESH_COOLDOWN_MS - (now - lastManualRefreshRef.current)) / 1000
      );

      setIsBackendUpdating(true);
      setRefreshMessage(`Please wait ${remaining} seconds before refreshing again.`);

      setTimeout(() => {
        setIsBackendUpdating(false);
        setRefreshMessage("");
      }, 1500);

      return;
    }

    lastManualRefreshRef.current = now;
    refreshWeatherFromBackend();

    if (timerRef.current) clearInterval(timerRef.current);
    timerRef.current = setInterval(refreshWeatherFromBackend, AUTO_REFRESH_MS);
  }, [refreshWeatherFromBackend]);

  useEffect(() => {
    fetchFrontendData();

    timerRef.current = setInterval(refreshWeatherFromBackend, AUTO_REFRESH_MS);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchFrontendData, refreshWeatherFromBackend]);

  return {
    currentStations,
    forecastStations,
    forecastTimes,
    lastUpdated,
    isRefreshing,
    isBackendUpdating,
    refreshMessage,
    refreshNow,
  };
}