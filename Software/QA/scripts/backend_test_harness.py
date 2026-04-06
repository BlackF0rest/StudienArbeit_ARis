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
BACKEND_DIR = REPO_ROOT / "Software" / "Backend_Prototype"


@dataclass
class TestResult:
    name: str
    passed: bool
    reason: str = ""
    details: dict[str, Any] | None = None


class BackendServer:
    def __init__(self) -> None:
        self.port = self._find_open_port()
        self.base_url = f"http://127.0.0.1:{self.port}"
        self.db_path = REPO_ROOT / "Software" / "QA" / "reports" / f"qa_backend_{self.port}.db"
        self.proc: subprocess.Popen[str] | None = None

    def __enter__(self) -> "BackendServer":
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


def request_json(base_url: str, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    url = urllib.parse.urljoin(base_url, path)
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")

    request = urllib.request.Request(url=url, data=body, headers=headers, method=method)
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
