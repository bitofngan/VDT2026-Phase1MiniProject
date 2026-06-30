export default function StationToolbar({
  mode,
  province,
  provinces,
  forecastTimes,
  selectedForecastTime,
  stationCount,
  isRefreshing,
  refreshDisabled,
  lastUpdated,
  onModeChange,
  onProvinceChange,
  onForecastTimeChange,
  onRefresh,
}) {
  return (
    <div
      style={{
        position: "absolute",
        top: 12,
        left: 12,
        zIndex: 10,
        background: "white",
        padding: 10,
        borderRadius: 8,
        boxShadow: "0 2px 8px rgba(0,0,0,0.2)",
        width: 210,
      }}
    >
      <select
        value={mode}
        onChange={(e) => onModeChange(e.target.value)}
        style={{ width: "100%" }}
      >
        <option value="current">Current weather</option>
        <option value="forecast">Forecast flood risk</option>
      </select>

      <select
        value={province}
        onChange={(e) => onProvinceChange(e.target.value)}
        style={{ width: "100%", marginTop: 8 }}
      >
        <option value="ALL">All provinces</option>
        {provinces.map((provinceName) => (
          <option key={provinceName} value={provinceName}>
            {provinceName}
          </option>
        ))}
      </select>

      {mode === "forecast" && (
        <select
          value={selectedForecastTime}
          onChange={(e) => onForecastTimeChange(e.target.value)}
          style={{ width: "100%", marginTop: 8 }}
        >
          <option value="WORST">Worst risk in forecast</option>
          {forecastTimes.map((time) => (
            <option key={time} value={time}>
              {time}
            </option>
          ))}
        </select>
      )}

      <div style={{ fontSize: 12, marginTop: 6 }}>
        {stationCount} stations
      </div>

      <button
        onClick={onRefresh}
        disabled={refreshDisabled}
        style={{
          marginTop: 8,
          width: "100%",
          padding: "6px",
          cursor: refreshDisabled ? "not-allowed" : "pointer",
        }}
      >
        {isRefreshing ? "Refreshing..." : "Refresh data"}
      </button>

      <div style={{ fontSize: 11, marginTop: 6 }}>
        Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : "Never"}
      </div>
    </div>
  );
}