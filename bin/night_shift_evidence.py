#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import signal
import subprocess
from pathlib import Path


FORBIDDEN_ACTION_RE = re.compile(
    r"\b(merge|release|publish|tag|notarize|deploy|appcast|cask|credential|billing|delete|destructive|move user files?)\b",
    re.IGNORECASE,
)
UNSAFE_APPROVAL_RE = re.compile(
    r"\b(should|can|will|safe to|go ahead and)\s+(push|merge|release|publish|tag|notarize|deploy|delete|move|change credentials|change billing)\b"
    r"|\b(push commits|merge prs|cut releases|deploy to|publish to|update appcast|update cask)\b",
    re.IGNORECASE,
)


def _git_show(repo: Path, source_ref: str, relative: str) -> list[str]:
    proc = subprocess.Popen(
        ["git", "show", f"{source_ref}:{relative}"],
        cwd=repo,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = proc.communicate(timeout=30)
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, signal.SIGTERM)
        try:
            proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGKILL)
            proc.communicate()
        raise OSError("git show timed out")
    if proc.returncode != 0:
        raise OSError(stderr or stdout)
    return stdout.splitlines()


def first_label_value(output: str, labels: list[str]) -> str:
    def clean_value(value: str) -> str:
        return re.sub(r"^\d+[.)]\s+", "", value.strip())

    lines = output.splitlines()
    for index, raw_line in enumerate(lines):
        line = raw_line.strip().lstrip("-*0123456789. ")
        lower = line.lower()
        for label in labels:
            needle = label.lower()
            if lower.startswith(needle):
                value = line[len(label) :].strip(" :-")
                if value:
                    return clean_value(value)
                for next_line in lines[index + 1 :]:
                    next_value = next_line.strip().strip("-* ")
                    if not next_value:
                        continue
                    if re.match(r"^[A-Z_ ]+:\s*$", next_value):
                        break
                    return clean_value(next_value)
    return ""


def label_block(output: str, labels: list[str]) -> str:
    lines = output.splitlines()
    collected: list[str] = []
    active = False
    for raw in lines:
        stripped = raw.strip()
        normalized = stripped.lstrip("-*0123456789. ")
        lower = normalized.lower()
        if not active:
            for label in labels:
                if lower.startswith(label.lower()):
                    active = True
                    inline = normalized[len(label) :].strip(" :-")
                    if inline:
                        collected.append(inline)
                    break
            continue
        if re.match(r"^\d+[.)]\s+[A-Z][A-Z_ ]+:", stripped) or re.match(r"^[A-Z][A-Z_ ]+:", stripped):
            break
        collected.append(stripped)
    return "\n".join(line for line in collected if line).strip()


def evidence_validation_reasons(
    output: str,
    repo: Path | None,
    candidate_files: list[str] | None = None,
    proof_kind: str = "source",
    evidence_sources: dict[str, str] | None = None,
    source_ref: str = "",
) -> list[str]:
    if not repo:
        return []
    block = label_block(output, ["EVIDENCE"])
    entries = re.findall(r"(?:^|\s|[-*`])([A-Za-z0-9_./@+-]+):(\d+)\s*\|\s*([^\n]+)", block)
    if not entries:
        return ["evidence did not include `path:line | exact source line`"]
    task_id = first_label_value(output, ["TASK_ID", "TASK ID"])
    if task_id.startswith("issue-") and len(entries) != 1:
        return ["issue evidence must contain exactly one citation"]
    evidence_bullets = [line for line in block.splitlines() if line.lstrip().startswith(("-", "*"))]
    if any(not re.search(r"[A-Za-z0-9_./@+-]+:\d+\b", line) for line in evidence_bullets):
        return ["evidence contains a statement that was not tied to an exact path:line"]
    supplied_sources = evidence_sources or {}
    allowed = set(candidate_files or []) | set(supplied_sources)
    claim = first_label_value(output, ["CLAIM"])
    negative_claim = bool(re.search(r"\b(does not|doesn't|missing|no|lacks?|absent|without)\b", claim, re.IGNORECASE))
    intent_claim = bool(re.search(r"\b(intentional(?:ly)?|deliberate(?:ly)?)\b", claim, re.IGNORECASE))
    denied_intent_claim = bool(re.search(
        r"\b(?:not\s+(?:intentional(?:ly)?|deliberate(?:ly)?)|unintentional(?:ly)?)\b",
        claim,
        re.IGNORECASE,
    ))
    if negative_claim and proof_kind != "test":
        return ["negative claim requires deterministic repository proof"]
    claimed_paths = {
        value.strip("`.,:;()[]")
        for value in re.findall(r"`([^`]+)`|((?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.@+-]+)", claim)
        for value in value
        if value and "/" in value
    }
    stop = {
        "about", "after", "change", "changes", "code", "coverage", "file", "files",
        "from", "into", "line", "missing", "night", "repo", "shift", "test", "tests",
        "that", "this", "with", "logic",
    }
    claim_words = {
        word.rstrip("s") for word in re.findall(r"[a-z0-9]+", claim.lower()) if len(word) >= 4 and word not in stop
    }
    valid_entries = 0
    for relative, raw_line, raw_quote in entries:
        if allowed and relative not in allowed:
            return [f"evidence path was not supplied to the worker: {relative}"]
        try:
            if relative in supplied_sources:
                lines = str(supplied_sources[relative]).splitlines()
            elif source_ref:
                lines = _git_show(repo, source_ref, relative)
            else:
                path = (repo / relative).resolve()
                path.relative_to(repo.resolve())
                lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            source_line = lines[int(raw_line) - 1]
        except (OSError, ValueError, IndexError):
            return [f"evidence path or line does not exist: {relative}:{raw_line}"]
        quote = raw_quote.strip().strip("`").strip('"').strip()
        if " ".join(quote.split()) != " ".join(source_line.strip().split()):
            return [f"evidence quote does not match source: {relative}:{raw_line}"]
        source_intent = bool(re.search(
            r"\b(intentional(?:ly)?|deliberate(?:ly)?)\b", source_line, re.IGNORECASE
        ))
        source_denied_intent = bool(re.search(
            r"\b(?:not\s+(?:intentional(?:ly)?|deliberate(?:ly)?)|unintentional(?:ly)?)\b",
            source_line,
            re.IGNORECASE,
        ))
        if intent_claim and (not source_intent or denied_intent_claim != source_denied_intent):
            return [f"cited line does not support claimed intent: {relative}:{raw_line}"]
        source_words = {
            word.rstrip("s") for word in re.findall(r"[a-z0-9]+", source_line.lower()) if len(word) >= 4 and word not in stop
        }
        if claim_words & source_words:
            valid_entries += 1
        else:
            return [f"cited line does not support the claim: {relative}:{raw_line}"]
    if valid_entries != len(entries):
        return ["not every cited line supports the claim"]
    return []


def summarize_output(output: str) -> str:
    for labels in [
        ["CLAIM"],
        ["BEST_NEXT_ACTION", "BEST NEXT ACTION"],
        ["PROPOSED_CHANGE", "PROPOSED CHANGE"],
        ["SUMMARY"],
    ]:
        value = first_label_value(output, labels)
        if value:
            return value
    return " ".join(output.strip().split())[:180] or "No usable summary captured."


def action_type(output: str) -> str:
    value = first_label_value(output, ["ACTION_TYPE", "ACTION TYPE"]).lower()
    value = re.sub(r"[^a-z-]+", "", value)
    if value in {"brief", "issue", "patch-plan", "draft-pr-candidate", "reject"}:
        return value
    low = output.lower()
    if "draft pr candidate" in low or "draft-pr-candidate" in low:
        return "draft-pr-candidate"
    if "safe_for_draft_pr: yes" in low or "safe for draft pr: yes" in low:
        return "draft-pr-candidate"
    if "proposed_change" in low or "proposed change" in low:
        return "patch-plan"
    if "issue" in low:
        return "issue"
    return "brief"


def concrete_paths(output: str, candidate_files: list[str] | None = None) -> list[str]:
    candidates = candidate_files or []
    found = [path for path in candidates if path and path in output]
    if candidates:
        return list(dict.fromkeys(found))[:8]
    path_pattern = re.compile(r"(?<![\w.-])(?:[\w.-]+/)+[\w.@+-]+\.[A-Za-z0-9]+")
    file_block = label_block(output, ["FILES_TO_TOUCH", "FILES TO TOUCH"])
    return list(dict.fromkeys(found + path_pattern.findall(file_block)))[:8]


def clean_inline_code(value: str) -> str:
    cleaned = value.strip()
    cleaned = re.sub(r"^```(?:bash|sh|shell)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    if len(cleaned) >= 2 and cleaned.startswith("`") and cleaned.endswith("`"):
        cleaned = cleaned[1:-1].strip()
    return cleaned


def proposes_test_theater(output: str) -> bool:
    """Detect test plans that prove symbol presence instead of behavior."""
    proposal_lines = [
        line for line in output.splitlines()
        if not (
            re.match(r"\s*(?:EVIDENCE\s*:)?\s*[A-Za-z0-9_./@+-]+:\d+\s*\|", line, re.IGNORECASE)
            or re.search(r"\[[A-Za-z0-9_./@+-]+(?::\d+)?\]\([^\n)]+:\d+(?:[-–]\d+)?\)", line)
            or re.search(r"\[[A-Za-z0-9_./@+-]+:\d+\]\([^\n)]+\)", line)
        )
    ]
    low = " ".join("\n".join(proposal_lines).lower().split())
    presence_test = re.search(
        r"(?:test|assert|check).{0,48}(?:signature|import|exist(?:s|ence)?|identifier|textual (?:match|reference))"
        r"|(?:signature|import|exist(?:s|ence)?|identifier|textual (?:match|reference)).{0,48}(?:test|assert|check)",
        low,
    )
    behavior = re.search(
        r"\b(?:return(?:s|ed|ing)?|rais(?:e|es|ed|ing)|throw(?:s|n|ing)?|response|status code|state change|side effect|output|error message|failure path|success path|observable behavior)\b",
        low,
    )
    return bool(presence_test and not behavior)


def output_quality_reasons(
    rc: int,
    output: str,
    candidate_files: list[str] | None = None,
    verification_commands: list[str] | None = None,
    repo: Path | None = None,
    proof_kind: str = "source",
    evidence_sources: dict[str, str] | None = None,
    source_ref: str = "",
) -> list[str]:
    if rc != 0:
        return ["worker command failed"]
    if not output.strip():
        return ["worker returned no output"]
    reasons: list[str] = []
    evidence = first_label_value(output, ["EVIDENCE"])
    verification = first_label_value(output, ["TESTS_TO_RUN", "TESTS TO RUN", "VERIFICATION"])
    expected = first_label_value(output, ["EXPECTED_RESULT", "EXPECTED RESULT"])
    paths = concrete_paths(output, candidate_files)
    file_block = label_block(output, ["FILES_TO_TOUCH", "FILES TO TOUCH"])
    proposed_paths = re.findall(
        r"(?<![\w.-])([A-Za-z0-9_.@+-]+(?:/[A-Za-z0-9_.@+-]+)*\.[A-Za-z0-9]+)",
        file_block,
    )
    if not evidence or evidence.lower() in {"none", "n/a", "unknown"}:
        reasons.append("missing repo evidence")
    elif not re.search(r"[A-Za-z0-9_./@+-]+:\d+\s*\|\s*\S+", evidence):
        reasons.append("evidence must include `path:line | exact source line`")
    if not paths:
        reasons.append("missing an exact repo-relative path")
    elif candidate_files and any(path not in set(candidate_files) for path in proposed_paths):
        reasons.append("file to touch was not supplied to the worker")
    if not verification or verification.lower() in {"none", "n/a", "unknown"}:
        reasons.append("missing an exact verification command")
    elif verification_commands and not any(command in verification for command in verification_commands):
        reasons.append("verification command was not detected from this repo")
    if not expected or expected.lower() in {"none", "n/a", "unknown"}:
        reasons.append("missing the expected proof result")
    reasons.extend(
        evidence_validation_reasons(output, repo, candidate_files, proof_kind, evidence_sources, source_ref)
    )
    coverage_only = any(str(path).startswith("coverage-index/") for path in (evidence_sources or {}))
    if coverage_only and proposes_test_theater(output):
        reasons.append("coverage proposal tests symbol presence instead of observable behavior")
    if action_type(output) == "reject":
        reasons.append("worker explicitly rejected the task")
    return reasons


def confidence_bonus(output: str) -> int:
    confidence = first_label_value(output, ["CONFIDENCE"]).lower()
    risk = first_label_value(output, ["RISK"]).lower()
    if confidence == "high" or risk == "low":
        return 8
    if confidence == "medium" or risk == "medium":
        return 4
    if confidence == "low" or risk == "high":
        return -6
    return 0


def score_output(
    rc: int,
    output: str,
    candidate_files: list[str] | None = None,
    verification_commands: list[str] | None = None,
    repo: Path | None = None,
    proof_kind: str = "source",
    evidence_sources: dict[str, str] | None = None,
    source_ref: str = "",
) -> str:
    low = output.lower()
    if rc != 0:
        return "REJECT"
    if not output.strip():
        return "REJECT"
    if UNSAFE_APPROVAL_RE.search(output) and (
        "safe_for_draft_pr: yes" in low
        or "safe for draft pr: yes" in low
        or "safe_for_codex_to_attempt: yes" in low
        or "safe for codex to attempt: yes" in low
    ):
        return "REJECT"
    if action_type(output) == "reject":
        return "REJECT"
    quality_reasons = output_quality_reasons(
        rc,
        output,
        candidate_files,
        verification_commands,
        repo,
        proof_kind,
        evidence_sources,
        source_ref,
    )
    critical_quality = (
        "evidence",
        "cited line",
        "not every cited",
        "claimed missing test",
        "negative claim",
        "missing an exact repo-relative path",
        "missing an exact verification command",
        "verification command",
        "file to touch",
        "coverage proposal",
    )
    if any(reason.startswith(critical_quality) for reason in quality_reasons):
        return "REJECT"
    safe_yes = (
        "safe_for_draft_pr: yes" in low
        or "safe for draft pr: yes" in low
        or "safe_for_codex_to_attempt: yes" in low
        or "safe for codex to attempt: yes" in low
    )
    if safe_yes and not quality_reasons:
        # Worker prose is never proof by itself. Deterministic execution can
        # promote a MAYBE candidate to a proven draft later in the pipeline.
        return "MAYBE"
    if len(quality_reasons) <= 1 and (
        "best_next_action:" in low
        or "best next action:" in low
        or "proposed_change:" in low
        or "proposed change:" in low
        or "safe_for_draft_pr: no" in low
        or "safe for draft pr: no" in low
    ):
        return "MAYBE"
    return "REJECT"


def artifact_priority(row: dict) -> int:
    base = {"KEEP": 100, "MAYBE": 45, "REJECT": 0}.get(row["score"], 0)
    output = row.get("output", "")
    if row["lane"] == "windows":
        base += 5
    if "test" in output.lower():
        base += 6
    if "exact" in output.lower() or "file" in output.lower():
        base += 4
    if UNSAFE_APPROVAL_RE.search(output):
        base -= 25
    base += confidence_bonus(output)
    if row["rc"] != 0 or row["timed_out"]:
        base -= 40
    return base
