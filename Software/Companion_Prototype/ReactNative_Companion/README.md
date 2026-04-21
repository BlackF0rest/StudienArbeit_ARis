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
