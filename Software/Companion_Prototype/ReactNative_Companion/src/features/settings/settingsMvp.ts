export type SettingSource = 'Runtime' | 'Backend';

export type SettingSpec = {
  id: string;
  label: string;
  source: SettingSource;
  validation: string;
  errorFeedback: string;
};

export const SETTINGS_MVP_SPECS: SettingSpec[] = [
  {
    id: 'connection-status',
    label: 'Verbindungsstatus',
    source: 'Runtime',
    validation: 'Read-only Statuswert (disconnected | connecting | connected).',
    errorFeedback: 'Bei unbekanntem Status wird "unknown" angezeigt und ein Hinweis eingeblendet.'
  },
  {
    id: 'teleprompter-defaults',
    label: 'Teleprompter Defaults',
    source: 'Backend',
    validation:
      'Geschwindigkeit 10-400 wpm, Schriftgröße 12-96 px, Farbe als Hex (#RRGGBB). Ungültige Eingaben blockieren Save.',
    errorFeedback:
      'Save wird nur nach Backend-ACK + Read-After-Write als erfolgreich markiert; sonst klare Fehlermeldung mit Retry.'
  },
  {
    id: 'runtime-flags',
    label: 'Betriebsflags',
    source: 'Backend',
    validation: 'Nur boolesche Flags aus Backend-Antwort; nicht-boolesche Felder werden ignoriert.',
    errorFeedback:
      'Falls Flags nicht verfügbar sind oder Speichern fehlschlägt, wird ein sichtbarer Fehler statt stillem Fehlschlag ausgegeben.'
  }
];

const HEX_COLOR_REGEX = /^#([0-9a-fA-F]{6})$/;

export const validateTeleprompterDefaults = (values: {
  speed: number;
  fontSize: number;
  fontColor: string;
}) => {
  if (!Number.isFinite(values.speed) || values.speed < 10 || values.speed > 400) {
    return 'Geschwindigkeit muss zwischen 10 und 400 liegen.';
  }

  if (!Number.isFinite(values.fontSize) || values.fontSize < 12 || values.fontSize > 96) {
    return 'Schriftgröße muss zwischen 12 und 96 liegen.';
  }

  if (!HEX_COLOR_REGEX.test(values.fontColor)) {
    return 'Schriftfarbe muss ein Hex-Wert im Format #RRGGBB sein.';
  }

  return undefined;
};
