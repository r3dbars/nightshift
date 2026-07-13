#!/usr/bin/env python3
"""Prove worker wrappers fail closed on offline and malformed responses."""

from __future__ import annotations

import os
import subprocess
import tempfile
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread


ROOT = Path(__file__).resolve().parents[1]


class MalformedHandler(BaseHTTPRequestHandler):
    authorization = ""

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        length = int(self.headers.get("Content-Length", "0"))
        self.rfile.read(length)
        type(self).authorization = self.headers.get("Authorization", "")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"choices": []}')

    def log_message(self, *_args) -> None:
        return


def run_wrapper(command: list[str], environment: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        timeout=30,
    )


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="night-shift-wrapper-proof-") as tmp:
        env = os.environ.copy()
        env.update({"HOME": tmp, "CODEX_HOME": str(Path(tmp) / ".codex")})

        offline = run_wrapper(
            [str(ROOT / "bin" / "maestro-local"), "offline-check"],
            {**env, "MAESTRO_LOCAL_BASE_URL": "http://127.0.0.1:9/v1"},
        )
        if offline.returncode != 1 or "leave this task untouched" not in offline.stderr:
            raise SystemExit("local wrapper did not fail cleanly when offline")

        server = HTTPServer(("127.0.0.1", 0), MalformedHandler)
        Thread(target=server.serve_forever, daemon=True).start()
        try:
            base = f"http://127.0.0.1:{server.server_port}/v1"
            malformed_local = run_wrapper(
                [str(ROOT / "bin" / "maestro-local"), "malformed-check"],
                {**env, "MAESTRO_LOCAL_BASE_URL": base},
            )
            malformed_windows = run_wrapper(
                [str(ROOT / "bin" / "maestro-windows"), "malformed-check"],
                {
                    **env,
                    "WINDOWS_WORKER_BASE_URL": base,
                    "WINDOWS_WORKER_API_KEY": "wrapper-proof-key",
                },
            )
            windows_authorization = MalformedHandler.authorization
            custom_home = Path(tmp) / "custom-codex-home"
            subprocess.run(
                [str(ROOT / "install.sh"), "--codex-home", str(custom_home), "--no-path"],
                cwd=ROOT,
                env={**env, "SHELL": "/bin/bash"},
                check=True,
                capture_output=True,
                text=True,
            )
            custom_home_delegate = run_wrapper(
                [str(custom_home / "bin" / "maestro-delegate"), "local", "--label", "custom-home", "--", "malformed-check"],
                {
                    **env,
                    "CODEX_HOME": str(custom_home),
                    "MAESTRO_LOCAL_BASE_URL": base,
                },
            )
        finally:
            server.shutdown()

        for name, result in (("local", malformed_local), ("Windows", malformed_windows)):
            if result.returncode != 1 or "no usable chat content" not in result.stderr:
                raise SystemExit(f"{name} wrapper did not reject malformed chat JSON")
        if windows_authorization != "Bearer wrapper-proof-key":
            raise SystemExit("Windows wrapper did not preserve its authorization header")
        if custom_home_delegate.returncode != 1 or "MAESTRO_PROOF=" not in custom_home_delegate.stderr:
            raise SystemExit("maestro-delegate did not honor CODEX_HOME when HOME differed")
        if not list((custom_home / "maestro" / "runs").glob("*-custom-home-local")):
            raise SystemExit("maestro-delegate did not write its proof under CODEX_HOME")

    print("WORKER_WRAPPER_ERROR_PROOF: GREEN | offline, malformed, and custom CODEX_HOME paths fail closed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
