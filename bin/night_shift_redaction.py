"""Small, conservative redaction pass for text sent to model lanes or ledgers."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any


SECRET_PATTERNS = (
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)\bAuthorization\s*:\s*(?:Bearer|Basic)\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|token|secret|password)\s*([:=])\s*([^\s'\"]{8,}|['\"][^'\"]+['\"])") ,
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)

SENSITIVE_NAMES = {
    "credentials", "credentials.json", "id_rsa", "id_ed25519", "known_hosts",
    ".netrc", ".npmrc", ".pypirc",
}
SENSITIVE_PARTS = {".ssh", ".aws", ".gnupg", "secrets", "private-keys"}
SENSITIVE_SUFFIXES = {".key", ".pem", ".p12", ".pfx", ".jks"}


def redact(text: str) -> str:
    result = text
    for pattern in SECRET_PATTERNS:
        result = pattern.sub("[REDACTED_SECRET]", result)
    return result


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def context_path_is_sensitive(path: str) -> bool:
    candidate = Path(path)
    parts = tuple(part.lower() for part in candidate.parts)
    name = candidate.name.lower()
    return (
        candidate.is_absolute()
        or ".." in candidate.parts
        or name == ".env"
        or name.startswith(".env.")
        or name in SENSITIVE_NAMES
        or any(part in SENSITIVE_PARTS for part in parts)
        or candidate.suffix.lower() in SENSITIVE_SUFFIXES
    )


def sanitize_evidence_sources(sources: Any) -> dict[str, str]:
    if not isinstance(sources, dict):
        return {}
    return {
        str(path): redact(str(value))
        for path, value in sources.items()
        if not context_path_is_sensitive(str(path))
    }


def sanitize_task_for_ledger(task: dict) -> dict:
    def sanitize_value(value: Any) -> Any:
        if isinstance(value, str):
            return redact(value)
        if isinstance(value, dict):
            return sanitize_task_for_ledger(value)
        if isinstance(value, list):
            return [sanitize_value(item) for item in value]
        return value

    safe: dict = {}
    for key, value in task.items():
        if key == "evidence_sources":
            safe[key] = sanitize_evidence_sources(value)
        elif key == "files" and isinstance(value, list):
            safe[key] = [
                redact(str(path)) for path in value if not context_path_is_sensitive(str(path))
            ]
        else:
            safe[key] = sanitize_value(value)
    return safe
