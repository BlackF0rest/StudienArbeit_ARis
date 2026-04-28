# Minimal HUD (SvelteKit)

This project is configured for **static export** via `@sveltejs/adapter-static`.
The production build is written to the `build/` directory and can be copied to a Raspberry Pi without running `npm run build` on the Pi.

## Local development

```sh
npm install
npm run dev
```

## Production build (Windows dev machine)

```powershell
npm ci
npm run build
```

After build, verify `build/index.html` exists.

## Package build artifact (Windows PowerShell)

```powershell
cd C:\Projects\StudienArbeit_ARis\Software\Onboard_UI
tar -czf onboard-ui-build.tar.gz -C . build
```

## Deploy on Raspberry Pi (via Tabby SSH)

Copy artifact from Windows to Pi:

```powershell
scp .\onboard-ui-build.tar.gz admin@raspberrypi:/opt/aris-ui/releases/onboard-ui-build.tar.gz
```

Activate on Pi:

```bash
sudo mkdir -p /opt/aris-ui/releases /opt/aris-ui/current
sudo chown -R admin:admin /opt/aris-ui
rm -rf /opt/aris-ui/current/*
tar -xzf /opt/aris-ui/releases/onboard-ui-build.tar.gz -C /opt/aris-ui
cp -a /opt/aris-ui/build/. /opt/aris-ui/current/
sudo systemctl restart aris-ui.service
sudo systemctl status aris-ui.service --no-pager
```

## `aris-ui.service` (static hosting)

Use a static web server instead of `npm run preview`:

```ini
[Unit]
Description=ARIS UI (static)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=admin
WorkingDirectory=/opt/aris-ui/current
ExecStart=/usr/bin/python3 -m http.server 4173 --bind 127.0.0.1 --directory /opt/aris-ui/current
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
```
