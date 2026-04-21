import { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Switch, Text, TextInput, View } from 'react-native';

import { ApiClientError } from '@shared/api/client';
import { settingsApi } from '@shared/api/settingsApi';
import { useConnectionStore } from '@shared/state/store';
import { teleprompterApi } from '@shared/api/teleprompterApi';

import { SETTINGS_MVP_SPECS, validateTeleprompterDefaults } from './settingsMvp';

type SaveState = {
  kind: 'idle' | 'saving' | 'success' | 'error';
  message?: string;
};

const toErrorMessage = (error: unknown) => {
  if (error instanceof ApiClientError) {
    return `${error.message}${error.traceId ? ` (trace: ${error.traceId})` : ''}`;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return 'Unbekannter Fehler beim Speichern.';
};

const readBooleanFlags = (payload: Record<string, unknown>): Record<string, boolean> => {
  const nested = payload.flags ?? payload.runtime_flags;
  if (!nested || typeof nested !== 'object') {
    return {};
  }

  return Object.fromEntries(
    (Object.entries(nested as Record<string, unknown>).filter(
      (entry: [string, unknown]) => typeof entry[1] === 'boolean'
    ) as Array<[string, boolean]>)
  );
};

export const SettingsPanel = () => {
  const connection = useConnectionStore();

  const [teleprompterSpeed, setTeleprompterSpeed] = useState('120');
  const [teleprompterFontSize, setTeleprompterFontSize] = useState('28');
  const [teleprompterFontColor, setTeleprompterFontColor] = useState('#FFFFFF');
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const [flagsAvailable, setFlagsAvailable] = useState(false);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | undefined>();
  const [teleprompterSaveState, setTeleprompterSaveState] = useState<SaveState>({ kind: 'idle' });
  const [flagsSaveState, setFlagsSaveState] = useState<SaveState>({ kind: 'idle' });

  useEffect(() => {
    const loadSettings = async () => {
      setLoading(true);
      setLoadError(undefined);

      try {
        const [teleprompter, deviceSettings] = await Promise.all([
          teleprompterApi.getCurrent(),
          settingsApi.getDeviceSettings()
        ]);

        setTeleprompterSpeed(String(Math.round(teleprompter.speed)));
        setTeleprompterFontSize(String(Math.round(teleprompter.fontSize)));
        setTeleprompterFontColor(teleprompter.fontColor.toUpperCase());

        const parsedFlags = readBooleanFlags(deviceSettings as Record<string, unknown>);
        setFlags(parsedFlags);
        setFlagsAvailable(Object.keys(parsedFlags).length > 0);
      } catch (error) {
        setLoadError(toErrorMessage(error));
      } finally {
        setLoading(false);
      }
    };

    void loadSettings();
  }, []);

  const teleprompterValidationError = useMemo(
    () =>
      validateTeleprompterDefaults({
        speed: Number(teleprompterSpeed),
        fontSize: Number(teleprompterFontSize),
        fontColor: teleprompterFontColor.trim()
      }),
    [teleprompterFontColor, teleprompterFontSize, teleprompterSpeed]
  );

  const saveTeleprompterDefaults = async () => {
    if (teleprompterValidationError) {
      setTeleprompterSaveState({ kind: 'error', message: teleprompterValidationError });
      return;
    }

    const expected = {
      speed: Number(teleprompterSpeed),
      fontSize: Number(teleprompterFontSize),
      fontColor: teleprompterFontColor.trim().toUpperCase()
    };

    setTeleprompterSaveState({ kind: 'saving', message: 'Speichere Teleprompter Defaults…' });

    try {
      await teleprompterApi.sendToGlasses({
        text: '',
        ...expected
      });
      const refreshed = await teleprompterApi.getCurrent();

      const confirmed =
        Math.round(refreshed.speed) === expected.speed &&
        Math.round(refreshed.fontSize) === expected.fontSize &&
        refreshed.fontColor.toUpperCase() === expected.fontColor;

      if (!confirmed) {
        throw new Error('Backend hat Änderungen nicht bestätigt (Read-After-Write mismatch).');
      }

      setTeleprompterSaveState({ kind: 'success', message: 'Teleprompter Defaults erfolgreich gespeichert und bestätigt.' });
    } catch (error) {
      setTeleprompterSaveState({ kind: 'error', message: toErrorMessage(error) });
    }
  };

  const toggleFlag = (flagName: string, value: boolean) => {
    setFlags(current => ({
      ...current,
      [flagName]: value
    }));
    setFlagsSaveState({ kind: 'idle' });
  };

  const saveFlags = async () => {
    setFlagsSaveState({ kind: 'saving', message: 'Speichere Betriebsflags…' });

    try {
      await settingsApi.updateDeviceSettings({ flags });
      const refreshed = await settingsApi.getDeviceSettings();
      const refreshedFlags = readBooleanFlags(refreshed as Record<string, unknown>);

      const confirmed =
        Object.keys(flags).length === Object.keys(refreshedFlags).length &&
        Object.entries(flags).every(([key, value]) => refreshedFlags[key] === value);

      if (!confirmed) {
        throw new Error('Backend hat die Betriebsflags nicht bestätigt (Read-After-Write mismatch).');
      }

      setFlagsSaveState({ kind: 'success', message: 'Betriebsflags erfolgreich gespeichert und bestätigt.' });
    } catch (error) {
      setFlagsSaveState({ kind: 'error', message: toErrorMessage(error) });
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Settings (MVP)</Text>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>MVP-Umfang</Text>
        {SETTINGS_MVP_SPECS.map(spec => (
          <View key={spec.id} style={styles.specRow}>
            <Text style={styles.specTitle}>{spec.label}</Text>
            <Text style={styles.specMeta}>Quelle: {spec.source}</Text>
            <Text style={styles.specMeta}>Validierung: {spec.validation}</Text>
            <Text style={styles.specMeta}>Fehlerfeedback: {spec.errorFeedback}</Text>
          </View>
        ))}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Verbindungsstatus</Text>
        <Text style={styles.statusLine}>Runtime Status: {connection.status || 'unknown'}</Text>
        <Text style={styles.caption}>Quelle: Runtime Store (`useConnectionStore`).</Text>
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Teleprompter Defaults</Text>
        <Text style={styles.caption}>Quelle: Backend (`/api/teleprompter/current`, Save via `/api/teleprompter/send`).</Text>

        <Text style={styles.label}>Geschwindigkeit (10-400)</Text>
        <TextInput
          value={teleprompterSpeed}
          onChangeText={setTeleprompterSpeed}
          keyboardType="numeric"
          style={styles.input}
        />

        <Text style={styles.label}>Schriftgröße (12-96)</Text>
        <TextInput
          value={teleprompterFontSize}
          onChangeText={setTeleprompterFontSize}
          keyboardType="numeric"
          style={styles.input}
        />

        <Text style={styles.label}>Schriftfarbe (#RRGGBB)</Text>
        <TextInput value={teleprompterFontColor} onChangeText={setTeleprompterFontColor} autoCapitalize="characters" style={styles.input} />

        {teleprompterValidationError ? <Text style={styles.error}>{teleprompterValidationError}</Text> : null}

        <Pressable
          style={[styles.button, (teleprompterSaveState.kind === 'saving' || Boolean(teleprompterValidationError)) && styles.buttonDisabled]}
          onPress={() => void saveTeleprompterDefaults()}
          disabled={teleprompterSaveState.kind === 'saving' || Boolean(teleprompterValidationError)}
        >
          <Text style={styles.buttonLabel}>Teleprompter Defaults speichern</Text>
        </Pressable>
        {teleprompterSaveState.message ? (
          <Text style={teleprompterSaveState.kind === 'error' ? styles.error : styles.info}>{teleprompterSaveState.message}</Text>
        ) : null}
      </View>

      <View style={styles.card}>
        <Text style={styles.cardTitle}>Betriebsflags</Text>
        <Text style={styles.caption}>Nur verfügbar, wenn das Backend boolesche Flags liefert (`flags` / `runtime_flags`).</Text>

        {flagsAvailable ? (
          Object.entries(flags).map(([flagName, value]) => (
            <View style={styles.flagRow} key={flagName}>
              <Text style={styles.label}>{flagName}</Text>
              <Switch value={value} onValueChange={next => toggleFlag(flagName, next)} />
            </View>
          ))
        ) : (
          <Text style={styles.info}>Keine backendseitigen Betriebsflags verfügbar.</Text>
        )}

        <Pressable
          style={[styles.button, (!flagsAvailable || flagsSaveState.kind === 'saving') && styles.buttonDisabled]}
          onPress={() => void saveFlags()}
          disabled={!flagsAvailable || flagsSaveState.kind === 'saving'}
        >
          <Text style={styles.buttonLabel}>Betriebsflags speichern</Text>
        </Pressable>
        {flagsSaveState.message ? <Text style={flagsSaveState.kind === 'error' ? styles.error : styles.info}>{flagsSaveState.message}</Text> : null}
      </View>

      {loading ? <Text style={styles.info}>Lade Einstellungen…</Text> : null}
      {loadError ? <Text style={styles.error}>Fehler beim Laden: {loadError}</Text> : null}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 12,
    paddingBottom: 24
  },
  title: {
    color: '#ffffff',
    fontSize: 20,
    fontWeight: '700'
  },
  card: {
    gap: 10,
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#111827'
  },
  cardTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600'
  },
  specRow: {
    gap: 2,
    paddingBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937'
  },
  specTitle: {
    color: '#e5e7eb',
    fontSize: 14,
    fontWeight: '600'
  },
  specMeta: {
    color: '#9ca3af',
    fontSize: 12
  },
  caption: {
    color: '#9ca3af',
    fontSize: 12
  },
  statusLine: {
    color: '#d1d5db',
    fontSize: 16,
    fontWeight: '600'
  },
  label: {
    color: '#d1d5db',
    fontSize: 14
  },
  input: {
    backgroundColor: '#0b1220',
    color: '#ffffff',
    borderWidth: 1,
    borderColor: '#374151',
    borderRadius: 8,
    paddingVertical: 8,
    paddingHorizontal: 10
  },
  button: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 12,
    alignItems: 'center'
  },
  buttonDisabled: {
    opacity: 0.45
  },
  buttonLabel: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '600'
  },
  flagRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  error: {
    color: '#fca5a5',
    fontSize: 13
  },
  info: {
    color: '#93c5fd',
    fontSize: 13
  }
});
