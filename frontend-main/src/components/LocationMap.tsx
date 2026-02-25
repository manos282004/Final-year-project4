import { useEffect, useRef, useState } from "react";
import { apiService } from "../services/api";

/* ===============================
   Types
================================ */
type LocationType = {
  id: number;
  name: string;
  latitude: number;
  longitude: number;
  insights: string;
  nearbyBusinessCount: number; // IMPORTANT
  commercialWeight: number;    // 1–10
};

interface LocationMapProps {
  businessType: string;
  selectedLocation?: {
    lat: number;
    lng: number;
  };
}

/* ===============================
   Constants
================================ */
const DEFAULT_CENTER = { lat: 13.0213, lng: 80.2231 }; // Saidapet

/* ===============================
   Density Logic (INLINE)
================================ */
function calculateDensityScore(loc: LocationType) {
  return loc.nearbyBusinessCount * 1.2 + loc.commercialWeight * 5;
}

/* ===============================
   Component
================================ */
export default function LocationMap({
  businessType,
  selectedLocation,
}: LocationMapProps) {
  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<google.maps.Map | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);
  const infoWindowRef = useRef<google.maps.InfoWindow | null>(null);

  const [locations, setLocations] = useState<LocationType[]>([]);

  /* ===============================
     Fetch & rank locations
  ================================ */
  useEffect(() => {
    apiService.getLocations(businessType).then((data) => {
      const ranked = data
        .map((loc: LocationType) => ({
          ...loc,
          densityScore: calculateDensityScore(loc),
        }))
        .sort((a: any, b: any) => b.densityScore - a.densityScore)
        .slice(0, 3); // TOP 3 ONLY

      setLocations(ranked);
    });
  }, [businessType]);

  /* ===============================
     Initialize Map (ONCE)
  ================================ */
  useEffect(() => {
    if (!mapDivRef.current || mapRef.current) return;

    mapRef.current = new window.google.maps.Map(mapDivRef.current, {
      center: DEFAULT_CENTER,
      zoom: 14,
    });

    infoWindowRef.current = new window.google.maps.InfoWindow();
  }, []);

  /* ===============================
     Render Accurate Markers
  ================================ */
  useEffect(() => {
    if (!mapRef.current) return;

    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];

    locations.forEach((loc: any) => {
      const marker = new window.google.maps.Marker({
        position: { lat: loc.latitude, lng: loc.longitude },
        map: mapRef.current!,
        title: loc.name,
      });

      marker.addListener("click", () => {
        infoWindowRef.current?.setContent(`
          <div style="max-width:220px">
            <strong>${loc.name}</strong><br/>
            <small>${loc.insights}</small><br/>
            <b>Density Score:</b> ${loc.densityScore.toFixed(1)}
          </div>
        `);
        infoWindowRef.current?.open(mapRef.current!, marker);
      });

      markersRef.current.push(marker);
    });
  }, [locations]);

  /* ===============================
     Chatbot / List Fly-To
  ================================ */
  useEffect(() => {
    if (!mapRef.current || !selectedLocation) return;

    mapRef.current.panTo(selectedLocation);
    mapRef.current.setZoom(16);
  }, [selectedLocation]);

  return (
    <div
      ref={mapDivRef}
      style={{
        height: "400px",
        width: "100%",
        borderRadius: "12px",
      }}
    />
  );
}
