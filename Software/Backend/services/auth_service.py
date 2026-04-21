from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from repositories.sqlite_repo import SQLiteRepository


class AuthService:
    def __init__(
        self,
        repo: SQLiteRepository,
        pairing_ttl_seconds: int = 300,
        token_ttl_days: int = 30,
    ):
        self.repo = repo
        self.pairing_ttl_seconds = pairing_ttl_seconds
        self.token_ttl_days = token_ttl_days

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @staticmethod
    def _hash_secret(secret: str, salt: str) -> str:
        payload = f"{salt}:{secret}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def start_pairing(self, device_id: str, device_name: str | None = None) -> dict:
        code = f"{secrets.randbelow(1_000_000):06d}"
        salt = secrets.token_hex(16)
        code_hash = self._hash_secret(code, salt)
        expires_at = self._utc_now() + timedelta(seconds=self.pairing_ttl_seconds)

        session_id = self.repo.create_pairing_session(
            device_id=device_id,
            device_name=device_name,
            code_hash=code_hash,
            code_salt=salt,
            expires_at=expires_at,
        )

        return {
            "session_id": session_id,
            "pairing_code": code,
            "expires_at": expires_at.isoformat(),
            "device_id": device_id,
        }

    def exchange_pairing_code(self, device_id: str, pairing_code: str) -> tuple[dict | None, dict | None]:
        record = self.repo.get_latest_open_pairing_session(device_id)
        if not record:
            return None, {"code": "pairing_not_found", "message": "No active pairing request"}

        now = self._utc_now()
        if datetime.fromisoformat(record["expires_at"]) < now:
            self.repo.close_pairing_session(record["id"], "expired")
            return None, {"code": "pairing_expired", "message": "Pairing code has expired"}

        expected_hash = self._hash_secret(pairing_code, record["code_salt"])
        if not hmac.compare_digest(expected_hash, record["code_hash"]):
            return None, {"code": "pairing_invalid", "message": "Pairing code is invalid"}

        self.repo.close_pairing_session(record["id"], "used")

        token_plain = secrets.token_urlsafe(32)
        token_salt = secrets.token_hex(16)
        token_hash = self._hash_secret(token_plain, token_salt)
        token_id = str(uuid.uuid4())
        expires_at = now + timedelta(days=self.token_ttl_days)

        # Gerätewechsel => alte Device-Sessions invalidieren
        self.repo.revoke_tokens_for_other_devices(device_id=device_id)
        self.repo.store_auth_token(
            token_id=token_id,
            device_id=device_id,
            token_plain=token_plain,
            token_hash=token_hash,
            token_salt=token_salt,
            expires_at=expires_at,
        )

        return {
            "access_token": token_plain,
            "token_type": "Bearer",
            "expires_at": expires_at.isoformat(),
            "device_id": device_id,
        }, None

    def validate_token(self, raw_token: str) -> dict | None:
        token_prefix = raw_token[:10]
        candidates = self.repo.get_active_tokens_by_prefix(token_prefix)
        now = self._utc_now()

        for record in candidates:
            expected_hash = self._hash_secret(raw_token, record["token_salt"])
            if not hmac.compare_digest(expected_hash, record["token_hash"]):
                continue

            if datetime.fromisoformat(record["expires_at"]) < now:
                self.repo.revoke_token(record["token_id"], reason="expired")
                return None

            return record

        return None

    def revoke_token(self, raw_token: str) -> bool:
        token = self.validate_token(raw_token)
        if not token:
            return False
        self.repo.revoke_token(token["token_id"], reason="manual")
        return True
