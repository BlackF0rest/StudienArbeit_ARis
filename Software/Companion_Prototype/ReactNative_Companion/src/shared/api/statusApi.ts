import { apiRequest } from '@shared/api/client';

export type ApiStatus = {
  app: string;
  version: string;
  health: string;
  handshake?: {
    protocol?: string;
    device?: {
      device_id?: string;
      friendly_name?: string;
      firmware_version?: string;
      app_version?: string;
      capabilities?: string[];
    };
  };
  hardware_ready?: {
    ok: boolean;
    [key: string]: unknown;
  };
  endpoints?: Record<string, string>;
  [key: string]: unknown;
};

export type MainInfo = {
  battery_percent: number;
  temperature_c: number;
  humidity_percent: number;
  battery_unit: string;
  temperature_unit: string;
  humidity_unit: string;
  pinmap?: unknown;
};

export type SensorSnapshot = {
  [key: string]: unknown;
};

export const statusApi = {
  getStatus: () => apiRequest<ApiStatus>('/api/status'),
  getMainInfo: () => apiRequest<MainInfo>('/api/mainInfo'),
  getSensorSnapshot: () => apiRequest<SensorSnapshot>('/api/sensors')
};
