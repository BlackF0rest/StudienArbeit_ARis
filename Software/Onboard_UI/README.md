# ARIS Onboard UI

Dieses Modul enthält die Onboard-Bedienoberfläche für ARIS (SvelteKit/Vite). Das UI ist für den Einsatz auf dem Zielgerät (u. a. Raspberry Pi Zero 2 W im Kiosk-Betrieb) ausgelegt und trennt klar zwischen launch-relevanten Bedienrouten und Entwicklungs-/Debug-Oberflächen.

## Zweck und Launch-Scope

Die Launch-Freigabe umfasst ausschließlich diese produktiven Bedienrouten:

- `/` – Home/HUD-Einstieg
- `/Navigation` – Navigationsansicht
- `/Teleprompter` – Teleprompter-Ansicht
- `/Messages` – Nachrichten/Kommunikation

Referenz für den offiziell freigegebenen Umfang:

- `docs/release/onboard_route_manifest.md`

## Abgrenzung: Launch-Routen vs. Dev/Debug

Nicht Teil des Launch-Scopes sind:

- `/Debug` – Operator-/Debug-Route
- `/dev/*` – Entwicklungs-Namespace

Diese Routen sind für Entwicklung, Diagnose und interne Verifikation gedacht und dürfen nicht mit der Launch-Freigabe verwechselt werden.

## Voraussetzungen

- Node.js 20.x (empfohlen)
- npm (zu Node passend)

## Lokale Entwicklung

Aus dem Verzeichnis `Software/Onboard_UI`:

```bash
npm ci
npm run dev
```

Danach ist das UI im lokalen Dev-Server erreichbar (Standard bei Vite: `http://localhost:5173`).

## Build (Production)

```bash
npm run build
```

Erzeugt den produktionsnahen Build für das Deployment.

## Preview (Production-Build lokal testen)

```bash
npm run preview
```

Startet eine lokale Vorschau des zuvor gebauten Artefakts (typisch auf Port `4173`).

## Umgebungsvariablen (`.env.example`)

Lege für lokale Läufe eine `.env` basierend auf `.env.example` an.

Aktuell sind folgende Variablen vorgesehen:

- `DATABASE_URL`  
  Beispiel: `mysql://root:mysecretpassword@localhost:3306/local`  
  Verbindungsstring für lokale DB-/Persistenzfunktionen.
- `AR_COMPACT` (`"true"`/`"false"`)  
  Schaltet kompakte UI-Darstellung um.
- `DEBUG_UI` (`"true"`/`"false"`)  
  Aktiviert/gatet Debug-bezogene UI-Elemente.

Hinweis: Defaultwerte und Beispielwerte stehen in `Software/Onboard_UI/.env.example`.

## Deployment-Referenz

Für das Zielsystem-Deployment (Pi Zero 2 W, Bullseye Lite) siehe:

- `docs/deploy/pi_zero2w_bullseye_lite.md`

## QA- und Launch-Kriterien

Für Launch-Bewertung und Freigabe sind insbesondere diese Dokumente maßgeblich:

- `docs/release/onboard_launch_visual_review_2026-04-12.md` (Visual-Review inkl. P0-Checks)
- `docs/release/onboard_design_signoff.md` (Sign-off-Entscheidung/Status)

Wichtige Leitplanke: Launch-Checks beziehen sich auf die vier freigegebenen Routen (`/`, `/Navigation`, `/Teleprompter`, `/Messages`) im definierten Zielprofil.
