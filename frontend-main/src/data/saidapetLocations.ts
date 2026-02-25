export type BusinessType = "showroom" | "service" | "spares";

export interface MicroLocation {
  id: string;
  name: string;
  latitude: number;
  longitude: number;

  // Business-wise density
  density: {
    showroom: number;
    service: number;
    spares: number;
  };

  insights: string;
}

export const SAIDAPET_MICRO_LOCATIONS: MicroLocation[] = [
  {
    id: "railway-station-road",
    name: "Saidapet Railway Station Road",
    latitude: 13.0213,
    longitude: 80.2245,
    density: {
      showroom: 20,
      service: 55,
      spares: 35,
    },
    insights: "Highest commuter flow and service demand"
  },
  {
    id: "anna-salai-junction",
    name: "Anna Salai – Saidapet Junction",
    latitude: 13.0219,
    longitude: 80.2231,
    density: {
      showroom: 25,
      service: 45,
      spares: 40,
    },
    insights: "Heavy vehicle movement and breakdown demand"
  },
  {
    id: "bazaar-road",
    name: "Saidapet Bazaar Road",
    latitude: 13.0238,
    longitude: 80.2269,
    density: {
      showroom: 15,
      service: 25,
      spares: 50,
    },
    insights: "Dense spare parts and accessories market"
  },
  {
    id: "west-mambalam-link",
    name: "Saidapet – West Mambalam Link Road",
    latitude: 13.0201,
    longitude: 80.2149,
    density: {
      showroom: 40,
      service: 20,
      spares: 15,
    },
    insights: "Good frontage and visibility for showrooms"
  },
  {
    id: "guindy-border-road",
    name: "Saidapet – Guindy Border Road",
    latitude: 13.0189,
    longitude: 80.2188,
    density: {
      showroom: 35,
      service: 30,
      spares: 25,
    },
    insights: "Transit corridor between residential and IT areas"
  }
];
