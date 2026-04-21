# ReactNative Companion

React-Native (Expo) Basisprojekt für die ARis-Companion-App.

## Projektstruktur

```text
src/
  app/
    navigation/
    screens/
  features/
    connection/
    navigation/
    settings/
    teleprompter/
  shared/
    api/
    state/
    types/
```

## Voraussetzungen

- Node.js 20+
- npm 10+
- Expo CLI (optional global)
- Für Device-Tests: Expo Go App oder Android/iOS-Simulator

## Installation

```bash
npm install
```

## Entwicklung starten

```bash
npm run start
```

Weitere Targets:

```bash
npm run android
npm run ios
npm run web
```

## Build-/Type-Checks

```bash
npm run lint
npm run typecheck
```

## Laufzeitkonfiguration

API-Endpunkte werden über Expo Public Env-Variablen gesetzt:

- `EXPO_PUBLIC_API_BASE_URL` (Default: `http://localhost:3000`)

Beispiel:

```bash
EXPO_PUBLIC_API_BASE_URL=https://api.example.local npm run start
```

## Architektur-Hinweise

- `src/app`: Navigation und Screen-Komposition
- `src/features/*`: gekapselte Feature-Module
- `src/shared/*`: gemeinsame Typen, API-Helfer und State-Bausteine

## Connection Diagnostics

Im Screen **Connection** gibt es eine Diagnostics-Ansicht mit:

- letzter erfolgreicher Anfrage (Pfad),
- letzter gemessener Latenz,
- Fehlerrate (Fehler/Requests),
- zuletzt empfangenem Backend-Timestamp,
- letzter Trace-ID.

Zusätzlich schreibt der Companion pro Request strukturierte Logs mit Trace-ID (`[Companion][request|response|error]`), damit sich Client- und Backend-Logs korrelieren lassen.

## Typische Fehlerbilder (Companion ↔ Backend)

### 1) Falsches WLAN / anderes Netzwerk

**Symptom:** Requests schlagen mit `network_error` oder `timeout` fehl, häufig 100% Fehlerrate in der Diagnostics-Ansicht.  
**Ursache:** Smartphone/Tablet ist nicht im selben Netzwerk wie das Backend (z. B. Mobilfunk aktiv, falsche SSID).  
**Maßnahmen:**

- Gleiches WLAN für Companion-Device und Backend sicherstellen.
- Mobilfunk testweise deaktivieren.
- Backend-IP aus dem Zielnetz im Companion als `EXPO_PUBLIC_API_BASE_URL` setzen.

### 2) IP-Wechsel des Backends

**Symptom:** Verbindung war vorher stabil, danach plötzlich `network_error`/`timeout`; letzte erfolgreiche Anfrage bleibt alt.  
**Ursache:** DHCP hat dem Backend eine neue IP gegeben (z. B. Router-Neustart).  
**Maßnahmen:**

- Aktuelle Backend-IP prüfen (`hostname -I` / Router DHCP-Liste).
- Companion-Basis-URL aktualisieren und App neu starten.
- Optional statische DHCP-Lease für das Backend einrichten.

### 3) Backend nicht erreichbar / Dienst down

**Symptom:** Keine erfolgreiche Anfrage mehr, meist `timeout` oder `http_error` bei Gateway/Proxy.  
**Ursache:** Backend-Prozess gestoppt, Crash oder Host ausgeschaltet.  
**Maßnahmen:**

- Backend-Service-Status prüfen (z. B. `systemctl status aris-backend` auf dem Zielsystem).
- Logs mit Trace-ID vergleichen (Companion-Konsole ↔ Backend-Logs).
- Service neu starten und Health-/Status-Endpoint testen.
