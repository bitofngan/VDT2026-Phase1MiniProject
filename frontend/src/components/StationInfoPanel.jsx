import {
  formatForecastTime,
  formatRiskReason,
} from "../utils/formatters";

export default function StationInfoPanel({ station, mode, onClose }) {
  if (!station) {
    return (
      <div className="station-panel-empty">
        <p>No station selected.</p>
      </div>
    );
  }

  return (
    <div className="station-panel">
      <div className="station-panel-header">
        <div>
          <h3>{station.name || station.station_name || station.telecom_station_name}</h3>
          <p>{station.id || station.station_id || station.telecom_station_id}</p>
        </div>

        <button className="station-panel-close" onClick={onClose}>
          ×
        </button>
      </div>

      <div className="station-panel-section">
        <InfoRow label="Province" value={station.province} />
        <InfoRow label="Elevation" value={`${station.elevation_m ?? "N/A"} m`} />
      </div>

      {mode === "current" ? (
        <div className="station-panel-section">
          <h4>Current Weather</h4>
          <InfoRow label="Temperature" value={`${station.current_temp_c ?? "N/A"} °C`} />
          <InfoRow label="Rain" value={`${station.current_precip_mm ?? "N/A"} mm`} />
          <InfoRow label="Wind" value={`${station.current_wind_mps ?? "N/A"} m/s`} />
          <InfoRow label="Humidity" value={`${station.current_humidity ?? "N/A"}%`} />
          <InfoRow label="Pressure" value={`${station.current_pressure_mb ?? "N/A"} mb`} />
          <InfoRow label="Condition" value={station.current_condition ?? "N/A"} />
          <InfoRow label="Observed at" value={station.current_weather_time ?? "N/A"} />
        </div>
      ) : (
        <div className="station-panel-section">
          <h4>Forecast Flood Risk</h4>
          <InfoRow
            label="Risk"
            value={station.flood_risk || station.risk_level || "N/A"}
          />
          <InfoRow
            label="Rain 3h"
            value={`${station.precip_3h_mm ?? station.rain_3h_mm ?? "N/A"} mm`}
          />
          <InfoRow
            label="Rain 24h"
            value={`${station.precip_24h_mm ?? "N/A"} mm`}
          />
          <InfoRow label="Forecast time" value={formatForecastTime(station.forecast_time_vn)} />
          <InfoRow label="Reason" value={formatRiskReason(station.risk_reason)} />
        </div>
      )}
    </div>
  );
}

function InfoRow({ label, value }) {
  return (
    <div className="station-info-row">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}