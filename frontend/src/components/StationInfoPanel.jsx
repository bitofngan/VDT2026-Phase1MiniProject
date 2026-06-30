export default function StationInfoPanel({ station, mode, onClose }) {
  if (!station) return null;

  return (
    <div
      style={{
        position: "absolute",
        top: 12,
        right: 12,
        zIndex: 10,
        width: 290,
        background: "white",
        padding: 14,
        borderRadius: 10,
        boxShadow: "0 2px 10px rgba(0,0,0,0.25)",
      }}
    >
      <button onClick={onClose} style={{ float: "right" }}>
        ×
      </button>

      <h3>{station.name}</h3>

      <p><b>ID:</b> {station.id}</p>
      <p><b>Province:</b> {station.province}</p>
      <p><b>Elevation:</b> {station.elevation_m ?? "N/A"} m</p>

      {mode === "current" ? (
        <>
          <hr />
          <p><b>Current weather</b></p>
          <p><b>Temperature:</b> {station.current_temp_c ?? "N/A"} °C</p>
          <p><b>Rain:</b> {station.current_precip_mm ?? "N/A"} mm</p>
          <p><b>Wind:</b> {station.current_wind_mps ?? "N/A"} m/s</p>
          <p><b>Humidity:</b> {station.current_humidity ?? "N/A"}%</p>
          <p><b>Pressure:</b> {station.current_pressure_mb ?? "N/A"} mb</p>
          <p><b>Condition:</b> {station.current_condition ?? "N/A"}</p>
          <p><b>Observed at:</b> {station.current_weather_time ?? "N/A"}</p>
        </>
      ) : (
        <>
          <hr />
          <p><b>Forecast flood risk</b></p>
          <p><b>Risk:</b> {station.flood_risk ?? "N/A"}</p>
          <p><b>Rain 3h:</b> {station.precip_3h_mm ?? "N/A"} mm</p>
          <p><b>Rain 24h:</b> {station.precip_24h_mm ?? "N/A"} mm</p>
          <p><b>Forecast time:</b> {station.forecast_time_vn ?? "N/A"}</p>
          <p><b>Reason:</b> {station.risk_reason ?? "N/A"}</p>
        </>
      )}
    </div>
  );
}