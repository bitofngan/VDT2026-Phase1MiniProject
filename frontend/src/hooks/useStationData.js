import { useCallback, useEffect, useRef, useState } from "react";

const AUTO_REFRESH_MS = 30 * 60 * 1000;
const MANUAL_REFRESH_COOLDOWN_MS = 10 * 60 * 1000;

export default function useStationData() {
  const [currentStations, setCurrentStations] = useState([]);
  const [forecastStations, setForecastStations] = useState([]);
  const [forecastTimes, setForecastTimes] = useState([]);

  const [lastUpdated, setLastUpdated] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState("");

  const timerRef = useRef(null);
  const lastManualRefreshRef = useRef(0);

  const fetchFrontendData = useCallback(async () => {
    setIsRefreshing(true);
    setRefreshMessage("Loading latest data from database...");

    try {
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
    } catch (err) {
      console.error("Failed to load frontend data:", err);
      setRefreshMessage("Failed to load data from database.");
    } finally {
      setIsRefreshing(false);
      setTimeout(() => setRefreshMessage(""), 1000);
    }
  }, []);

  const refreshNow = useCallback(() => {
    const now = Date.now();

    if (now - lastManualRefreshRef.current < MANUAL_REFRESH_COOLDOWN_MS) {
      const remaining = Math.ceil(
        (MANUAL_REFRESH_COOLDOWN_MS - (now - lastManualRefreshRef.current)) /
          1000
      );

      setRefreshMessage(`Please wait ${remaining} seconds before refreshing again.`);
      setTimeout(() => setRefreshMessage(""), 1500);
      return;
    }

    lastManualRefreshRef.current = now;
    fetchFrontendData();
  }, [fetchFrontendData]);

  useEffect(() => {
    fetchFrontendData();

    timerRef.current = setInterval(fetchFrontendData, AUTO_REFRESH_MS);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchFrontendData]);

  return {
    currentStations,
    forecastStations,
    forecastTimes,
    lastUpdated,
    isRefreshing,
    isBackendUpdating: false,
    refreshMessage,
    refreshNow,
  };
}