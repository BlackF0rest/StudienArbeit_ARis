import { useCallback, useEffect, useMemo, useState } from 'react';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { ApiClientError } from '@shared/api/client';
import { navigationApi, type NavigationSnapshot } from '@shared/api/navigationApi';

const POLL_INTERVAL_MS = 3_000;
const STALE_AFTER_MS = 10_000;

const formatApiError = (error: unknown): string => {
  if (error instanceof ApiClientError) {
    if (error.code === 'timeout') return 'Zeitüberschreitung beim Laden der Navigationsdaten.';
    if (error.code === 'network_error') return 'Netzwerkfehler. Backend nicht erreichbar.';
    if (error.code === 'invalid_response') return 'Ungültige Antwort vom Backend.';
    return `Backend-Fehler: ${error.message}`;
  }

  return error instanceof Error ? error.message : 'Unbekannter Fehler';
};

const asLocalDateTime = (iso: string | undefined): string => {
  if (!iso) return 'n/a';
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString();
};

const getAgeMs = (iso: string | undefined): number | null => {
  if (!iso) return null;
  const ts = Date.parse(iso);
  if (Number.isNaN(ts)) return null;
  return Date.now() - ts;
};

export const NavigationReadView = () => {
  const [snapshot, setSnapshot] = useState<NavigationSnapshot | null>(null);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const current = await navigationApi.getCurrent();
      setSnapshot(current);
      setError(null);
    } catch (err) {
      setError(formatApiError(err));
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refresh();

    const intervalId = setInterval(() => {
      void refresh();
    }, POLL_INTERVAL_MS);

    return () => clearInterval(intervalId);
  }, [refresh]);

  const snapshotAgeMs = useMemo(() => getAgeMs(snapshot?.timestamp), [snapshot?.timestamp]);
  const isStale = typeof snapshotAgeMs === 'number' && snapshotAgeMs > STALE_AFTER_MS;

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Navigation (Read)</Text>
      <Text style={styles.subtitle}>Polling alle {POLL_INTERVAL_MS / 1000}s · Stale ab {STALE_AFTER_MS / 1000}s</Text>

      {error ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Fehler</Text>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : null}

      <View style={styles.panel}>
        <View style={styles.rowBetween}>
          <Text style={styles.label}>Status</Text>
          <Text style={[styles.value, isStale ? styles.stale : styles.fresh]}>{isStale ? 'STALE DATA' : 'Fresh'}</Text>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.label}>Heading</Text>
          <Text style={styles.value}>{snapshot?.heading ?? 'n/a'}</Text>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.label}>Orientation</Text>
          <Text style={styles.value}>{snapshot?.orientation ?? 'n/a'}</Text>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.label}>Timestamp</Text>
          <Text style={styles.value}>{asLocalDateTime(snapshot?.timestamp)}</Text>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.label}>Source</Text>
          <Text style={styles.value}>{snapshot?.source?.provider ?? 'n/a'}</Text>
        </View>

        <View style={styles.rowBetween}>
          <Text style={styles.label}>Alter</Text>
          <Text style={styles.value}>{typeof snapshotAgeMs === 'number' ? `${Math.max(0, Math.round(snapshotAgeMs / 1000))}s` : 'n/a'}</Text>
        </View>
      </View>

      <Pressable onPress={() => void refresh()} style={[styles.refreshButton, isRefreshing ? styles.refreshDisabled : null]} disabled={isRefreshing}>
        <Text style={styles.refreshLabel}>{isRefreshing ? 'Aktualisiere…' : 'Jetzt aktualisieren'}</Text>
      </Pressable>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 12
  },
  title: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: '700'
  },
  subtitle: {
    color: '#9ca3af'
  },
  panel: {
    backgroundColor: '#1f2937',
    borderRadius: 12,
    padding: 12,
    gap: 10
  },
  rowBetween: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 8
  },
  label: {
    color: '#d1d5db',
    fontWeight: '600'
  },
  value: {
    color: '#ffffff',
    flexShrink: 1,
    textAlign: 'right'
  },
  stale: {
    color: '#f59e0b',
    fontWeight: '700'
  },
  fresh: {
    color: '#34d399',
    fontWeight: '700'
  },
  refreshButton: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'center'
  },
  refreshDisabled: {
    opacity: 0.6
  },
  refreshLabel: {
    color: '#ffffff',
    fontWeight: '700'
  },
  errorBox: {
    borderWidth: 1,
    borderColor: '#f87171',
    borderRadius: 8,
    padding: 10,
    backgroundColor: '#7f1d1d'
  },
  errorTitle: {
    color: '#fecaca',
    fontWeight: '700'
  },
  errorText: {
    color: '#fee2e2'
  }
});
