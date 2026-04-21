import { useState } from 'react';

export type ConnectionState = 'disconnected' | 'connecting' | 'connected';

export const useConnectionState = () => {
  const [state, setState] = useState<ConnectionState>('disconnected');
  return { state, setState };
};
