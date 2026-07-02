import { useCallback, useEffect, useRef, useState } from "react";

const AUTO_REFRESH_MS = 30 * 60 * 1000;

export default function useStationData() {
  const [currentStations, setCurrentStations] = useState([]);
  const [forecastStations, setForecastStations] = useState([]);
  const [forecastTimes, setForecastTimes] = useState([]);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const timerRef = useRef(null);

  const fetchAllData = useCallback(async () => {
    setIsRefreshing(true);

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
      console.error("Failed to refresh station data:", err);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  const refreshNow = useCallback(() => {
    fetchAllData();

    if (timerRef.current) clearInterval(timerRef.current);

    timerRef.current = setInterval(() => {
      fetchAllData();
    }, AUTO_REFRESH_MS);
  }, [fetchAllData]);

  useEffect(() => {
    fetchAllData();

    timerRef.current = setInterval(() => {
      fetchAllData();
    }, AUTO_REFRESH_MS);

    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [fetchAllData]);

  return {
    currentStations,
    forecastStations,
    forecastTimes,
    lastUpdated,
    isRefreshing,
    refreshNow,
  };
}