import { useEffect, useRef } from "react";
import { useMap } from "@vis.gl/react-google-maps";

export default function AutoFitProvince({ stations, province }) {
  const map = useMap();
  const lastFittedProvinceRef = useRef(null);

  useEffect(() => {
    if (!map) return;
    if (province === "ALL") return;
    if (!stations || stations.length === 0) return;

    // Only auto-fit when the selected province actually changes.
    // Do not auto-fit again just because stations refreshed.
    if (lastFittedProvinceRef.current === province) return;
    lastFittedProvinceRef.current = province;

    const bounds = new google.maps.LatLngBounds();

    stations.forEach((station) => {
      bounds.extend({
        lat: Number(station.latitude),
        lng: Number(station.longitude),
      });
    });

    map.fitBounds(bounds, {
      top: 90,
      right: 90,
      bottom: 90,
      left: 90,
    });
  }, [map, province, stations]);

  return null;
}