import { useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ApiClientError } from '@shared/api/client';
import { statusApi } from '@shared/api/statusApi';
import { resetDiagnostics, useConnectionState } from '@shared/state/store';

const formatTimestamp = (timestamp?: string) => {
  if (!timestamp) {
    return '—';
  }

  const parsed = new Date(timestamp);
  if (Number.isNaN(parsed.getTime())) {
    return timestamp;
  }

  return parsed.toLocaleString();
};

export const ConnectionPanel = () => {
  const { state, diagnostics, setState } = useConnectionState();
  const [pingState, setPingState] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [pingMessage, setPingMessage] = useState<string>();

  const handleToggleConnection = () => {
    setState(prev => (prev === 'connected' ? 'disconnected' : 'connected'));
  };

  const handlePing = async () => {
    setPingState('loading');
    setPingMessage(undefined);

    try {
      await statusApi.getStatus();
      setPingState('success');
      setPingMessage('Status erfolgreich abgerufen.');
      setState('connected');
    } catch (error) {
      setPingState('error');
      setState('disconnected');
      if (error instanceof ApiClientError) {
        setPingMessage(`${error.message}${error.traceId ? ` (trace: ${error.traceId})` : ''}`);
      } else if (error instanceof Error) {
        setPingMessage(error.message);
      } else {
        setPingMessage('Unbekannter Fehler beim Statusabruf.');
      }
    }
  };

  const errorRate = useMemo(() => {
    if (diagnostics.totalRequests === 0) {
      return '0.0%';
    }

    return `${((diagnostics.failedRequests / diagnostics.totalRequests) * 100).toFixed(1)}%`;
  }, [diagnostics.failedRequests, diagnostics.totalRequests]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Connection</Text>
      <Text style={styles.status}>Status: {state}</Text>

      <View style={styles.actionsRow}>
        <Pressable style={styles.button} onPress={handleToggleConnection}>
          <Text style={styles.buttonLabel}>Toggle Connection</Text>
        </Pressable>
        <Pressable style={[styles.button, pingState === 'loading' && styles.buttonDisabled]} onPress={() => void handlePing()} disabled={pingState === 'loading'}>
          <Text style={styles.buttonLabel}>Status prüfen</Text>
        </Pressable>
      </View>

      <View style={styles.diagnosticsCard}>
        <Text style={styles.cardTitle}>Connection Diagnostics</Text>
        <Text style={styles.diagnosticLine}>Letzte erfolgreiche Anfrage: {diagnostics.lastSuccessfulRequest ?? '—'}</Text>
        <Text style={styles.diagnosticLine}>Latenz: {diagnostics.lastLatencyMs !== undefined ? `${diagnostics.lastLatencyMs} ms` : '—'}</Text>
        <Text style={styles.diagnosticLine}>Fehlerrate: {errorRate} ({diagnostics.failedRequests}/{diagnostics.totalRequests})</Text>
        <Text style={styles.diagnosticLine}>Zuletzt empfangener Timestamp: {formatTimestamp(diagnostics.lastReceivedTimestamp)}</Text>
        <Text style={styles.diagnosticMeta}>Letzte Trace-ID: {diagnostics.lastTraceId ?? '—'}</Text>

        <Pressable style={styles.secondaryButton} onPress={resetDiagnostics}>
          <Text style={styles.secondaryButtonLabel}>Diagnostik zurücksetzen</Text>
        </Pressable>
      </View>

      {pingMessage ? <Text style={pingState === 'error' ? styles.errorText : styles.infoText}>{pingMessage}</Text> : null}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 12,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#111827'
  },
  title: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '600'
  },
  status: {
    color: '#d1d5db',
    fontSize: 16
  },
  actionsRow: {
    flexDirection: 'row',
    gap: 10
  },
  button: {
    flex: 1,
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'center'
  },
  buttonDisabled: {
    opacity: 0.6
  },
  buttonLabel: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600'
  },
  diagnosticsCard: {
    backgroundColor: '#0b1220',
    borderRadius: 10,
    padding: 12,
    gap: 6,
    borderWidth: 1,
    borderColor: '#1f2937'
  },
  cardTitle: {
    color: '#f9fafb',
    fontWeight: '700',
    fontSize: 16,
    marginBottom: 4
  },
  diagnosticLine: {
    color: '#d1d5db',
    fontSize: 14
  },
  diagnosticMeta: {
    color: '#9ca3af',
    fontSize: 12,
    marginTop: 4
  },
  secondaryButton: {
    marginTop: 8,
    alignSelf: 'flex-start',
    backgroundColor: '#374151',
    borderRadius: 6,
    paddingHorizontal: 10,
    paddingVertical: 8
  },
  secondaryButtonLabel: {
    color: '#f3f4f6',
    fontWeight: '600',
    fontSize: 12
  },
  infoText: {
    color: '#93c5fd',
    fontSize: 13
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 13
  }
});
