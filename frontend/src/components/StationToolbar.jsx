function buildForecastOptions(forecastTimes) {
  const options = [
    {
      value: "WORST",
      label: "Worst risk in next 7 days",
    },
  ];

  forecastTimes.forEach((time, index) => {
    const hoursAhead = (index + 1) * 3;

    let label = `Next ${hoursAhead} hours`;

    if (hoursAhead === 24) label = "Next 24 hours";

    if (hoursAhead > 24 && hoursAhead % 24 === 0) {
      label = `Day ${hoursAhead / 24}`;
    }

    if (hoursAhead > 24 && hoursAhead % 24 !== 0) {
      label = `Day ${Math.floor(hoursAhead / 24)} + ${hoursAhead % 24}h`;
    }

    options.push({
      value: time,
      label,
    });
  });

  return options;
}

export default function StationToolbar({
  mode,
  province,
  provinces,
  forecastTimes,
  selectedForecastTime,
  riskFilter,
  stationCount,
  lastUpdated,
  onModeChange,
  onProvinceChange,
  onRiskFilterChange,
  onForecastTimeChange,
}) {
  const forecastOptions = buildForecastOptions(forecastTimes);

  return (
    <div className="station-toolbar">
      <div className="toolbar-top">
        <div>
          <h2>Vietnam Station Map</h2>
          <p>
            {stationCount} stations shown
            {lastUpdated ? ` · Updated ${lastUpdated.toLocaleTimeString()}` : ""}
          </p>
        </div>

        <div className="map-tabs">
          <button
            className={mode === "forecast" ? "map-tab active" : "map-tab"}
            onClick={() => onModeChange("forecast")}
          >
            Forecast Risk
          </button>

          <button
            className={mode === "current" ? "map-tab active" : "map-tab"}
            onClick={() => onModeChange("current")}
          >
            Current Weather
          </button>
        </div>
      </div>

      <div
        className={
          mode === "forecast"
            ? "toolbar-filters three-columns"
            : "toolbar-filters two-columns"
        }
      >
        <label className="filter-field">
          <span>Province</span>
          <select value={province} onChange={(e) => onProvinceChange(e.target.value)}>
            <option value="ALL">All provinces</option>
            {provinces.map((provinceName) => (
              <option key={provinceName} value={provinceName}>
                {provinceName}
              </option>
            ))}
          </select>
        </label>

        <label className="filter-field">
          <span>Risk level</span>
          <select
            value={riskFilter}
            onChange={(e) => onRiskFilterChange(e.target.value)}
          >
            <option value="ALL">All risk levels</option>
            <option value="AT_RISK">At risk only</option>
            <option value="UNKNOWN">Unknown</option>
            <option value="SAFE">Safe</option>
            <option value="LOW">Low</option>
            <option value="MEDIUM">Medium</option>
            <option value="HIGH">High</option>
          </select>
        </label>

        {mode === "forecast" && (
          <label className="filter-field">
            <span>Forecast time</span>
            <select
              value={selectedForecastTime}
              onChange={(e) => onForecastTimeChange(e.target.value)}
            >
              {forecastOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>
    </div>
  );
}