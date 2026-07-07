import { useEffect, useRef, useState } from "react";
import { useMap } from "@vis.gl/react-google-maps";
import {
  MarkerClusterer,
  SuperClusterAlgorithm,
} from "@googlemaps/markerclusterer";

const VIEWPORT_PADDING_RATIO = 0.25;

function getRiskLevel(station) {
  return String(
    station.risk_level || station.flood_risk || station.risk || "UNKNOWN"
  ).toUpperCase();
}

function getMarkerColor(station, mode) {
  const risk = getRiskLevel(station);

  if (risk === "HIGH") return "#ef4444";
  if (risk === "MEDIUM") return "#f59e0b";
  if (risk === "LOW") return "#84cc16";
  if (risk === "SAFE") return "#16a34a";

  if (mode === "current") {
    const rain = Number(station.current_precip_mm ?? 0);
    if (rain >= 20) return "#ef4444";
    if (rain >= 5) return "#f59e0b";
    return "#16a34a";
  }

  return "#64748b";
}

function getStationId(station, index) {
  return (
    station.id ||
    station.station_id ||
    station.telecom_station_id ||
    `${station.latitude}-${station.longitude}-${index}`
  );
}

function expandBounds(bounds) {
  const ne = bounds.getNorthEast();
  const sw = bounds.getSouthWest();

  const latPadding = (ne.lat() - sw.lat()) * VIEWPORT_PADDING_RATIO;
  const lngPadding = (ne.lng() - sw.lng()) * VIEWPORT_PADDING_RATIO;

  return new google.maps.LatLngBounds(
    {
      lat: sw.lat() - latPadding,
      lng: sw.lng() - lngPadding,
    },
    {
      lat: ne.lat() + latPadding,
      lng: ne.lng() + lngPadding,
    }
  );
}

export default function ClusteredStationMarkers({
  stations,
  onStationClick,
  mode,
}) {
  const map = useMap();

  const clustererRef = useRef(null);
  const markersRef = useRef([]);
  const idleListenerRef = useRef(null);

  const [visibleStations, setVisibleStations] = useState([]);

  useEffect(() => {
    if (!map) return;

    function updateVisibleStations() {
      const bounds = map.getBounds();
      if (!bounds) return;

      const expandedBounds = expandBounds(bounds);

      const nextVisibleStations = stations.filter((station) => {
        if (!station.latitude || !station.longitude) return false;

        return expandedBounds.contains({
          lat: Number(station.latitude),
          lng: Number(station.longitude),
        });
      });

      setVisibleStations(nextVisibleStations);
    }

    updateVisibleStations();

    idleListenerRef.current?.remove();
    idleListenerRef.current = map.addListener("idle", updateVisibleStations);

    return () => {
      idleListenerRef.current?.remove();
      idleListenerRef.current = null;
    };
  }, [map, stations]);

  useEffect(() => {
    if (!map) return;

    if (!clustererRef.current) {
      clustererRef.current = new MarkerClusterer({
        map,
        markers: [],
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
                fillColor: "#118ab2",
                fillOpacity: 0.92,
                strokeColor: "white",
                strokeWeight: 2,
              },
            });
          },
        },
      });
    }

    clustererRef.current.clearMarkers();

    markersRef.current.forEach((marker) => {
      google.maps.event.clearInstanceListeners(marker);
      marker.setMap(null);
    });

    markersRef.current = visibleStations.map((station, index) => {
      const marker = new google.maps.Marker({
        position: {
          lat: Number(station.latitude),
          lng: Number(station.longitude),
        },
        optimized: true,
        clickable: true,
        title: station.name || station.station_name || getStationId(station, index),
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 4,
          fillColor: getMarkerColor(station, mode),
          fillOpacity: 0.9,
          strokeColor: "white",
          strokeWeight: 1,
        },
      });

      marker.addListener("click", () => {
        onStationClick(station);
      });

      return marker;
    });

    clustererRef.current.addMarkers(markersRef.current);

    return () => {
      clustererRef.current?.clearMarkers();

      markersRef.current.forEach((marker) => {
        google.maps.event.clearInstanceListeners(marker);
        marker.setMap(null);
      });

      markersRef.current = [];
    };
  }, [map, visibleStations, onStationClick, mode]);

  useEffect(() => {
    return () => {
      idleListenerRef.current?.remove();
      clustererRef.current?.clearMarkers();

      markersRef.current.forEach((marker) => {
        google.maps.event.clearInstanceListeners(marker);
        marker.setMap(null);
      });

      markersRef.current = [];
      clustererRef.current = null;
    };
  }, []);

  return null;
}