from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "Software" / "Backend"


@dataclass
class TestResult:
    name: str
    passed: bool
    reason: str = ""
    details: dict[str, Any] | None = None


class BackendServer:
    def __init__(self) -> None:
        self.external_base_url = os.environ.get("QA_BACKEND_BASE_URL")
        self.port = self._find_open_port() if self.external_base_url is None else None
        self.base_url = self.external_base_url or f"http://127.0.0.1:{self.port}"
        self.db_path = REPO_ROOT / "Software" / "QA" / "reports" / f"qa_backend_{self.port}.db"
        self.proc: subprocess.Popen[str] | None = None
        self.auth_token: str | None = None
        self.default_headers: dict[str, str] = {}

    def __enter__(self) -> "BackendServer":
        if self.external_base_url:
            self._wait_until_ready(timeout=20)
            return self

        env = os.environ.copy()
        env.update(
            {
                "HOST": "127.0.0.1",
                "PORT": str(self.port),
                "DB_PATH": str(self.db_path),
                "PYTHONUNBUFFERED": "1",
            }
        )
        self.proc = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd=BACKEND_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        self._wait_until_ready(timeout=20)
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self.external_base_url:
            return
        if self.proc is None:
            return
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait(timeout=5)

    @staticmethod
    def _find_open_port() -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))
            return int(s.getsockname()[1])

    def _wait_until_ready(self, timeout: int = 20) -> None:
        deadline = time.time() + timeout
        last_error = "service not started"
        while time.time() < deadline:
            if self.proc is not None and self.proc.poll() is not None:
                startup_logs = self.proc.stdout.read() if self.proc.stdout else ""
                raise RuntimeError(f"Backend exited early: {startup_logs.strip()}")
            try:
                response = request_json(self.base_url, "GET", "/api/status")
                if response["status"] == 200:
                    return
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
            time.sleep(0.2)
        raise RuntimeError(f"Backend did not become ready: {last_error}")

    def bootstrap_auth(self, device_id: str = "qa-harness", device_name: str = "QA Harness") -> str:
        start_response = request_json(
            self.base_url,
            "POST",
            "/api/auth/pairing/start",
            payload={"device_id": device_id, "device_name": device_name},
        )
        if start_response["status"] != 201:
            raise RuntimeError(f"pairing/start failed with status {start_response['status']}")

        pairing_code = start_response["json"].get("data", {}).get("pairing_code")
        if not pairing_code:
            raise RuntimeError("pairing/start response did not include pairing_code")

        exchange_response = request_json(
            self.base_url,
            "POST",
            "/api/auth/pairing/exchange",
            payload={"device_id": device_id, "pairing_code": pairing_code},
        )
        if exchange_response["status"] != 201:
            raise RuntimeError(f"pairing/exchange failed with status {exchange_response['status']}")

        token = exchange_response["json"].get("data", {}).get("access_token")
        if not token:
            raise RuntimeError("pairing/exchange response did not include access_token")

        self.auth_token = token
        self.default_headers = {"Authorization": f"Bearer {token}"}
        return token


def request_json(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    default_headers: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    url = urllib.parse.urljoin(base_url, path)
    body = None
    request_headers = {"Content-Type": "application/json"}
    if default_headers:
        request_headers.update(default_headers)
    if headers:
        request_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url=url, data=body, headers=request_headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8")
            return {
                "status": response.status,
                "json": json.loads(raw) if raw else {},
            }
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8")
        parsed = json.loads(raw) if raw else {}
        return {"status": exc.code, "json": parsed}


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)
