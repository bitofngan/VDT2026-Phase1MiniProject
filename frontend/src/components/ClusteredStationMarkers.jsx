import { useEffect, useRef } from "react";
import { useMap } from "@vis.gl/react-google-maps";
import {
  MarkerClusterer,
  SuperClusterAlgorithm,
} from "@googlemaps/markerclusterer";

function getMarkerColor(station, mode) {
  if (mode === "current") {
    const rain = Number(station.current_precip_mm ?? 0);

    if (rain >= 20) return "#d32f2f";
    if (rain >= 5) return "#fdd835";
    return "#2e7d32";
  }

  if (station.flood_risk === "HIGH") return "#d32f2f";
  if (station.flood_risk === "MEDIUM") return "#fdd835";
  return "#2e7d32";
}

export default function ClusteredStationMarkers({
  stations,
  onStationClick,
  mode,
}) {
  const map = useMap();
  const clustererRef = useRef(null);
  const markersRef = useRef([]);

  useEffect(() => {
    if (!map) return;

    clustererRef.current?.clearMarkers();

    markersRef.current.forEach((marker) => {
      google.maps.event.clearInstanceListeners(marker);
      marker.setMap(null);
    });

    markersRef.current = [];

    const markers = stations
      .filter((station) => station.latitude && station.longitude)
      .map((station) => {
        const marker = new google.maps.Marker({
          position: {
            lat: Number(station.latitude),
            lng: Number(station.longitude),
          },
          optimized: true,
          clickable: true,
          icon: {
            path: google.maps.SymbolPath.CIRCLE,
            scale: 4,
            fillColor: getMarkerColor(station, mode),
            fillOpacity: 0.9,
            strokeWeight: 0,
          },
        });

        marker.addListener("click", () => {
          onStationClick(station);
        });

        return marker;
      });

    markersRef.current = markers;

    clustererRef.current = new MarkerClusterer({
      map,
      markers,
      algorithm: new SuperClusterAlgorithm({
        radius: 120,
        maxZoom: 14,
      }),
      renderer: {
        render({ count, position }) {
          return new google.maps.Marker({
            position,
            optimized: true,
            label: {
              text: String(count),
              color: "white",
              fontSize: "12px",
              fontWeight: "bold",
            },
            icon: {
              path: google.maps.SymbolPath.CIRCLE,
              scale: 18,
              fillColor: "#1976d2",
              fillOpacity: 0.9,
              strokeColor: "white",
              strokeWeight: 2,
            },
          });
        },
      },
    });

    return () => {
      clustererRef.current?.clearMarkers();

      markersRef.current.forEach((marker) => {
        google.maps.event.clearInstanceListeners(marker);
        marker.setMap(null);
      });

      markersRef.current = [];
    };
  }, [map, stations, onStationClick, mode]);

  return null;
}