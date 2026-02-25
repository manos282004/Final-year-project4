import { useState, useEffect, useRef } from "react";
import { MapPin, AlertCircle, TrendingUp, Map } from "lucide-react";
import BusinessTypeSelector from "../components/BusinessTypeSelector";
import Chatbot from "./Chatbot";
import { apiService } from "../services/api";

/* ===============================
   Types
================================ */
type LocationData = {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  insights: string;
  distanceKm?: number;
  score?: number;
  mapUrl?: string;
};

export default function Location() {
  const [selectedBusinessType, setSelectedBusinessType] =
    useState<string>("showroom");
  const [area] = useState<string>("Saidapet, Chennai");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [locations, setLocations] = useState<LocationData[]>([]);
  const [selectedLocation, setSelectedLocation] =
    useState<LocationData | null>(null);

  const mapRef = useRef<google.maps.Map | null>(null);
  const mapDivRef = useRef<HTMLDivElement | null>(null);
  const markersRef = useRef<google.maps.Marker[]>([]);

  /* ===============================
     Load locations
  ================================ */
  useEffect(() => {
    loadLocations();
  }, [selectedBusinessType]);

  const loadLocations = async () => {
    setLoading(true);
    setError(null);

    try {
      const data = await apiService.getLocations(selectedBusinessType, area);
      setLocations(data);
      setSelectedLocation(data[0] || null);
    } catch (err) {
      setError("Unable to load location data. Please ensure backend is running.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  /* ===============================
     Chatbot -> Map connection
  ================================ */
  const handleChatbotLocationSelect = (location: LocationData) => {
    const match = locations.find((loc) => loc.id === location.id);
    if (match) setSelectedLocation(match);
  };

  const handleChatbotLocationsUpdate = (newLocations: LocationData[]) => {
    if (!newLocations || newLocations.length === 0) return;
    setLocations(newLocations);
    setSelectedLocation(newLocations[0] || null);
  };

  /* ===============================
     Initialize Google Map (once)
  ================================ */
  useEffect(() => {
    if (!mapDivRef.current || mapRef.current || locations.length === 0) return;

    mapRef.current = new window.google.maps.Map(mapDivRef.current, {
      center: {
        lat: locations[0].latitude,
        lng: locations[0].longitude,
      },
      zoom: 14,
    });
  }, [locations]);

  /* ===============================
     Render markers
  ================================ */
  useEffect(() => {
    if (!mapRef.current) return;

    markersRef.current.forEach((m) => m.setMap(null));
    markersRef.current = [];

    locations.forEach((location) => {
      const marker = new window.google.maps.Marker({
        position: {
          lat: location.latitude,
          lng: location.longitude,
        },
        map: mapRef.current!,
        title: location.name,
      });

      marker.addListener("click", () => {
        setSelectedLocation(location);
      });

      markersRef.current.push(marker);
    });
  }, [locations]);

  /* ===============================
     Fly to selected location
  ================================ */
  useEffect(() => {
    if (!mapRef.current || !selectedLocation) return;

    mapRef.current.panTo({
      lat: selectedLocation.latitude,
      lng: selectedLocation.longitude,
    });
    mapRef.current.setZoom(16);
  }, [selectedLocation]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center space-x-3 mb-6">
          <MapPin className="w-8 h-8 text-green-600" />
          <h2 className="text-2xl font-bold text-gray-800">
            Accurate Location Insights - Saidapet
          </h2>
        </div>

        <BusinessTypeSelector
          selectedType={selectedBusinessType}
          onSelectType={setSelectedBusinessType}
        />
      </div>

      {/* Chatbot */}
      <Chatbot
        businessType={selectedBusinessType}
        onLocationSelect={handleChatbotLocationSelect}
        onLocationsUpdate={handleChatbotLocationsUpdate}
      />

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start space-x-3">
          <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
          <div>
            <p className="text-red-800 font-medium">Connection Error</p>
            <p className="text-red-600 text-sm">{error}</p>
          </div>
        </div>
      )}

      {/* Loading */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Map */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-xl shadow-lg overflow-hidden">
              <div className="h-[600px]">
                {locations.length > 0 ? (
                  <div
                    ref={mapDivRef}
                    style={{ height: "100%", width: "100%" }}
                  />
                ) : (
                  <div className="h-full flex items-center justify-center bg-gray-100">
                    <p className="text-gray-500">
                      No suitable locations found
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Details Panel */}
          <div className="space-y-4">
            {selectedLocation && (
              <div className="bg-white rounded-xl shadow-lg p-6">
                <h3 className="text-xl font-bold text-gray-800 mb-4">
                  {selectedLocation.name}
                </h3>

                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gradient-to-br from-blue-50 to-green-50 rounded-lg">
                    <div className="flex items-center space-x-3">
                      <TrendingUp className="w-6 h-6 text-blue-600" />
                      <span className="font-medium text-gray-700">
                        Distance From Service Centre
                      </span>
                    </div>
                    <span className="text-2xl font-bold text-blue-600">
                      {selectedLocation.distanceKm
                        ? `${selectedLocation.distanceKm} km`
                        : "N/A"}
                    </span>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-gray-600 text-sm">
                      {selectedLocation.insights}
                    </p>
                  </div>

                  {selectedLocation.mapUrl && (
                    <a
                      href={selectedLocation.mapUrl}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-2 text-blue-600 hover:underline text-sm"
                    >
                      <Map className="w-4 h-4" />
                      Open in Google Maps
                    </a>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
