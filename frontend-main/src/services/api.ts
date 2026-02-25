const API_BASE_URL =
  import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/* =======================
   Interfaces
======================= */

export interface BusinessType {
  id: string;
  name: string;
}

export interface Strategy {
  id: string;
  title: string;
  description: string;
  recommendations: string[];
}

export interface KPIData {
  growthScore: number;
  demandLevel: string;
  riskLevel: string;
  insight: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  locations?: LocationData[];
}

export interface AnalyticsData {
  categories: string[];
  demand: number[];
  growth: number[];
}

export interface LocationData {
  id: string;
  name: string;
  latitude: number;
  longitude: number;
  insights: string;
  distanceKm?: number;
  score?: number;
  mapUrl?: string;
}

/* =======================
   API Service
======================= */

class ApiService {
  private async fetchWithErrorHandling(
    url: string,
    options?: RequestInit
  ) {
    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  /* -------- Business APIs -------- */

  async getBusinessTypes(): Promise<BusinessType[]> {
    return this.fetchWithErrorHandling('/business-types/');
  }

  async getStrategy(
    businessType: string,
    location: string
  ): Promise<Strategy> {
    return this.fetchWithErrorHandling('/strategy/', {
      method: 'POST',
      body: JSON.stringify({ businessType, location }),
    });
  }

  async getKPIData(businessType: string): Promise<KPIData> {
    return this.fetchWithErrorHandling(
      `/kpi/?businessType=${businessType}`
    );
  }

  /* -------- Chatbot (SESSION + HISTORY) -------- */

  async sendChatMessage(payload: {
    message: string;
    sessionId: string;
    businessType?: string;
  }): Promise<{ content: string; sessionId: string; locations?: LocationData[] }> {
    return this.fetchWithErrorHandling('/chat/', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async getChatHistory(sessionId: string): Promise<ChatMessage[]> {
    return this.fetchWithErrorHandling(
      `/chat-history/?sessionId=${sessionId}`
    );
  }
  async getChatSessions(): Promise<{ sessionId: string }[]> {
  return this.fetchWithErrorHandling('/chat-sessions/');
}

  async deleteChatSession(sessionId: string): Promise<{ deleted: boolean; sessionId: string }> {
    return this.fetchWithErrorHandling(`/chat-sessions/${sessionId}/`, {
      method: 'DELETE',
    });
  }

  /* -------- Analytics -------- */

  async getAnalytics(
    businessType: string
  ): Promise<AnalyticsData> {
    return this.fetchWithErrorHandling(
      `/analytics/?businessType=${businessType}`
    );
  }

  /* -------- Locations -------- */

  async getLocations(
    businessType: string,
    area?: string
  ): Promise<LocationData[]> {
    const qs = new URLSearchParams({ businessType });
    if (area) qs.set('area', area);
    return this.fetchWithErrorHandling(`/locations/?${qs.toString()}`);
  }

  async getLocationInsights(
    locationId: string
  ): Promise<LocationData> {
    return this.fetchWithErrorHandling(
      `/locations/${locationId}/`
    );
  }
}

/* =======================
   Export
======================= */

export const apiService = new ApiService();
