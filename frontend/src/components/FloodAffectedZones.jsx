import { useEffect, useRef } from "react";
import { useMap } from "@vis.gl/react-google-maps";
import * as turf from "@turf/turf";

const BUFFER_KM = 20;

function getZoneStyle(risk) {
  if (risk === "HIGH") {
    return {
      strokeColor: "#d32f2f",
      fillColor: "#d32f2f",
      fillOpacity: 0.22,
    };
  }

  if (risk === "MEDIUM") {
    return {
      strokeColor: "#fdd835",
      fillColor: "#fdd835",
      fillOpacity: 0.2,
    };
  }

  return null;
}

function createBufferedHull(stations) {
  const points = stations
    .filter((station) => station.latitude && station.longitude)
    .map((station) =>
      turf.point([Number(station.longitude), Number(station.latitude)])
    );

  if (points.length === 0) return null;

  if (points.length === 1) {
    return turf.buffer(points[0], BUFFER_KM, { units: "kilometers" });
  }

  const collection = turf.featureCollection(points);
  const hull = turf.convex(collection);

  if (!hull) {
    return turf.buffer(collection, BUFFER_KM, { units: "kilometers" });
  }

  return turf.buffer(hull, BUFFER_KM, { units: "kilometers" });
}

function geoJsonPolygonToGooglePaths(feature) {
  const geometry = feature.geometry;

  if (!geometry) return [];

  if (geometry.type === "Polygon") {
    return geometry.coordinates.map((ring) =>
      ring.map(([lng, lat]) => ({ lat, lng }))
    );
  }

  if (geometry.type === "MultiPolygon") {
    return geometry.coordinates.flatMap((polygon) =>
      polygon.map((ring) => ring.map(([lng, lat]) => ({ lat, lng })))
    );
  }

  return [];
}

export default function FloodAffectedZones({ stations }) {
  const map = useMap();
  const polygonsRef = useRef([]);

  useEffect(() => {
    if (!map) return;

    polygonsRef.current.forEach((polygon) => polygon.setMap(null));
    polygonsRef.current = [];

    const highStations = stations.filter(
      (station) => station.flood_risk === "HIGH"
    );
    const mediumStations = stations.filter(
      (station) => station.flood_risk === "MEDIUM"
    );

    const zones = [
      { risk: "MEDIUM", feature: createBufferedHull(mediumStations) },
      { risk: "HIGH", feature: createBufferedHull(highStations) },
    ];

    zones.forEach(({ risk, feature }) => {
      if (!feature) return;

      const style = getZoneStyle(risk);
      const paths = geoJsonPolygonToGooglePaths(feature);

      paths.forEach((path) => {
        const polygon = new google.maps.Polygon({
          map,
          paths: path,
          strokeColor: style.strokeColor,
          strokeOpacity: 0.85,
          strokeWeight: 2,
          fillColor: style.fillColor,
          fillOpacity: style.fillOpacity,
          clickable: false,
        });

        polygonsRef.current.push(polygon);
      });
    });

    return () => {
      polygonsRef.current.forEach((polygon) => polygon.setMap(null));
      polygonsRef.current = [];
    };
  }, [map, stations]);

  return null;
}