import { useEffect, useMemo, useState } from "react";

const RISK_ORDER = {
  HIGH: 1,
  MEDIUM: 2,
  LOW: 3,
  UNKNOWN: 4,
  SAFE: 5,
};

function getRiskLevel(station) {
  return String(
    station.risk_level || station.flood_risk || station.risk || "UNKNOWN"
  ).toUpperCase();
}

function isAtRisk(station) {
  const risk = getRiskLevel(station);
  return risk === "LOW" || risk === "MEDIUM" || risk === "HIGH";
}

function formatRainfall(value) {
  if (value === undefined || value === null || value === "") return "-";

  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) return "-";

  return numberValue.toFixed(2);
}

function formatForecastTime(value) {
  if (!value) return "-";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  const day = String(date.getDate()).padStart(2, "0");
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const year = date.getFullYear();

  const hour = String(date.getHours()).padStart(2, "0");
  const minute = String(date.getMinutes()).padStart(2, "0");
  const second = String(date.getSeconds()).padStart(2, "0");

  return `${day}/${month}/${year} - ${hour}:${minute}:${second}`;
}

export default function RiskForecastTable() {
  const [stations, setStations] = useState([]);
  const [provinceFilter, setProvinceFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("AT_RISK");
  const [searchText, setSearchText] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdated, setLastUpdated] = useState(null);

  async function fetchRiskForecastTable() {
    setIsLoading(true);

    try {
      const res = await fetch("http://127.0.0.1:8000/api/risk-forecast-table");
      const data = await res.json();

      setStations(data);
      setLastUpdated(new Date());
    } catch (err) {
      console.error("Failed to load risk forecast table:", err);
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    fetchRiskForecastTable();
  }, []);

  const provinces = useMemo(() => {
    return [...new Set(stations.map((s) => s.province).filter(Boolean))].sort();
  }, [stations]);

  const filteredStations = useMemo(() => {
    let result = [...stations];

    if (provinceFilter !== "ALL") {
      result = result.filter((station) => station.province === provinceFilter);
    }

    if (riskFilter === "AT_RISK") {
      result = result.filter(isAtRisk);
    } else if (riskFilter !== "ALL") {
      result = result.filter((station) => getRiskLevel(station) === riskFilter);
    }

    if (searchText.trim()) {
      const keyword = searchText.trim().toLowerCase();

      result = result.filter((station) => {
        return (
          String(station.id || "").toLowerCase().includes(keyword) ||
          String(station.name || "").toLowerCase().includes(keyword) ||
          String(station.province || "").toLowerCase().includes(keyword) ||
          String(station.weather_station_name || "")
            .toLowerCase()
            .includes(keyword)
        );
      });
    }

    result.sort((a, b) => {
      const riskA = getRiskLevel(a);
      const riskB = getRiskLevel(b);

      return (RISK_ORDER[riskA] || 99) - (RISK_ORDER[riskB] || 99);
    });

    return result;
  }, [stations, provinceFilter, riskFilter, searchText]);

  const summary = useMemo(() => {
    return {
      total: stations.length,
      shown: filteredStations.length,
      high: stations.filter((s) => getRiskLevel(s) === "HIGH").length,
      medium: stations.filter((s) => getRiskLevel(s) === "MEDIUM").length,
      low: stations.filter((s) => getRiskLevel(s) === "LOW").length,
    };
  }, [stations, filteredStations]);

  return (
    <div className="forecast-page">
      <header className="forecast-header">
        <div>
          <h1>Risk Forecast</h1>
          <p>
            Stations with predicted flood risk in the next 5–7 days
            {lastUpdated ? ` · Updated ${lastUpdated.toLocaleTimeString()}` : ""}
          </p>
        </div>

        <button
          className="refresh-button"
          onClick={fetchRiskForecastTable}
          disabled={isLoading}
        >
          {isLoading ? "Loading..." : "Refresh"}
        </button>
      </header>

      <section className="forecast-summary-grid">
        <ForecastSummaryCard title="At-Risk Rows" value={summary.total} />
        <ForecastSummaryCard title="Shown" value={summary.shown} />
        <ForecastSummaryCard title="High Risk" value={summary.high} />
        <ForecastSummaryCard title="Medium Risk" value={summary.medium} />
        <ForecastSummaryCard title="Low Risk" value={summary.low} />
      </section>

      <section className="forecast-table-card">
        <div className="forecast-filters">
          <label className="filter-field">
            <span>Search</span>
            <input
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder="Search station, province, weather station..."
            />
          </label>

          <label className="filter-field">
            <span>Province</span>
            <select
              value={provinceFilter}
              onChange={(e) => setProvinceFilter(e.target.value)}
            >
              <option value="ALL">All provinces</option>
              {provinces.map((province) => (
                <option key={province} value={province}>
                  {province}
                </option>
              ))}
            </select>
          </label>

          <label className="filter-field">
            <span>Risk level</span>
            <select
              value={riskFilter}
              onChange={(e) => setRiskFilter(e.target.value)}
            >
              <option value="AT_RISK">At risk only</option>
              <option value="ALL">All risk levels</option>
              <option value="HIGH">High</option>
              <option value="MEDIUM">Medium</option>
              <option value="LOW">Low</option>
              <option value="UNKNOWN">Unknown</option>
            </select>
          </label>
        </div>

        <div className="table-wrapper">
          <table className="risk-table">
            <thead>
              <tr>
                <th>Station ID</th>
                <th>Station Name</th>
                <th>Province</th>
                <th>Risk</th>
                <th>Forecast Time</th>
                <th>3h Rainfall</th>
                <th>24h Rainfall</th>
                <th>Weather Station</th>
              </tr>
            </thead>

            <tbody>
              {filteredStations.map((station, index) => {
                const risk = getRiskLevel(station);

                return (
                  <tr key={`${station.id}-${station.forecast_time_vn}-${index}`}>
                    <td>{station.id || "-"}</td>
                    <td>{station.name || "-"}</td>
                    <td>{station.province || "-"}</td>
                    <td>
                      <span className={`risk-badge risk-${risk.toLowerCase()}`}>
                        {risk}
                      </span>
                    </td>
                    <td>{formatForecastTime(station.forecast_time_vn)}</td>
                    <td>{formatRainfall(station.rain_3h_mm)} mm</td>
                    <td>{formatRainfall(station.precip_24h_mm)} mm</td>
                    <td>{station.weather_station_name || "-"}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {!isLoading && filteredStations.length === 0 && (
            <div className="empty-table-message">
              No stations match the current filters.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

function ForecastSummaryCard({ title, value }) {
  return (
    <div className="forecast-summary-card">
      <div>{title}</div>
      <strong>{value}</strong>
    </div>
  );
}