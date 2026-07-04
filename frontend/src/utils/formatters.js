export function formatForecastTime(timeString) {
  if (!timeString) return "N/A";

  const date = new Date(timeString);

  return new Intl.DateTimeFormat("en-GB", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Ho_Chi_Minh",
  }).format(date);
}

export function formatRiskReason(reason) {
  const reasons = {
    rainfall_below_thresholds:
      "Rainfall remains below all flood warning thresholds.",

    rolling_24h_precip_exceeds_low_threshold:
      "24-hour accumulated rainfall exceeds the Low flood threshold.",

    rolling_24h_precip_exceeds_medium_threshold:
      "24-hour accumulated rainfall exceeds the Medium flood threshold.",

    rolling_24h_precip_exceeds_high_threshold:
      "24-hour accumulated rainfall exceeds the High flood threshold.",

    avg_1h_precip_exceeds_estimated_1h_high_threshold:
      "Heavy short-duration rainfall indicates a High flood risk.",

    no_weather_forecast_rows:
      "No forecast data is available for the nearest weather station.",

    no_nearest_weather_station:
      "No nearby weather station could be matched.",

    nearest_weather_station_outside_max_radius:
      "Nearest weather station is outside the supported radius.",
  };

  return reasons[reason] || reason || "N/A";
}

export function formatVietnamTime(value) {
  if (!value) return "-";

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;

  return new Intl.DateTimeFormat("en-GB", {
    timeZone: "Asia/Ho_Chi_Minh",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  }).format(date);
}