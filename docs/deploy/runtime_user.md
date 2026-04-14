# Runtime + Build User

Für Runtime und Build ist **genau ein Zieluser** festgelegt:

- `admin`

## Verifikation auf dem Zielsystem

Diese Checks müssen auf dem Raspberry Pi erfolgreich sein:

```bash
getent passwd admin
id admin
```

## Hinweis zu alten `pi`-Setups

- Wenn der User `pi` nicht existiert, dürfen systemd Units **nicht** `User=pi` enthalten.
- In diesem Repository sind die Deploy-Units auf `User=admin` umgestellt.
