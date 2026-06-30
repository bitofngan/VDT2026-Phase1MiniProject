import { Map, AdvancedMarker, Pin } from "@vis.gl/react-google-maps";
import { sampleStations } from "../data/sampleStations";

function getRiskColor(risk) {
  if (risk === "HIGH") return "#d32f2f";
  if (risk === "MEDIUM") return "#f9a825";
  return "#2e7d32";
}

export default function StationMap() {
  return (
    <Map
      defaultCenter={{ lat: 16.0544, lng: 108.2022 }}
      defaultZoom={6}
      mapId="telecom-flood-risk-map"
      style={{ width: "100%", height: "100vh" }}
    >
      {sampleStations.map((station) => (
        <AdvancedMarker
          key={station.id}
          position={{ lat: station.latitude, lng: station.longitude }}
          title={station.name}
        >
          <Pin background={getRiskColor(station.floodRisk)} />
        </AdvancedMarker>
      ))}
    </Map>
  );
}