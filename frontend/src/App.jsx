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
  const [stations, setStations] = useState([]);
  const [message, setMessage] = useState("");
  const [deleteId, setDeleteId] = useState("");

  const [reportStationId, setReportStationId] = useState("");
  const [weatherReport, setWeatherReport] = useState(null);
  const [isReportLoading, setIsReportLoading] = useState(false);

  const [form, setForm] = useState({
    id: "",
    name: "",
    latitude: "",
    longitude: "",
    province: "",
    elevation_m: "",
    low_rain_threshold_24h_mm: 80,
    medium_rain_threshold_24h_mm: 150,
    high_rain_threshold_24h_mm: 200,
  });

  async function adminFetch(endpoint, options = {}) {
    const res = await fetch(`http://127.0.0.1:8000${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
        ...(options.headers || {}),
      },
    });

    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Admin action failed.");
    }

    return data;
  }

  async function loadStations() {
    try {
      const data = await adminFetch("/api/admin/telecom-stations");
      setStations(data);
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function callAdminEndpoint(endpoint) {
    try {
      const data = await adminFetch(endpoint, { method: "POST" });
      setMessage(data.message || "Admin action completed.");
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function addStation(e) {
    e.preventDefault();

    try {
      const payload = {
        ...form,
        latitude: Number(form.latitude),
        longitude: Number(form.longitude),
        elevation_m: form.elevation_m === "" ? null : Number(form.elevation_m),
        low_rain_threshold_24h_mm: Number(form.low_rain_threshold_24h_mm),
        medium_rain_threshold_24h_mm: Number(form.medium_rain_threshold_24h_mm),
        high_rain_threshold_24h_mm: Number(form.high_rain_threshold_24h_mm),
      };

      const data = await adminFetch("/api/admin/telecom-stations", {
        method: "POST",
        body: JSON.stringify(payload),
      });

      setMessage(data.message);

      setForm({
        id: "",
        name: "",
        latitude: "",
        longitude: "",
        province: "",
        elevation_m: "",
        low_rain_threshold_24h_mm: 80,
        medium_rain_threshold_24h_mm: 150,
        high_rain_threshold_24h_mm: 200,
      });

      loadStations();
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function deleteStation(e) {
    e.preventDefault();

    if (!deleteId.trim()) return;

    try {
      const data = await adminFetch(
        `/api/admin/telecom-stations/${encodeURIComponent(deleteId.trim())}`,
        { method: "DELETE" }
      );

      setMessage(data.message);
      setDeleteId("");
      loadStations();
    } catch (err) {
      setMessage(err.message);
    }
  }

  async function generateWeatherReport(e) {
    e.preventDefault();

    if (!reportStationId) return;

    setIsReportLoading(true);

    try {
      const data = await adminFetch(
        `/api/admin/station-weather-report/${encodeURIComponent(
          reportStationId
        )}`
      );

      setWeatherReport(data);
      setMessage(`Weather report generated for ${reportStationId}.`);
    } catch (err) {
      setMessage(err.message);
      setWeatherReport(null);
    } finally {
      setIsReportLoading(false);
    }
  }

  useEffect(() => {
    loadStations();
  }, []);

  return (
    <div className="admin-page">
      <header className="forecast-header">
        <div>
          <h1>Admin Tools</h1>
          <p>Manage backend update tasks, telecom stations, and station reports.</p>
        </div>

        <button className="refresh-button logout-button" onClick={onLogout}>
          Logout
        </button>
      </header>

      {message && <div className="admin-message">{message}</div>}

      <section className="admin-card">
        <h2>Update Tasks</h2>

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
        </div>
      </section>

      <section className="admin-card">
        <h2>Add Telecom Station</h2>

        <form className="admin-form" onSubmit={addStation}>
          <label className="filter-field">
            <span>Station ID</span>
            <input
              value={form.id}
              onChange={(e) => setForm({ ...form, id: e.target.value })}
              placeholder="TS-ADMIN-00001"
              required
            />
          </label>

          <label className="filter-field">
            <span>Name</span>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="Telecom Station TS-ADMIN-00001"
              required
            />
          </label>

          <label className="filter-field">
            <span>Latitude</span>
            <input
              type="number"
              step="any"
              value={form.latitude}
              onChange={(e) => setForm({ ...form, latitude: e.target.value })}
              required
            />
          </label>

          <label className="filter-field">
            <span>Longitude</span>
            <input
              type="number"
              step="any"
              value={form.longitude}
              onChange={(e) => setForm({ ...form, longitude: e.target.value })}
              required
            />
          </label>

          <label className="filter-field">
            <span>Province</span>
            <input
              value={form.province}
              onChange={(e) => setForm({ ...form, province: e.target.value })}
              placeholder="Hà Nội"
              required
            />
          </label>

          <label className="filter-field">
            <span>Elevation</span>
            <input
              type="number"
              step="any"
              value={form.elevation_m}
              onChange={(e) => setForm({ ...form, elevation_m: e.target.value })}
              placeholder="Optional"
            />
          </label>

          <label className="filter-field">
            <span>Low Threshold 24h</span>
            <input
              type="number"
              step="any"
              value={form.low_rain_threshold_24h_mm}
              onChange={(e) =>
                setForm({ ...form, low_rain_threshold_24h_mm: e.target.value })
              }
            />
          </label>

          <label className="filter-field">
            <span>Medium Threshold 24h</span>
            <input
              type="number"
              step="any"
              value={form.medium_rain_threshold_24h_mm}
              onChange={(e) =>
                setForm({
                  ...form,
                  medium_rain_threshold_24h_mm: e.target.value,
                })
              }
            />
          </label>

          <label className="filter-field">
            <span>High Threshold 24h</span>
            <input
              type="number"
              step="any"
              value={form.high_rain_threshold_24h_mm}
              onChange={(e) =>
                setForm({ ...form, high_rain_threshold_24h_mm: e.target.value })
              }
            />
          </label>

          <button className="refresh-button" type="submit">
            Add Station
          </button>
        </form>
      </section>

      <section className="admin-card">
        <h2>Remove Telecom Station</h2>

        <form className="admin-delete-form" onSubmit={deleteStation}>
          <label className="filter-field">
            <span>Station ID</span>
            <input
              value={deleteId}
              onChange={(e) => setDeleteId(e.target.value)}
              placeholder="TS-ADMIN-00001"
            />
          </label>

          <button className="refresh-button logout-button" type="submit">
            Delete Station
          </button>
        </form>
      </section>

      <section className="admin-card">
        <h2>Generate Station Weather Report</h2>

        <p className="muted-text">
          Generate past and forecasted weather for a selected telecom station.
        </p>

        <form className="admin-delete-form" onSubmit={generateWeatherReport}>
          <label className="filter-field">
            <span>Station</span>
            <select
              value={reportStationId}
              onChange={(e) => setReportStationId(e.target.value)}
              required
            >
              <option value="">Select station</option>
              {stations.map((station) => (
                <option key={station.id} value={station.id}>
                  {station.id} - {station.name}
                </option>
              ))}
            </select>
          </label>

          <button
            className="refresh-button"
            type="submit"
            disabled={isReportLoading}
          >
            {isReportLoading ? "Generating..." : "Generate Report"}
          </button>
        </form>

        {weatherReport && <StationWeatherReport report={weatherReport} />}
      </section>

      <section className="admin-card">
        <h2>Current Telecom Stations</h2>

        <p className="muted-text">{stations.length} stations in database.</p>

        <div className="table-wrapper">
          <table className="risk-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Province</th>
                <th>Latitude</th>
                <th>Longitude</th>
                <th>Elevation</th>
              </tr>
            </thead>

            <tbody>
              {stations.slice(0, 200).map((station) => (
                <tr key={station.id}>
                  <td>{station.id}</td>
                  <td>{station.name}</td>
                  <td>{station.province}</td>
                  <td>{station.latitude}</td>
                  <td>{station.longitude}</td>
                  <td>{station.elevation_m ?? "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {stations.length > 200 && (
          <p className="muted-text">Showing first 200 stations only.</p>
        )}
      </section>
    </div>
  );
}

function StationWeatherReport({ report }) {
  const pastChartRows = [...(report.past || [])]
    .reverse()
    .slice(-24)
    .map((row) => ({
      time: formatReportTime(row.fetched_at || row.last_updated),
      rain: Number(row.precip_mm ?? 0),
    }));

  const forecastChartRows = [...(report.forecast || [])]
    .slice(0, 56)
    .map((row) => ({
      time: formatReportTime(row.forecast_time_vn),
      rain3h: Number(row.precip_3h_mm ?? 0),
      rain24h: Number(row.precip_24h_mm ?? 0),
      temp: Number(row.temperature_c ?? 0),
      wind: Number(row.wind_speed_mps ?? 0),
      risk: row.flood_risk || "UNKNOWN",
    }));

  const maxPastRain = Math.max(...pastChartRows.map((row) => row.rain), 1);
  const maxForecastRain = Math.max(
    ...forecastChartRows.map((row) => row.rain3h),
    1
  );

  return (
    <div className="station-report">
      <h3>
        {report.station.id} - {report.station.name}
      </h3>

      <p className="muted-text">
        Province: {report.station.province || "-"} · Weather station:{" "}
        {report.weather_station?.weather_station_name || "-"}
      </p>

      <h4>Past Rainfall Graph</h4>

      {pastChartRows.length === 0 ? (
        <p className="muted-text">
          No past rainfall records found for this station yet.
        </p>
      ) : (
        <div className="rainfall-chart">
          {pastChartRows.map((row, index) => (
            <div className="rainfall-bar-wrap" key={`${row.time}-${index}`}>
              <div
                className="rainfall-bar"
                style={{
                  height: `${Math.max((row.rain / maxPastRain) * 160, 4)}px`,
                }}
                title={`${row.time}: ${row.rain.toFixed(2)} mm`}
              />
              <span>{row.time}</span>
            </div>
          ))}
        </div>
      )}

      <h4>Forecasted 3h Rainfall Graph</h4>

      {forecastChartRows.length === 0 ? (
        <p className="muted-text">No forecast rainfall records found.</p>
      ) : (
        <RainfallScaleChart rows={forecastChartRows} />
      )}

      <h4>Forecasted Temperature Graph</h4>

      {forecastChartRows.length === 0 ? (
        <p className="muted-text">No forecast temperature records found.</p>
      ) : (
        <ForecastLineChart
          rows={forecastChartRows}
          valueKey="temp"
          unit="°C"
          color="#ef4444"
        />
      )}

      <h4>Forecasted Wind Speed Graph</h4>

      {forecastChartRows.length === 0 ? (
        <p className="muted-text">No forecast wind records found.</p>
      ) : (
        <ForecastLineChart
          rows={forecastChartRows}
          valueKey="wind"
          unit="m/s"
          color="#2563eb"
        />
      )}

      <h4>Past Weather</h4>

      <div className="table-wrapper">
        <table className="risk-table">
          <thead>
            <tr>
              <th>Fetched At</th>
              <th>Rain</th>
              <th>Temp</th>
              <th>Wind</th>
              <th>Humidity</th>
              <th>Condition</th>
            </tr>
          </thead>

          <tbody>
            {(report.past || []).map((row, index) => (
              <tr key={index}>
                <td>{formatReportTime(row.fetched_at || row.last_updated)}</td>
                <td>{formatNumber(row.precip_mm)} mm</td>
                <td>{formatNumber(row.temp_c)} °C</td>
                <td>{formatNumber(row.wind_mps)} m/s</td>
                <td>{formatNumber(row.humidity)}%</td>
                <td>{row.condition_text || "-"}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {(!report.past || report.past.length === 0) && (
          <div className="empty-table-message">No past weather records.</div>
        )}
      </div>

      <h4>Forecasted Weather</h4>

      <div className="table-wrapper">
        <table className="risk-table">
          <thead>
            <tr>
              <th>Forecast Time</th>
              <th>3h Rainfall</th>
              <th>24h Rainfall</th>
              <th>Temp</th>
              <th>Wind</th>
              <th>Risk</th>
              <th>Reason</th>
            </tr>
          </thead>

          <tbody>
            {(report.forecast || []).map((row, index) => (
              <tr key={index}>
                <td>{formatReportTime(row.forecast_time_vn)}</td>
                <td>{formatNumber(row.precip_3h_mm)} mm</td>
                <td>{formatNumber(row.precip_24h_mm)} mm</td>
                <td>{formatNumber(row.temperature_c)} °C</td>
                <td>{formatNumber(row.wind_speed_mps)} m/s</td>
                <td>
                  <span
                    className={`risk-badge risk-${String(
                      row.flood_risk || "unknown"
                    ).toLowerCase()}`}
                  >
                    {row.flood_risk || "-"}
                  </span>
                </td>
                <td>{formatRiskReason(row.risk_reason)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {(!report.forecast || report.forecast.length === 0) && (
          <div className="empty-table-message">No forecast weather records.</div>
        )}
      </div>
    </div>
  );
}

function RainfallScaleChart({ rows }) {
  const maxRain = Math.max(...rows.map((row) => row.rain3h), 1);
  const chartMax = Math.ceil(Math.max(maxRain, 50) / 10) * 10;
  const scaleValues = [
    chartMax,
    chartMax * 0.75,
    chartMax * 0.5,
    chartMax * 0.25,
    0,
  ];

  const chartWidth = Math.max(rows.length * 96, 1100);

  return (
    <div className="rainfall-scale-chart">
      <div className="rainfall-scale-axis">
        {scaleValues.map((value) => (
          <span key={value}>{Math.round(value)} mm</span>
        ))}
      </div>

      <div className="rainfall-scale-scroll">
        <div
          className="rainfall-scale-plot"
          style={{ width: `${chartWidth}px` }}
        >
          <div className="rainfall-grid-lines">
            {scaleValues.map((value) => (
              <div key={value} className="rainfall-grid-line" />
            ))}
          </div>

          <div className="danger-zone danger-zone-high">High danger</div>
          <div className="danger-zone danger-zone-medium">Medium</div>

          <div className="rainfall-scale-bars">
            {rows.map((row, index) => (
              <div className="rainfall-bar-wrap" key={`${row.time}-${index}`}>
                <div
                  className={`rainfall-bar forecast-risk-${row.risk.toLowerCase()}`}
                  style={{
                    height: `${Math.max((row.rain3h / chartMax) * 180, 4)}px`,
                  }}
                  title={`${row.time}: ${row.rain3h.toFixed(
                    2
                  )} mm / 3h · Risk: ${row.risk}`}
                />
                <span>{row.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function ForecastLineChart({ rows, valueKey, unit, color }) {
  const values = rows.map((row) => Number(row[valueKey] ?? 0));
  const minValue = Math.min(...values);
  const maxValue = Math.max(...values);
  const range = maxValue - minValue || 1;

  const scaleValues = [
    maxValue,
    minValue + range * 0.75,
    minValue + range * 0.5,
    minValue + range * 0.25,
    minValue,
  ];

  const chartWidth = Math.max(rows.length * 110, 1600);

  return (
    <div className="forecast-line-wrapper">
      <div className="forecast-axis">
        {scaleValues.map((value, index) => (
          <span key={index}>
            {value.toFixed(1)} {unit}
          </span>
        ))}
      </div>

      <div className="forecast-line-chart">
        <div className="forecast-line-inner" style={{ width: `${chartWidth}px` }}>
          <svg viewBox="0 0 1000 240">
            {[0, 1, 2, 3, 4].map((i) => (
              <line
                key={i}
                x1="0"
                y1={20 + i * 50}
                x2="1000"
                y2={20 + i * 50}
                stroke="#d1d5db"
                strokeDasharray="5 5"
              />
            ))}

            <polyline
              fill="none"
              stroke={color}
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
              points={buildSvgLinePoints(values, 1000, 220, 20)}
            />

            {buildSvgPoints(values, 1000, 220, 20).map((point, index) => (
              <circle
                key={index}
                cx={point.x}
                cy={point.y}
                r="3"
                fill={color}
                stroke="white"
                strokeWidth="1"
              />
            ))}
          </svg>

          <div className="forecast-line-labels">
            {rows.map((row, index) => (
              <span
                key={`${row.time}-${index}`}
                style={{
                  visibility: index % 4 === 0 ? "visible" : "hidden",
                }}
              >
                {row.time}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function buildSvgLinePoints(values, width, height, padding) {
  if (!values || values.length === 0) return "";

  const numericValues = values.map((value) => {
    const numberValue = Number(value);
    return Number.isNaN(numberValue) ? 0 : numberValue;
  });

  const minValue = Math.min(...numericValues);
  const maxValue = Math.max(...numericValues);
  const range = maxValue - minValue || 1;

  return numericValues
    .map((value, index) => {
      const x =
        numericValues.length === 1
          ? width / 2
          : padding +
            (index / (numericValues.length - 1)) * (width - padding * 2);

      const y =
        height -
        padding -
        ((value - minValue) / range) * (height - padding * 2);

      return `${x},${y}`;
    })
    .join(" ");
}

function formatNumber(value) {
  if (value === null || value === undefined || value === "") return "-";

  const numberValue = Number(value);

  if (Number.isNaN(numberValue)) return "-";

  return numberValue.toFixed(2);
}

function formatReportTime(value) {
  if (!value) return "-";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString("en-GB", {
    timeZone: "Asia/Ho_Chi_Minh",
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatRiskReason(value) {
  if (!value) return "-";

  return String(value)
    .replaceAll("_", " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

function buildSvgPoints(values, width, height, padding) {
  if (!values.length) return [];

  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;

  return values.map((value, index) => {
    const x =
      padding +
      (index / Math.max(values.length - 1, 1)) *
        (width - padding * 2);

    const y =
      height -
      padding -
      ((value - min) / range) *
        (height - padding * 2);

    return { x, y };
  });
}