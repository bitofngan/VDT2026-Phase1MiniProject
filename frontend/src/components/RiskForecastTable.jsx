import { useMemo, useState } from "react";

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

function getStationId(station) {
  return station.id || station.station_id || station.telecom_station_id || "-";
}

function getStationName(station) {
  return station.name || station.station_name || station.telecom_station_name || "-";
}

function getForecastTime(station) {
  return station.forecast_time_vn || station.forecast_time || "-";
}

function getRainfall(station) {
  const value =
    station.rain_3h_mm ??
    station.rainfall_mm ??
    station.precipitation_mm ??
    station.precipitation_3h_mm ??
    station.past3hprecip_mm ??
    station.rain_mm;

  if (value === undefined || value === null || value === "") return "-";

  const numberValue = Number(value);
  if (Number.isNaN(numberValue)) return "-";

  return numberValue.toFixed(2);
}

function getWeatherStationName(station) {
  return (
    station.weather_station_name ||
    station.nearest_weather_station_name ||
    station.weather_name ||
    station.matched_weather_station_name ||
    "-"
  );
}

export default function RiskForecastTable({
  stations = [],
  lastUpdated,
  isRefreshing,
  onRefresh,
}) {
  const [provinceFilter, setProvinceFilter] = useState("ALL");
  const [riskFilter, setRiskFilter] = useState("AT_RISK");
  const [searchText, setSearchText] = useState("");

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
          String(getStationId(station)).toLowerCase().includes(keyword) ||
          String(getStationName(station)).toLowerCase().includes(keyword) ||
          String(station.province || "").toLowerCase().includes(keyword) ||
          String(getWeatherStationName(station)).toLowerCase().includes(keyword)
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
          onClick={onRefresh}
          disabled={isRefreshing}
        >
          {isRefreshing ? "Refreshing..." : "Refresh"}
        </button>
      </header>

      <section className="forecast-summary-grid">
        <ForecastSummaryCard title="Total Forecast Rows" value={summary.total} />
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
              <option value="SAFE">Safe</option>
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
                <th>Weather Station</th>
              </tr>
            </thead>

            <tbody>
              {filteredStations.map((station, index) => {
                const risk = getRiskLevel(station);

                return (
                  <tr key={`${getStationId(station)}-${getForecastTime(station)}-${index}`}>
                    <td>{getStationId(station)}</td>
                    <td>{getStationName(station)}</td>
                    <td>{station.province || "-"}</td>
                    <td>
                      <span className={`risk-badge risk-${risk.toLowerCase()}`}>
                        {risk}
                      </span>
                    </td>
                    <td>{getForecastTime(station)}</td>
                    <td>{getRainfall(station)} mm</td>
                    <td>{getWeatherStationName(station)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>

          {!isRefreshing && filteredStations.length === 0 && (
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