import { apiRequest } from '@shared/api/client';

export type DeviceSettings = {
  brightness?: number;
  volume?: number;
  language?: string;
  flags?: Record<string, boolean>;
  runtime_flags?: Record<string, boolean>;
  [key: string]: unknown;
};

export const settingsApi = {
  getDeviceSettings: () => apiRequest<DeviceSettings>('/api/settings/device'),
  updateDeviceSettings: (payload: DeviceSettings) =>
    apiRequest<DeviceSettings>('/api/settings/device', {
      method: 'PATCH',
      body: payload
    })
};
