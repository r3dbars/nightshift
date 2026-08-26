"""Readiness probes and doctor checks."""
from __future__ import annotations

import ipaddress
import json
import os
import platform
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from night_shift_paths import (
    BIN,
    CODEX_HOME,
    CONFIG_DIR,
    DEFAULT_LOCAL_MODEL,
    DEFAULT_LOCAL_URL,
    DEFAULT_WINDOWS_MODEL,
    OLLAMA_LOCAL_URL,
    OVERNIGHT_ROOT,
    cli_attr,
    cli_module,
    runtime_tool as _runtime_tool,
)
from night_shift_runtime import latest_ledger as _latest_ledger
from night_shift_runtime import repo_root as _repo_root
from night_shift_runtime import run_cmd as _default_run_cmd
from night_shift_sandbox import detect_sandbox
from night_shift_portfolio import parse_json_text


def run_cmd(*args, **kwargs):
    return cli_attr("run_cmd", _default_run_cmd)(*args, **kwargs)


def runtime_tool(name: str) -> Path:
    return cli_attr("runtime_tool", _runtime_tool)(name)


def latest_ledger(*args, **kwargs):
    return cli_attr("latest_ledger", _latest_ledger)(*args, **kwargs)


def repo_root(*args, **kwargs):
    return cli_attr("repo_root", _repo_root)(*args, **kwargs)


def load_repo_profile(repo):
    cli = cli_module()
    if cli is None:
        raise RuntimeError("night_shift_cli is not loaded")
    return cli.load_repo_profile(repo)


def read_url_json(url: str, headers=None, timeout=8):
    req = urllib.request.Request(url, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))

def post_url_json(url: str, payload: dict, headers=None, timeout=20):
    body = json.dumps(payload).encode("utf-8")
    merged_headers = {"Content-Type": "application/json"}
    merged_headers.update(headers or {})
    req = urllib.request.Request(url, data=body, headers=merged_headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8", errors="replace"))

def retry_transient(call, *args, **kwargs):
    """Retry one brief local-network interruption, but never HTTP or data errors."""
    sleeper = cli_attr("time", time)
    for attempt in range(2):
        try:
            return call(*args, **kwargs)
        except (urllib.error.URLError, TimeoutError, ConnectionResetError, BrokenPipeError) as exc:
            if isinstance(exc, urllib.error.HTTPError):
                raise
            if attempt:
                raise
            sleeper.sleep(0.25)

def model_ids(data: dict) -> list[str]:
    return [str(m.get("id")) for m in data.get("data", []) if m.get("id")]

def chat_probe(name: str, base_url: str, model: str, headers=None) -> tuple[str, str]:
    try:
        data = cli_attr("retry_transient", retry_transient)(
            cli_attr("post_url_json", post_url_json),
            f"{base_url.rstrip('/')}/chat/completions",
            {
                "model": model,
                "messages": [{"role": "user", "content": "Reply exactly: NIGHT_SHIFT_OK"}],
                # Reasoning models may need room before they emit visible text.
                "max_tokens": 1024,
                "temperature": 0,
            },
            headers=headers,
            timeout=30,
        )
        content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
        if "NIGHT_SHIFT_OK" in content:
            return "GREEN", f"{name} chat works with {model}"
        return "YELLOW", f"{name} chat replied, but not with the expected setup token"
    except Exception as exc:
        return "YELLOW", f"{name} lists models, but chat failed with {model}: {exc}"

def safe_remote_url(url: str) -> tuple[str, str]:
    if not url.strip():
        return "INFO", "no other-computer AI server configured"
    parsed = urllib.parse.urlparse(url)
    host = parsed.hostname or ""
    if parsed.scheme != "http":
        return "YELLOW", "use an http:// URL for OpenAI-compatible local servers"
    if host in {"localhost", "127.0.0.1", "::1"}:
        return "GREEN", "local URL"
    try:
        ip = ipaddress.ip_address(host)
        if ip.is_private:
            return "GREEN", "private LAN URL"
        return "YELLOW", "this does not look like a private LAN address; avoid sending repo context to public URLs"
    except ValueError:
        if host.endswith(".local") or "." not in host:
            return "GREEN", "local network host name"
    return "YELLOW", "could not confirm this is a local/private AI server"

def free_gb(path: Path) -> float:
    try:
        usage = shutil.disk_usage(path if path.exists() else path.parent)
        return round(usage.free / 1024**3, 1)
    except Exception:
        return 0.0

def check_storage_permissions() -> tuple[str, str]:
    home = cli_attr("CODEX_HOME", CODEX_HOME)
    targets = [
        cli_attr("CONFIG_DIR", CONFIG_DIR),
        cli_attr("OVERNIGHT_ROOT", OVERNIGHT_ROOT),
        home / "maestro" / "runs",
        home / "maestro-sidecar",
    ]
    try:
        for target in targets:
            target.mkdir(parents=True, exist_ok=True)
            probe = target / ".night-shift-write-test"
            probe.write_text("ok\n", encoding="utf-8")
            probe.unlink()
        return "GREEN", "Night Shift can write setup, ledgers, artifacts, and token logs"
    except Exception as exc:
        return "RED", f"cannot write Night Shift support files: {exc}"

def check_power() -> tuple[str, str]:
    if platform.system() != "Darwin" or not shutil.which("pmset"):
        return "INFO", "power check skipped on this platform"
    batt = run_cmd(["pmset", "-g", "batt"], timeout=10)
    text = (batt.stdout + batt.stderr).lower()
    if "ac power" in text:
        return "GREEN", "plugged in; power looks safe for overnight work"
    if "battery power" in text:
        return "YELLOW", "this Mac appears to be on battery; plug in before Normal or Afterburner"
    return "INFO", "could not determine battery/AC state"

def check_recovery() -> tuple[str, str]:
    latest = latest_ledger()
    if not latest:
        return "GREEN", "no previous Night Shift run found"
    if (latest / "morning.md").exists():
        return "GREEN", f"latest run has a morning brief: {latest.name}"
    if (latest / "processes.tsv").exists() and not (latest / "STOP").exists():
        return "YELLOW", f"unfinished run found: {latest}; run `night-shift stop --latest` or `night-shift report --latest`"
    return "INFO", f"latest run looks incomplete but inactive: {latest.name}"

def supports_os() -> tuple[str, str]:
    system = platform.system()
    py = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    if system in {"Darwin", "Linux"} and sys.version_info >= (3, 9):
        return "GREEN", f"{system} with Python {py}; supported"
    if sys.version_info < (3, 9):
        return "RED", f"Python {py} is too old; install Python 3.9 or newer"
    return "YELLOW", f"{system} detected; Night Shift is best tested on macOS/Linux shells"

def check_endpoint(name: str, url: str, headers=None) -> tuple[str, str]:
    try:
        data = retry_transient(read_url_json, url, headers=headers, timeout=8)
        models = model_ids(data)
        return "GREEN", f"{name} reachable; models={models[:8]}"
    except urllib.error.URLError as exc:
        return "YELLOW", f"{name} not reachable: {exc}"
    except Exception as exc:
        return "YELLOW", f"{name} returned unreadable response: {exc}"

def check_model_endpoint(name: str, url: str, expected_model: str | None = None, headers=None) -> tuple[str, str]:
    state, message = check_endpoint(name, url, headers=headers)
    if state != "GREEN" or not expected_model:
        return state, message
    try:
        data = retry_transient(read_url_json, url, headers=headers, timeout=8)
        models = model_ids(data)
    except Exception:
        return state, message
    if models and expected_model not in models:
        return "YELLOW", f"{name} reachable; expected model '{expected_model}' not listed; models={models[:8]}"
    return state, message

def local_server_label(base_url: str) -> str:
    if "11434" in base_url:
        return "Ollama"
    if "1234" in base_url:
        return "LM Studio"
    return "Local model server"

def pick_local_model(models: list[str]) -> str | None:
    chat_models = [m for m in models if not re.search(r"embed|bge-|rerank", m, re.IGNORECASE)]
    if not chat_models:
        return None
    for marker in ("coder", "instruct"):
        marked = [m for m in chat_models if marker in m.lower()]
        if marked:
            return marked[0]
    return chat_models[0]

def loaded_lm_studio_models() -> list[str]:
    if not shutil.which("lms"):
        return []
    result = run_cmd(["lms", "ps", "--json"], timeout=20)
    if result.rc != 0:
        return []
    rows = parse_json_text(result.stdout, [])
    return [row.get("identifier", "") for row in rows if row.get("type") == "llm" and row.get("identifier")]

def autodetect_local_server() -> tuple[str, str | None] | None:
    try:
        data = read_url_json(f"{OLLAMA_LOCAL_URL}/models", timeout=3)
    except Exception:
        return None
    return OLLAMA_LOCAL_URL, pick_local_model(model_ids(data))

def doctor_advice(rows: list[tuple[str, str, str]]) -> list[str]:
    by_name = {name: state for name, state, _ in rows}
    advice: list[str] = []
    if (
        by_name.get("night-shift") == "RED"
        or by_name.get("maestro-delegate") == "RED"
        or by_name.get("maestro-token-report") == "RED"
    ):
        advice.append("Install: from the cloned Night Shift repo, run `./install.sh`.")
    if by_name.get("local-models") == "YELLOW":
        advice.append(
            "Mac local: open LM Studio and start the local server, or start Ollama "
            "(`ollama serve`) with a chat model pulled. "
            "Then rerun doctor, or pass `--local-url` and `--local-model`."
        )
    if by_name.get("local-chat") == "YELLOW":
        advice.append("Mac local chat: the model is listed, but chat failed. Reload the model and rerun doctor.")
    if by_name.get("windows-worker") == "YELLOW" or by_name.get("windows-chat") == "YELLOW":
        advice.append(
            "Windows worker: optional. To use it, run "
            "`export WINDOWS_WORKER_BASE_URL=http://WINDOWS_HOST:11434/v1` and "
            "`export WINDOWS_WORKER_MODEL=qwen3-coder:30b`, or pass `--windows-url` and `--windows-model`."
        )
    if by_name.get("claude") == "INFO":
        advice.append("Claude: install and sign in to the `claude` CLI, or ignore this optional lane.")
    if by_name.get("gh") == "INFO" or by_name.get("gh-auth") in {"INFO", "YELLOW"}:
        advice.append("GitHub: install `gh` and run `gh auth login` if you want PR state in the context pack.")
    if by_name.get("repo") == "RED":
        advice.append("Repo: pass `--repo /path/to/a/git/repo`.")
    if by_name.get("local-models") == "YELLOW" and by_name.get("windows-worker") == "YELLOW":
        advice.append("No local models yet: run `night-shift plan --repo <repo>` for a no-model planning brief.")
    elif by_name.get("local-models") == "GREEN" and by_name.get("windows-worker") == "YELLOW":
        advice.append("Mac-only path: run `night-shift run --repo <repo> --mode quiet --max-windows 0`.")
    elif by_name.get("local-models") == "YELLOW" and by_name.get("windows-worker") == "GREEN":
        advice.append("Windows-only path: run `night-shift run --repo <repo> --mode quiet --max-local 0`.")
    elif by_name.get("local-models") == "GREEN" and by_name.get("windows-worker") == "GREEN":
        advice.append("Mac+Windows path: run `night-shift run --repo <repo> --mode night-shift`.")
    return advice

def doctor_checks(
    repo: str | None,
    run_smoke=False,
    allow_fetch=True,
    skip_local=False,
    skip_windows=False,
) -> tuple[str, list[tuple[str, str, str]]]:
    rows: list[tuple[str, str, str]] = []

    rows.append(("os-python", *supports_os()))
    rows.append(("storage", *cli_attr("check_storage_permissions", check_storage_permissions)()))
    home = cli_attr("CODEX_HOME", CODEX_HOME)
    free = free_gb(home)
    rows.append(("disk", "GREEN" if free >= 5 else "YELLOW", f"{free} GB free near {home}"))
    rows.append(("power", *check_power()))
    rows.append(("recovery", *check_recovery()))
    provider = cli_attr("detect_sandbox", detect_sandbox)(run_cmd)
    provider_state = "GREEN" if provider.available else "YELLOW" if provider.runtime else "INFO"
    rows.append(("sandbox-provider", provider_state, provider.detail))
    bin_dir = cli_attr("BIN", BIN)
    path_state = "GREEN" if str(bin_dir) in os.environ.get("PATH", "") else "INFO"
    rows.append(("path", path_state, f"{bin_dir} is {'on' if path_state == 'GREEN' else 'not on'} PATH"))

    for label, path in [
        ("night-shift", runtime_tool("night-shift")),
        ("maestro-delegate", runtime_tool("maestro-delegate")),
        ("maestro-token-report", runtime_tool("maestro-token-report")),
        ("maestro-smoke", runtime_tool("maestro-smoke.sh")),
    ]:
        if path.exists() and os.access(path, os.X_OK):
            rows.append((label, "GREEN", str(path)))
        else:
            rows.append((label, "RED", f"missing or not executable: {path}"))

    for label, command in [("git", "git"), ("gh", "gh")]:
        found = shutil.which(command)
        state = "GREEN" if found else ("RED" if command == "git" else "INFO")
        rows.append((label, state, found or f"{command} not found"))

    claude = shutil.which("claude")
    rows.append(("claude", "GREEN" if claude else "INFO", claude or "claude CLI not found; optional"))

    if shutil.which("gh"):
        gh_auth = run_cmd(["gh", "auth", "status"], timeout=30)
        rows.append(("gh-auth", "GREEN" if gh_auth.rc == 0 else "INFO", (gh_auth.stderr or gh_auth.stdout).strip() or "GitHub auth optional"))

    if skip_local:
        rows.append(("local-models", "SKIPPED", "disabled by --no-local"))
        rows.append(("local-chat", "SKIPPED", "disabled by --no-local"))
    else:
        local_base = os.environ.get("MAESTRO_LOCAL_BASE_URL", DEFAULT_LOCAL_URL)
        local_model = os.environ.get("MAESTRO_LOCAL_MODEL", DEFAULT_LOCAL_MODEL)
        local_label = local_server_label(local_base)
        local_status, local_msg = check_model_endpoint(local_label, f"{local_base.rstrip('/')}/models", expected_model=local_model)
        if local_status != "GREEN" and "MAESTRO_LOCAL_BASE_URL" not in os.environ:
            fallback = autodetect_local_server()
            if fallback:
                local_base, detected_model = fallback
                local_label = local_server_label(local_base)
                if "MAESTRO_LOCAL_MODEL" not in os.environ and detected_model:
                    local_model = detected_model
                os.environ["MAESTRO_LOCAL_BASE_URL"] = local_base
                os.environ["MAESTRO_LOCAL_MODEL"] = local_model
                local_status, local_msg = check_model_endpoint(local_label, f"{local_base.rstrip('/')}/models", expected_model=local_model)
                local_msg = f"auto-detected {local_label}; {local_msg}"
        rows.append(("local-models", local_status, local_msg))
        if local_status == "GREEN":
            chat_state, chat_message = chat_probe(local_label, local_base, local_model)
            if chat_state != "GREEN" and "1234" in local_base:
                for loaded_model in loaded_lm_studio_models():
                    fallback_state, fallback_message = chat_probe(local_label, local_base, loaded_model)
                    if fallback_state == "GREEN":
                        local_model = loaded_model
                        os.environ["MAESTRO_LOCAL_MODEL"] = loaded_model
                        chat_state = fallback_state
                        chat_message = f"auto-selected loaded model; {fallback_message}"
                        break
            rows.append(("local-chat", chat_state, chat_message))

    if skip_windows:
        rows.append(("windows-worker", "SKIPPED", "disabled by --no-windows"))
        rows.append(("windows-chat", "SKIPPED", "disabled by --no-windows"))
    else:
        base = os.environ.get("WINDOWS_WORKER_BASE_URL", "").strip()
        key = os.environ.get("WINDOWS_WORKER_API_KEY", "ollama")
        windows_model = os.environ.get("WINDOWS_WORKER_MODEL", DEFAULT_WINDOWS_MODEL)
        if base:
            rows.append(("windows-url", *safe_remote_url(base)))
            win_status, win_msg = check_model_endpoint(
                "Windows worker",
                f"{base.rstrip('/')}/models",
                expected_model=windows_model,
                headers={"Authorization": f"Bearer {key}"},
            )
            rows.append(("windows-worker", win_status, win_msg))
            if win_status == "GREEN":
                rows.append(("windows-chat", *chat_probe("Windows worker", base, windows_model, headers={"Authorization": f"Bearer {key}"})))
        else:
            rows.append(("windows-worker", "INFO", "not configured; this is fine for Mac-only setup"))

    root = repo_root(repo)
    if repo:
        if root and root.exists():
            rev = run_cmd(["git", "-C", root, "rev-parse", "--short", "HEAD"], timeout=20)
            status = run_cmd(["git", "-C", root, "status", "--short"], timeout=20)
            branch = run_cmd(["git", "-C", root, "branch", "--show-current"], timeout=20)
            remote = run_cmd(["git", "-C", root, "remote", "get-url", "origin"], timeout=20)
            dirty = status.stdout.strip() != ""
            repo_state = "clean" if not dirty else f"dirty lines={len(status.stdout.splitlines())}; Night Shift will not edit this checkout"
            state = "YELLOW" if dirty else ("GREEN" if rev.rc == 0 else "RED")
            rows.append(("repo", state, f"{root} branch={branch.stdout.strip() or '(detached)'} head={rev.stdout.strip()} {repo_state}"))
            rows.append(("repo-remote", "GREEN" if remote.rc == 0 else "INFO", remote.stdout.strip() or "no origin remote configured"))
            if allow_fetch:
                if remote.rc == 0:
                    fetch = run_cmd(["git", "-C", root, "fetch", "origin", "--prune"], timeout=90)
                    rows.append(("repo-fetch", "GREEN" if fetch.rc == 0 else "YELLOW", fetch.stderr.strip() or fetch.stdout.strip() or "ok"))
                else:
                    rows.append(("repo-fetch", "INFO", "skipped because no origin remote is configured"))
            else:
                rows.append(("repo-fetch", "SKIPPED", "run command does not mutate repo refs; use doctor for fetch check"))
        else:
            rows.append(("repo", "RED", f"repo path missing: {root}"))
    if root and root.exists():
        profile, detail = load_repo_profile(root)
        if not profile:
            rows.append(("repo-profile", "INFO", detail))
            rows.append(("sandbox", "INFO", "analysis-only until a reviewed repo profile exists"))
        elif not profile.may_execute:
            rows.append(("repo-profile", "YELLOW", "profile loaded but trust, image, or execution setting prevents patch execution"))
            rows.append(("sandbox", "INFO", "analysis-only by repo-profile policy"))
        else:
            rows.append(("repo-profile", "GREEN", "owned repo with explicit sandbox execution profile"))
            rows.append(("sandbox", "GREEN" if provider.available else "YELLOW", provider.detail))

    if run_smoke:
        smoke = run_cmd([runtime_tool("maestro-smoke.sh")], timeout=180)
        state = "GREEN" if smoke.rc == 0 else "YELLOW"
        msg = (smoke.stdout + smoke.stderr).strip().replace("\n", " | ")
        rows.append(("lane-smoke", state, msg[:1200]))

    meaningful = [state for _, state, _ in rows if state not in {"INFO", "SKIPPED"}]
    if any(state == "RED" for state in meaningful):
        overall = "RED"
    elif any(state == "YELLOW" for state in meaningful):
        overall = "YELLOW"
    else:
        overall = "GREEN"
    return overall, rows

