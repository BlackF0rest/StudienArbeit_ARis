import { useSyncExternalStore } from 'react';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

export type ConnectionDiagnostics = {
  totalRequests: number;
  failedRequests: number;
  lastSuccessfulRequest?: string;
  lastLatencyMs?: number;
  lastReceivedTimestamp?: string;
  lastTraceId?: string;
};

export type ConnectionStoreState = {
  status: ConnectionStatus;
  baseUrl: string;
  traceId?: string;
  diagnostics: ConnectionDiagnostics;
};

type StateUpdater<T> = T | ((previous: T) => T);

const defaultBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:3000';

const emptyDiagnostics = (): ConnectionDiagnostics => ({
  totalRequests: 0,
  failedRequests: 0
});

let connectionState: ConnectionStoreState = {
  status: 'disconnected',
  baseUrl: defaultBaseUrl,
  diagnostics: emptyDiagnostics()
};

const listeners = new Set<() => void>();

const notify = () => {
  listeners.forEach(listener => listener());
};

export const getConnectionState = (): ConnectionStoreState => connectionState;

export const setConnectionState = (next: ConnectionStoreState) => {
  connectionState = next;
  notify();
};

export const updateConnectionState = (updater: (previous: ConnectionStoreState) => ConnectionStoreState) => {
  setConnectionState(updater(connectionState));
};

export const resetDiagnostics = () => {
  updateConnectionState(previous => ({
    ...previous,
    diagnostics: emptyDiagnostics()
  }));
};

export const registerRequestResult = (result: {
  path: string;
  traceId?: string;
  latencyMs: number;
  success: boolean;
  responseTimestamp?: string;
}) => {
  updateConnectionState(previous => ({
    ...previous,
    diagnostics: {
      ...previous.diagnostics,
      totalRequests: previous.diagnostics.totalRequests + 1,
      failedRequests: previous.diagnostics.failedRequests + (result.success ? 0 : 1),
      lastLatencyMs: result.latencyMs,
      lastTraceId: result.traceId,
      lastReceivedTimestamp: result.responseTimestamp ?? previous.diagnostics.lastReceivedTimestamp,
      lastSuccessfulRequest: result.success ? result.path : previous.diagnostics.lastSuccessfulRequest
    }
  }));
};

export const useConnectionStore = (): ConnectionStoreState =>
  useSyncExternalStore(
    listener => {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
    getConnectionState,
    getConnectionState
  );

export const useConnectionState = () => {
  const state = useConnectionStore();

  return {
    state: state.status,
    baseUrl: state.baseUrl,
    traceId: state.traceId,
    diagnostics: state.diagnostics,
    setState: (next: StateUpdater<ConnectionStatus>) => {
      updateConnectionState(previous => ({
        ...previous,
        status: typeof next === 'function' ? (next as (value: ConnectionStatus) => ConnectionStatus)(previous.status) : next
      }));
    },
    setBaseUrl: (next: StateUpdater<string>) => {
      updateConnectionState(previous => ({
        ...previous,
        baseUrl: typeof next === 'function' ? (next as (value: string) => string)(previous.baseUrl) : next
      }));
    },
    setTraceId: (next: string | undefined) => {
      updateConnectionState(previous => ({
        ...previous,
        traceId: next
      }));
    }
  };
};
