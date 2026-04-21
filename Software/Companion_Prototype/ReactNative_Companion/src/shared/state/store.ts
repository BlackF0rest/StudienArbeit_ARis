import { useSyncExternalStore } from 'react';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected';

export type ConnectionStoreState = {
  status: ConnectionStatus;
  baseUrl: string;
  traceId?: string;
};

type StateUpdater<T> = T | ((previous: T) => T);

const defaultBaseUrl = process.env.EXPO_PUBLIC_API_BASE_URL ?? 'http://localhost:3000';

let connectionState: ConnectionStoreState = {
  status: 'disconnected',
  baseUrl: defaultBaseUrl
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
