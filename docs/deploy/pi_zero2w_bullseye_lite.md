# Raspberry Pi Zero 2 W (Bullseye Lite) Deployment

This guide describes how to deploy ARIS on a Raspberry Pi Zero 2 W using Raspberry Pi OS Bullseye Lite.

## 1. Base OS prep

1. Flash **Raspberry Pi OS Bullseye Lite** to your microSD card.
2. Perform first-boot configuration:
   - Enable SSH.
   - Configure locale.
   - Configure timezone.
   - Configure Wi-Fi.
3. *(Optional, composite video / AV-out)* Enable TV-out by adding the following lines in `/boot/config.txt`:

```ini
enable_tvout=1
sdtv_mode=2
```

## 2. System packages

Install required system packages:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv sqlite3 \
  xserver-xorg xinit openbox unclutter curl git \
  ca-certificates fonts-dejavu flatpak
```

## 3. Node install (Pi-friendly)

Install Node.js 20 from NodeSource:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
node -v && npm -v
```

## 4. Clone and install project

Clone the repository and install UI/backend dependencies (single deploy user: `admin`):

```bash
git clone <YOUR_REPO_URL> /home/admin/Studienarbeit_ARis
cd /home/admin/Studienarbeit_ARis/Software/Onboard_UI
npm ci
npm run build

cd /home/admin/Studienarbeit_ARis/Software/Backend
python3 -m venv .venv
source .venv/bin/activate
pip install flask flask-cors
```

## 5. Install and enable services

1. Copy service files:
   - `aris-backend.service`
   - `aris-ui.service`
   - `aris-kiosk.service`
2. Reload systemd and enable/start services:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now aris-backend aris-ui aris-kiosk
```

## Automated deployment scripts

From the repository root, run:

```bash
bash Software/deploy/pi/install_pi.sh
bash Software/deploy/pi/update_onboard.sh
```

Notes:
- `install_pi.sh` is safe to re-run: it reuses existing Node/Python environments and only overwrites systemd service files when contents changed.
- `update_onboard.sh` performs a fast-forward-only `git pull`, rebuilds `Software/Onboard_UI`, and restarts `aris-backend`, `aris-ui`, and `aris-kiosk`.


### Midori-only deployment

The kiosk launcher (`Software/deploy/pi/kiosk/start_onboard.sh`) is intentionally **Midori-only**.
It no longer supports runtime browser switching via `ARIS_KIOSK_BROWSER`.

Startup order is fixed:

1. Flatpak: `org.midori_browser.Midori` (if installed)
2. Native binary: `midori` or `midori-browser`

If Midori is not available, startup fails with `exit 1` (no fallback to Chromium/Cog/other browsers).

> **Known limitation:** Chromium/Cog are not reliable on the target hardware and are therefore intentionally disabled.

The launcher also applies display rotation on startup via `xrandr`. By default it uses a 180° rotation (`ARIS_DISPLAY_ROTATION=inverted`).

To configure rotation without editing tracked service files, create a systemd override:

```bash
sudo systemctl edit aris-kiosk.service
```

Add:

```ini
[Service]
Environment=ARIS_DISPLAY_ROTATION=inverted
```

Then reload + restart:

```bash
sudo systemctl daemon-reload
sudo systemctl restart aris-kiosk.service
```

Install Midori before enabling kiosk startup.

### Midori install matrix (eindeutig)

| Fall | Verfügbarkeit | Was tun | Laufzeitpfad in `start_onboard.sh` |
| --- | --- | --- | --- |
| **A** | Native Midori-Paket vorhanden (`apt install midori` funktioniert) | `sudo apt install -y midori` | Native Binary (`midori` oder `midori-browser`) |
| **B** | Native Midori-Paket **nicht** vorhanden (`Unable to locate package midori`) | `flatpak install -y flathub org.midori_browser.Midori` | Flatpak-App `org.midori_browser.Midori` |

> Hinweis: `start_onboard.sh` prüft zuerst Flatpak Midori und startet danach (falls Flatpak nicht verfügbar ist) die native Midori-Binary.

Verify Midori availability with:

```bash
command -v midori || command -v midori-browser || true
flatpak info org.midori_browser.Midori || true
```

Interpretation für den Startpfad:
- Wenn `flatpak info org.midori_browser.Midori` erfolgreich ist, nutzt `start_onboard.sh` den Flatpak-Start (`flatpak run org.midori_browser.Midori`).
- Wenn Flatpak Midori nicht verfügbar ist, aber `command -v midori` oder `command -v midori-browser` erfolgreich ist, wird die native Binary genutzt.
- Wenn beides fehlschlägt, beendet sich `start_onboard.sh` mit Fehler (`exit 1`).

To disable rotation, set:

```ini
[Service]
Environment=ARIS_DISPLAY_ROTATION=normal
```


### Fallback: kiosk startup via `~/.bash_profile` (tty1)

If `aris-kiosk.service` cannot be used on your device, you can start ARIS kiosk from the login shell on `tty1`.
Use the tracked template file:

- `Software/deploy/pi/kiosk/bash_profile.kiosk.example`

Install it for user `admin`:

```bash
cp Software/deploy/pi/kiosk/bash_profile.kiosk.example /home/admin/.bash_profile
chown admin:admin /home/admin/.bash_profile
```

Important notes:
- This fallback depends on local login on `/dev/tty1` and **must not** run in parallel with an enabled `aris-kiosk.service`.
- The template already exports the required variables (`ARIS_FRONTEND_URL`, `ARIS_BACKEND_URL`, `ARIS_DISPLAY_ROTATION`, `XAUTHORITY`) before calling `start_onboard.sh`.
- `start_onboard.sh` also supports overriding these values via environment variables, so you can tune behavior without changing the script.

## 6. Verification

Run these checks:

```bash
curl -s http://127.0.0.1:5000/api/status
curl -sI http://127.0.0.1:4173
systemctl status aris-backend aris-ui aris-kiosk --no-pager
systemctl cat aris-backend aris-ui aris-kiosk
systemctl cat aris-backend aris-ui aris-kiosk | grep -F "/home/admin/Studienarbeit_ARis"
```

Ensure there are no references to alternative project roots (for example `/home/admin/aris` or `/home/admin/StudienArbeit_ARis`) in the `systemctl cat` output.

## 7. Troubleshooting

- **Blank screen / no X**
  - Check X packages were installed (`xserver-xorg`, `xinit`, `openbox`).
  - Review kiosk/UI logs: `journalctl -u aris-kiosk -u aris-ui -b --no-pager`.
- **Midori not found / kiosk exits immediately**
  - Verify either Flatpak Midori (`flatpak info org.midori_browser.Midori`) or native Midori (`command -v midori` / `command -v midori-browser`) is available.
  - Reinstall Midori and restart the service: `sudo systemctl restart aris-kiosk`.
- **Backend down**
  - Check backend logs: `journalctl -u aris-backend -b --no-pager`.
  - Verify Python virtualenv and dependencies are installed in `/home/admin/Studienarbeit_ARis/Software/Backend`.
- **AV mode mismatch**
  - Re-check `/boot/config.txt` values (`enable_tvout=1`, `sdtv_mode=2`) and reboot.
