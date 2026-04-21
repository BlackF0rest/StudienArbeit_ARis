import { useEffect, useMemo, useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import { ApiClientError } from '@shared/api/client';
import { teleprompterApi, type SendTeleprompterPayload, type TeleprompterConfig, type TeleprompterHistoryEntry } from '@shared/api/teleprompterApi';

const TEXT_MIN = 1;
const TEXT_MAX = 4000;
const NUMBER_RANGES = {
  speed: { min: 1, max: 200 },
  fontSize: { min: 0.5, max: 10 },
  lineHeight: { min: 1, max: 3 },
  opacity: { min: 0, max: 1 }
};

type FormErrors = Partial<Record<'text' | 'speed' | 'fontSize' | 'lineHeight' | 'opacity', string>>;

const formatApiError = (error: unknown): string => {
  if (error instanceof ApiClientError) {
    const backendMap: Record<string, string> = {
      invalid_teleprompter_payload:
        'Backend meldet ein ungültiges Teleprompter-Payload. Bitte Eingaben prüfen und erneut senden.'
    };

    if (error.backendCode && backendMap[error.backendCode]) {
      return backendMap[error.backendCode];
    }

    if (error.code === 'timeout') return 'Zeitüberschreitung beim Server. Bitte Verbindung prüfen.';
    if (error.code === 'network_error') return 'Netzwerkfehler. Ist das Backend erreichbar?';
    if (error.code === 'invalid_response') return 'Serverantwort konnte nicht gelesen werden.';
    if (error.code === 'http_error') return `Backend-Fehler (${error.status ?? 'ohne Status'}): ${error.message}`;
    return `Unbekannter API-Fehler: ${error.message}`;
  }

  return error instanceof Error ? error.message : 'Unbekannter Fehler';
};

const parseOptionalNumber = (
  value: string,
  key: keyof typeof NUMBER_RANGES,
  errors: FormErrors
): number | undefined => {
  if (!value.trim()) return undefined;

  const parsed = Number(value);
  if (Number.isNaN(parsed)) {
    errors[key] = 'Muss eine Zahl sein.';
    return undefined;
  }

  const range = NUMBER_RANGES[key];
  if (parsed < range.min || parsed > range.max) {
    errors[key] = `Wert muss zwischen ${range.min} und ${range.max} liegen.`;
    return undefined;
  }

  return parsed;
};

export const TeleprompterView = () => {
  const [current, setCurrent] = useState<TeleprompterConfig | null>(null);
  const [history, setHistory] = useState<TeleprompterHistoryEntry[]>([]);
  const [text, setText] = useState('');
  const [speed, setSpeed] = useState('');
  const [fontSize, setFontSize] = useState('');
  const [lineHeight, setLineHeight] = useState('');
  const [opacity, setOpacity] = useState('');
  const [apiError, setApiError] = useState<string | null>(null);
  const [formErrors, setFormErrors] = useState<FormErrors>({});
  const [isBusy, setIsBusy] = useState(false);

  const refreshData = async () => {
    setApiError(null);
    setIsBusy(true);
    try {
      const [currentConfig, historyEntries] = await Promise.all([teleprompterApi.getCurrent(), teleprompterApi.getHistory()]);
      setCurrent(currentConfig);
      setHistory(historyEntries);
    } catch (error) {
      setApiError(formatApiError(error));
    } finally {
      setIsBusy(false);
    }
  };

  useEffect(() => {
    void refreshData();
  }, []);

  const historyPreview = useMemo(() => history.slice(0, 5), [history]);

  const handleSend = async () => {
    const nextErrors: FormErrors = {};

    if (!text.trim()) {
      nextErrors.text = 'Text darf nicht leer sein.';
    } else if (text.length < TEXT_MIN || text.length > TEXT_MAX) {
      nextErrors.text = `Textlänge muss zwischen ${TEXT_MIN} und ${TEXT_MAX} Zeichen liegen.`;
    }

    const payload: SendTeleprompterPayload = { text: text.trim() };
    const parsedSpeed = parseOptionalNumber(speed, 'speed', nextErrors);
    const parsedFontSize = parseOptionalNumber(fontSize, 'fontSize', nextErrors);
    const parsedLineHeight = parseOptionalNumber(lineHeight, 'lineHeight', nextErrors);
    const parsedOpacity = parseOptionalNumber(opacity, 'opacity', nextErrors);

    if (parsedSpeed !== undefined) payload.speed = parsedSpeed;
    if (parsedFontSize !== undefined) payload.fontSize = parsedFontSize;
    if (parsedLineHeight !== undefined) payload.lineHeight = parsedLineHeight;
    if (parsedOpacity !== undefined) payload.opacity = parsedOpacity;

    setFormErrors(nextErrors);
    if (Object.keys(nextErrors).length > 0) return;

    setApiError(null);
    setIsBusy(true);
    try {
      await teleprompterApi.sendToGlasses(payload);
      setText('');
      setSpeed('');
      setFontSize('');
      setLineHeight('');
      setOpacity('');
      await refreshData();
    } catch (error) {
      setApiError(formatApiError(error));
    } finally {
      setIsBusy(false);
    }
  };

  const handleReset = async () => {
    setApiError(null);
    setIsBusy(true);
    try {
      const resetResult = await teleprompterApi.reset();
      setCurrent(resetResult.config);
      await refreshData();
    } catch (error) {
      setApiError(formatApiError(error));
    } finally {
      setIsBusy(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Teleprompter</Text>

      {apiError ? (
        <View style={styles.errorBox}>
          <Text style={styles.errorTitle}>Fehler bei der Backend-Kommunikation</Text>
          <Text style={styles.errorText}>{apiError}</Text>
        </View>
      ) : null}

      <View style={styles.panel}>
        <Text style={styles.sectionTitle}>Neuen Text senden</Text>
        <TextInput
          style={[styles.input, styles.multilineInput, formErrors.text ? styles.inputError : null]}
          placeholder="Teleprompter-Text eingeben"
          placeholderTextColor="#6b7280"
          value={text}
          onChangeText={setText}
          multiline
        />
        {formErrors.text ? <Text style={styles.validationText}>{formErrors.text}</Text> : null}
        <Text style={styles.helperText}>
          Länge: {text.length}/{TEXT_MAX} Zeichen
        </Text>

        <View style={styles.row}>
          <View style={styles.field}>
            <Text style={styles.label}>Speed (optional)</Text>
            <TextInput
              style={[styles.input, formErrors.speed ? styles.inputError : null]}
              value={speed}
              onChangeText={setSpeed}
              keyboardType="numeric"
              placeholder="1-200"
              placeholderTextColor="#6b7280"
            />
            {formErrors.speed ? <Text style={styles.validationText}>{formErrors.speed}</Text> : null}
          </View>
          <View style={styles.field}>
            <Text style={styles.label}>FontSize (optional)</Text>
            <TextInput
              style={[styles.input, formErrors.fontSize ? styles.inputError : null]}
              value={fontSize}
              onChangeText={setFontSize}
              keyboardType="numeric"
              placeholder="0.5-10"
              placeholderTextColor="#6b7280"
            />
            {formErrors.fontSize ? <Text style={styles.validationText}>{formErrors.fontSize}</Text> : null}
          </View>
        </View>

        <View style={styles.row}>
          <View style={styles.field}>
            <Text style={styles.label}>LineHeight (optional)</Text>
            <TextInput
              style={[styles.input, formErrors.lineHeight ? styles.inputError : null]}
              value={lineHeight}
              onChangeText={setLineHeight}
              keyboardType="numeric"
              placeholder="1-3"
              placeholderTextColor="#6b7280"
            />
            {formErrors.lineHeight ? <Text style={styles.validationText}>{formErrors.lineHeight}</Text> : null}
          </View>
          <View style={styles.field}>
            <Text style={styles.label}>Opacity (optional)</Text>
            <TextInput
              style={[styles.input, formErrors.opacity ? styles.inputError : null]}
              value={opacity}
              onChangeText={setOpacity}
              keyboardType="numeric"
              placeholder="0-1"
              placeholderTextColor="#6b7280"
            />
            {formErrors.opacity ? <Text style={styles.validationText}>{formErrors.opacity}</Text> : null}
          </View>
        </View>

        <View style={styles.buttonRow}>
          <Pressable disabled={isBusy} style={[styles.button, isBusy ? styles.buttonDisabled : null]} onPress={handleSend}>
            <Text style={styles.buttonLabel}>{isBusy ? 'Bitte warten...' : 'Text senden'}</Text>
          </Pressable>
          <Pressable
            disabled={isBusy}
            style={[styles.button, styles.secondaryButton, isBusy ? styles.buttonDisabled : null]}
            onPress={handleReset}
          >
            <Text style={styles.buttonLabel}>Reset</Text>
          </Pressable>
        </View>
      </View>

      <View style={styles.panel}>
        <Text style={styles.sectionTitle}>Aktueller Inhalt</Text>
        <Text style={styles.currentText}>{current?.text ?? 'Kein Inhalt geladen.'}</Text>
      </View>

      <View style={styles.panel}>
        <Text style={styles.sectionTitle}>Verlauf (neueste 5)</Text>
        {historyPreview.length === 0 ? (
          <Text style={styles.helperText}>Noch keine Einträge vorhanden.</Text>
        ) : (
          historyPreview.map(entry => (
            <View key={entry.id} style={styles.historyItem}>
              <Text style={styles.historyMeta}>
                #{entry.id} · {entry.timestamp} · Speed {entry.speed}
              </Text>
              <Text style={styles.historyText}>{entry.text}</Text>
            </View>
          ))
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    gap: 12,
    padding: 16,
    paddingBottom: 36
  },
  title: {
    color: '#ffffff',
    fontSize: 24,
    fontWeight: '600'
  },
  panel: {
    gap: 10,
    padding: 14,
    borderRadius: 12,
    backgroundColor: '#111827'
  },
  sectionTitle: {
    color: '#ffffff',
    fontSize: 18,
    fontWeight: '600'
  },
  currentText: {
    color: '#e5e7eb',
    fontSize: 16,
    lineHeight: 22
  },
  row: {
    flexDirection: 'row',
    gap: 10
  },
  field: {
    flex: 1,
    gap: 4
  },
  label: {
    color: '#cbd5e1',
    fontSize: 13
  },
  input: {
    backgroundColor: '#0f172a',
    borderWidth: 1,
    borderColor: '#334155',
    borderRadius: 8,
    color: '#f8fafc',
    paddingHorizontal: 10,
    paddingVertical: 8,
    fontSize: 14
  },
  multilineInput: {
    minHeight: 110,
    textAlignVertical: 'top'
  },
  inputError: {
    borderColor: '#ef4444'
  },
  helperText: {
    color: '#94a3b8',
    fontSize: 12
  },
  validationText: {
    color: '#fca5a5',
    fontSize: 12
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 10
  },
  button: {
    backgroundColor: '#2563eb',
    borderRadius: 8,
    paddingVertical: 10,
    paddingHorizontal: 14
  },
  secondaryButton: {
    backgroundColor: '#374151'
  },
  buttonDisabled: {
    opacity: 0.6
  },
  buttonLabel: {
    color: '#ffffff',
    fontWeight: '600'
  },
  errorBox: {
    backgroundColor: '#450a0a',
    borderWidth: 1,
    borderColor: '#dc2626',
    borderRadius: 8,
    padding: 10,
    gap: 4
  },
  errorTitle: {
    color: '#fecaca',
    fontWeight: '700'
  },
  errorText: {
    color: '#fca5a5',
    fontSize: 13
  },
  historyItem: {
    paddingBottom: 10,
    borderBottomWidth: 1,
    borderBottomColor: '#1f2937'
  },
  historyMeta: {
    color: '#93c5fd',
    fontSize: 12,
    marginBottom: 2
  },
  historyText: {
    color: '#e2e8f0',
    fontSize: 14
  }
});
