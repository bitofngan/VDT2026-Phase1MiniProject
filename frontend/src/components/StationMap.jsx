import { useEffect, useState } from "react";
import { Map, AdvancedMarker, Pin } from "@vis.gl/react-google-maps";

function getRiskColor(risk) {
  if (risk === "HIGH") return "#d32f2f";
  if (risk === "MEDIUM") return "#f9a825";
  return "#2e7d32";
}

export default function StationMap() {
  const [stations, setStations] = useState([]);

  useEffect(() => {
    fetch("http://127.0.0.1:8000/api/stations")
      .then((res) => res.json())
      .then((data) => setStations(data))
      .catch((err) => console.error("Failed to load stations:", err));
  }, []);

  return (
    <Map
      defaultCenter={{ lat: 16.0544, lng: 108.2022 }}
      defaultZoom={6}
      mapId="telecom-flood-risk-map"
      style={{ width: "100%", height: "100vh" }}
    >
      {stations.map((station) => (
        <AdvancedMarker
          key={station.id}
          position={{
            lat: Number(station.latitude),
            lng: Number(station.longitude),
          }}
          title={station.name}
        >
          <Pin background={getRiskColor(station.flood_risk)} />
        </AdvancedMarker>
      ))}
    </Map>
  );
}