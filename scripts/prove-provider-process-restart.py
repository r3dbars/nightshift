#!/usr/bin/env python3
"""Prove truthful offline state and recovery after a provider process restart."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("night_shift_provider_restart", str(ROOT / "bin" / "night-shift"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
CLI = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = CLI
LOADER.exec_module(CLI)

SERVER = r'''
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = json.dumps({"data": [{"id": "fixture-coder"}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args):
        return

HTTPServer(("127.0.0.1", int(sys.argv[1])), Handler).serve_forever()
'''


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def start_provider(port: int) -> subprocess.Popen[str]:
    return subprocess.Popen(
        [sys.executable, "-u", "-c", SERVER, str(port)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def wait_for_state(url: str, expected: str, timeout: float = 8.0) -> tuple[str, str]:
    deadline = time.monotonic() + timeout
    last = ("YELLOW", "provider not ready")
    while time.monotonic() < deadline:
        last = CLI.check_endpoint("fixture provider", url)
        if last[0] == expected:
            return last
        time.sleep(0.1)
    return last


def main() -> int:
    port = free_port()
    url = f"http://127.0.0.1:{port}/models"
    provider = start_provider(port)
    restarted = None
    try:
        initial = wait_for_state(url, "GREEN")
        if initial[0] != "GREEN":
            raise SystemExit(f"provider did not start: {initial}")

        provider.terminate()
        provider.wait(timeout=5)
        offline = CLI.check_endpoint("fixture provider", url)
        if offline[0] != "YELLOW" or "not reachable" not in offline[1]:
            raise SystemExit(f"offline provider was not reported honestly: {offline}")

        restarted = start_provider(port)
        recovered = wait_for_state(url, "GREEN")
        if recovered[0] != "GREEN":
            raise SystemExit(f"provider did not recover after restart: {recovered}")
    finally:
        for process in (restarted, provider):
            if process and process.poll() is None:
                process.terminate()
                process.wait(timeout=5)

    print("PROVIDER_RESTART_PROOF: GREEN | startup=GREEN offline=YELLOW restart=GREEN same-port=1")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
