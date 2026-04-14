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
  xserver-xorg xinit openbox chromium-browser unclutter curl git \
  ca-certificates fonts-dejavu
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
git clone <YOUR_REPO_URL> /home/admin/aris
cd /home/admin/aris/Software/Onboard_UI
npm ci
npm run build

cd /home/admin/aris/Software/Backend
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

## 6. Verification

Run these checks:

```bash
curl -s http://127.0.0.1:5000/api/status
curl -sI http://127.0.0.1:4173
systemctl status aris-backend aris-ui aris-kiosk --no-pager
```

## 7. Troubleshooting

- **Blank screen / no X**
  - Check X packages were installed (`xserver-xorg`, `xinit`, `openbox`).
  - Review kiosk/UI logs: `journalctl -u aris-kiosk -u aris-ui -b --no-pager`.
- **Chromium crash loop**
  - Verify `chromium-browser` is installed and launch flags are correct in kiosk startup/service scripts.
  - Confirm enough free memory/storage (`free -h`, `df -h`).
- **Backend down**
  - Check backend logs: `journalctl -u aris-backend -b --no-pager`.
  - Verify Python virtualenv and dependencies are installed in `/home/admin/aris/Software/Backend`.
- **AV mode mismatch**
  - Re-check `/boot/config.txt` values (`enable_tvout=1`, `sdtv_mode=2`) and reboot.
