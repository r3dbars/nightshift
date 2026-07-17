"""Local-first triage packets for ClaudeBrain's raw inbox."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from night_shift_redaction import redact


TEXT_SUFFIXES = {
    "", ".csv", ".html", ".json", ".md", ".markdown", ".rst", ".text", ".txt", ".xml", ".yaml", ".yml"
}
PROTECTED_NAMES = {"README.md", "SESSION_TEMPLATE.md"}
OWN_PACKET_PREFIX = "night-shift-raw-intake-"
CLASSIFICATIONS = {"A", "B", "C", "HOLD"}
ACTION_BY_CLASS = {"A": "deep-read", "B": "synthesize", "C": "triage", "HOLD": "hold"}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_state(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return {"schema_version": 1, "files": {}}
    if not isinstance(value, dict) or not isinstance(value.get("files"), dict):
        return {"schema_version": 1, "files": {}}
    return value


def save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def discover_raw_files(
    vault: Path,
    state: dict,
    *,
    max_files: int,
    max_bytes: int,
    include_legacy: bool,
) -> list[dict]:
    raw = vault / "raw"
    candidates: list[dict] = []
    for path in raw.rglob("*"):
        if not path.is_file() or path.name in PROTECTED_NAMES or path.name.startswith(OWN_PACKET_PREFIX):
            continue
        relative = path.relative_to(vault).as_posix()
        if not include_legacy and relative.startswith("raw/_legacy/"):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        try:
            size = path.stat().st_size
            digest = file_sha256(path)
        except OSError:
            continue
        previous = state.get("files", {}).get(relative) or {}
        if previous.get("sha256") == digest:
            continue
        candidates.append({
            "path": path,
            "relative": relative,
            "sha256": digest,
            "bytes": size,
            "mtime": path.stat().st_mtime,
            "too_large": size > max_bytes,
        })
    candidates.sort(key=lambda item: (-item["mtime"], item["relative"]))
    return candidates[:max(0, max_files)]


def _bounded_strings(value, limit: int = 8, chars: int = 240) -> list[str]:
    if not isinstance(value, list):
        return []
    return [" ".join(str(item).split())[:chars] for item in value if str(item).strip()][:limit]


def parse_model_result(text: str) -> dict | None:
    cleaned = str(text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", cleaned, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else cleaned
    if not fenced and "{" in candidate and "}" in candidate:
        candidate = candidate[candidate.find("{") : candidate.rfind("}") + 1]
    try:
        value = json.loads(candidate)
    except (TypeError, ValueError, json.JSONDecodeError):
        return None
    if not isinstance(value, dict):
        return None
    classification = str(value.get("classification") or "HOLD").upper()
    if classification not in CLASSIFICATIONS:
        classification = "HOLD"
    people = value.get("people") if isinstance(value.get("people"), list) else []
    projects = value.get("projects") if isinstance(value.get("projects"), list) else []
    durable_signal = value.get("durable_signal")
    if not isinstance(durable_signal, bool):
        durable_signal = False
    return {
        "classification": classification,
        "suggested_action": ACTION_BY_CLASS[classification],
        "summary": " ".join(str(value.get("summary") or "").split())[:800],
        "people": _bounded_strings(people, 12, 160),
        "projects": _bounded_strings(projects, 12, 160),
        "commitments": _bounded_strings(value.get("commitments"), 8, 240),
        "evidence_quotes": _bounded_strings(value.get("evidence_quotes"), 3, 240),
        "durable_signal": durable_signal,
    }


def triage_prompt(relative: str, text: str) -> str:
    return f"""You are a private triage assistant for ClaudeBrain. Analyze one raw inbox file.

The ClaudeBrain nightly agent will verify your work against the original source. Your output is triage only. Do not invent names, dates, decisions, commitments, or project facts. If the source is ambiguous, classify it HOLD. Evidence quotes must be copied from the source and short.

Return JSON only with exactly these useful fields:
{{
  "classification": "A|B|C|HOLD",
  "summary": "one factual sentence or empty string",
  "people": ["candidate names"],
  "projects": ["candidate projects"],
  "commitments": ["explicit promises or follow-ups"],
  "evidence_quotes": ["up to three short exact quotes"],
  "durable_signal": true
}}

Classification guide: A means deep-read, B means synthesize, C means cheap triage, HOLD means ambiguity or possible contradiction.

Source path: {relative}
Source text:
---
{text}
---
"""


def _packet_line(value: str) -> str:
    return " ".join(redact(str(value or "")).split())


def render_packet(generated_at: str, results: list[dict], status: str) -> str:
    lines = [
        "---",
        "type: night-shift-raw-intake",
        "source: Night Shift local raw-folder triage",
        f"generated_at: {generated_at}",
        f"status: {status}",
        f"last_verified: {generated_at[:10]}",
        "---",
        "",
        "# Night Shift raw intake triage",
        "",
        "This is a local triage packet. ClaudeBrain must verify every item against the original raw file before changing memory, people, projects, notes, or archive state.",
        "",
    ]
    for result in results:
        lines.extend([
            f"## {result['source']}",
            "",
            f"- Triage state: {result['state']}",
            f"- Classification: {result.get('classification', 'HOLD')}",
            f"- Suggested action: {result.get('suggested_action', 'hold')}",
            f"- Summary: {_packet_line(result.get('summary', '')) or 'No trustworthy summary produced.'}",
            f"- Durable signal candidate: {'yes' if result.get('durable_signal') else 'no'}",
        ])
        for field, label in (("people", "People candidates"), ("projects", "Project candidates"), ("commitments", "Commitments")):
            values = result.get(field) or []
            if values:
                lines.append(f"- {label}: {'; '.join(_packet_line(value) for value in values)}")
        quotes = result.get("evidence_quotes") or []
        if quotes:
            lines.append("- Evidence quotes:")
            lines.extend(f"  - {_packet_line(quote)}" for quote in quotes)
        if result.get("reason"):
            lines.append(f"- Processing note: {_packet_line(result['reason'])}")
        lines.append("")
    return "\n".join(lines)


def run_brain_intake(
    vault: Path,
    *,
    state_path: Path,
    local_model: str,
    max_files: int,
    max_chars: int,
    max_bytes: int,
    include_legacy: bool,
    call_model: Callable[[str, str], str],
    generated_at: str | None = None,
) -> dict:
    vault = vault.expanduser().resolve()
    raw = vault / "raw"
    if not vault.is_dir() or not raw.is_dir() or not (vault / "CLAUDE.md").is_file():
        raise ValueError("vault must contain CLAUDE.md and raw/")
    generated_at = generated_at or utc_now().isoformat(timespec="seconds")
    state = load_state(state_path)
    candidates = discover_raw_files(
        vault,
        state,
        max_files=max_files,
        max_bytes=max_bytes,
        include_legacy=include_legacy,
    )
    results: list[dict] = []
    completed = 0
    blocked = 0
    for candidate in candidates:
        result = {
            "source": candidate["relative"],
            "sha256": candidate["sha256"],
            "bytes": candidate["bytes"],
            "state": "TRIAGED",
        }
        if candidate["too_large"]:
            result.update({
                "state": "SKIPPED_TOO_LARGE",
                "classification": "HOLD",
                "suggested_action": "hold",
                "reason": f"source exceeds the {max_bytes}-byte intake limit",
            })
            state.setdefault("files", {})[candidate["relative"]] = {
                "sha256": candidate["sha256"], "state": result["state"], "updated_at": generated_at,
            }
            results.append(result)
            continue
        try:
            text = candidate["path"].read_text(encoding="utf-8", errors="replace")[:max_chars]
            parsed = parse_model_result(call_model(triage_prompt(candidate["relative"], text), local_model))
        except Exception as exc:
            parsed = None
            result.update({"state": "MODEL_BLOCKED", "classification": "HOLD", "suggested_action": "hold", "reason": str(exc)})
        if parsed is None:
            if result.get("state") == "TRIAGED":
                result["state"] = "MODEL_INVALID"
            result.setdefault("classification", "HOLD")
            result.setdefault("suggested_action", "hold")
            result.setdefault("reason", "local model did not return valid JSON; retry later")
            blocked += 1
        else:
            result.update(parsed)
            completed += 1
            state.setdefault("files", {})[candidate["relative"]] = {
                "sha256": candidate["sha256"], "state": "TRIAGED", "updated_at": generated_at,
            }
        results.append(result)
    status = "YELLOW" if blocked else "GREEN"
    packet = ""
    packet_path = ""
    if results:
        output_dir = raw / "scraps"
        output_dir.mkdir(parents=True, exist_ok=True)
        packet_path_obj = output_dir / f"{OWN_PACKET_PREFIX}{generated_at.replace(':', '').replace('+00:00', 'Z')}.md"
        packet = render_packet(generated_at, results, status)
        packet_path_obj.write_text(packet, encoding="utf-8")
        packet_path = str(packet_path_obj)
    state["last_run"] = {"at": generated_at, "status": status, "processed": completed, "blocked": blocked}
    save_state(state_path, state)
    return {
        "status": "NO_WORK" if not candidates else status,
        "discovered": len(candidates),
        "processed": completed,
        "blocked": blocked,
        "packet": packet_path,
        "state": str(state_path),
    }
