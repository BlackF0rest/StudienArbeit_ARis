import { apiRequest } from '@shared/api/client';

export type NavigationSnapshot = {
  heading: number | null;
  orientation: number | null;
  timestamp: string;
  source: {
    provider: string;
    sensor?: string;
    event_types?: string[];
  };
};

export const navigationApi = {
  getCurrent: () => apiRequest<NavigationSnapshot>('/api/navigation/current')
};
