import { apiRequest } from '@shared/api/client';

export type TeleprompterConfig = {
  speed?: number;
  font_size?: number;
  mirror?: boolean;
  [key: string]: unknown;
};

export type TeleprompterEntry = {
  id?: string | number;
  text?: string;
  created_at?: string;
  [key: string]: unknown;
};

export type SendTeleprompterPayload = {
  text: string;
  speed?: number;
  [key: string]: unknown;
};

export const teleprompterApi = {
  getConfig: () => apiRequest<TeleprompterConfig>('/api/teleprompter'),
  getCurrent: () => apiRequest<TeleprompterEntry>('/api/teleprompter/current'),
  getHistory: () => apiRequest<TeleprompterEntry[]>('/api/teleprompter/history'),
  sendToGlasses: (payload: SendTeleprompterPayload) =>
    apiRequest<TeleprompterEntry>('/api/teleprompter/send', {
      method: 'POST',
      body: payload
    }),
  reset: () =>
    apiRequest<TeleprompterEntry>('/api/teleprompter/reset', {
      method: 'POST'
    })
};
