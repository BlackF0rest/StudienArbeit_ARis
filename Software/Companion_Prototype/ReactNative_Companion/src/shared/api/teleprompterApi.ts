import { apiRequest } from '@shared/api/client';

export type TeleprompterConfig = {
  text: string;
  speed: number;
  fontSize: number;
  fontColor: string;
  backgroundColor: string;
  fontFamily: string;
  lineHeight: number;
  opacity: number;
};

export type TeleprompterHistoryEntry = {
  id: number;
  text: string;
  speed: number;
  fontSize: number;
  timestamp: string;
};

export type SendTeleprompterPayload = {
  text: string;
  speed?: number;
  fontSize?: number;
  fontColor?: string;
  backgroundColor?: string;
  fontFamily?: string;
  lineHeight?: number;
  opacity?: number;
};

export type TeleprompterSendResponse = {
  status: 'success';
  message: string;
  timestamp: string;
  warnings?: string[];
};

export type TeleprompterResetResponse = {
  status: 'reset';
  config: TeleprompterConfig;
};

export const teleprompterApi = {
  getConfig: () => apiRequest<TeleprompterConfig>('/api/teleprompter'),
  getCurrent: () => apiRequest<TeleprompterConfig>('/api/teleprompter/current'),
  getHistory: () => apiRequest<TeleprompterHistoryEntry[]>('/api/teleprompter/history'),
  sendToGlasses: (payload: SendTeleprompterPayload) =>
    apiRequest<TeleprompterSendResponse>('/api/teleprompter/send', {
      method: 'POST',
      body: payload
    }),
  reset: () =>
    apiRequest<TeleprompterResetResponse>('/api/teleprompter/reset', {
      method: 'POST'
    })
};
