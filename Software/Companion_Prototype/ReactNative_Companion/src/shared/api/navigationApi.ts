import { apiRequest } from '@shared/api/client';

export type NavigationState = {
  route: string;
  next_maneuver?: string;
  distance_m?: number;
  eta_seconds?: number;
  [key: string]: unknown;
};

export type NavigationRouteRequest = {
  destination: string;
  mode?: 'driving' | 'walking' | 'cycling';
  [key: string]: unknown;
};

/**
 * Vorläufiges Service-Modul.
 * Der Endpoint kann später auf einen dedizierten Navigation-Service umgestellt werden.
 */
export const navigationApi = {
  getState: () => apiRequest<NavigationState>('/api/navigation/state'),
  calculateRoute: (payload: NavigationRouteRequest) =>
    apiRequest<NavigationState>('/api/navigation/route', {
      method: 'POST',
      body: payload
    })
};
