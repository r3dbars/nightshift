from __future__ import annotations

import ast
import json
import re
from collections.abc import Callable

from night_shift_portfolio import status_check_failed


IGNORED_PATH_TERMS = {
    "app", "api", "src", "lib", "route", "index", "page", "test", "tests", "unit", "id",
}


def declared_symbols(text: str) -> list[str]:
    """Return testable declarations without treating Python nested helpers as APIs."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        tree = None
    if tree is not None:
        found: list[str] = []

        def visit_node(node: ast.AST, class_scope: bool = False) -> None:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not class_scope or not node.name.startswith("_"):
                    found.append(node.name)
                return
            if isinstance(node, ast.ClassDef):
                if not class_scope:
                    found.append(node.name)
                visit_scope(node.body, class_scope=True)
                return
            for child in ast.iter_child_nodes(node):
                visit_node(child, class_scope=class_scope)

        def visit_scope(statements: list[ast.stmt], class_scope: bool = False) -> None:
            for node in statements:
                visit_node(node, class_scope=class_scope)

        visit_scope(tree.body)
        return list(dict.fromkeys(found))

    patterns = (
        r"(?m)^\s*(?:(?:export|pub(?:\([^)]*\))?)\s+)?(?:async\s+)?(?:def|class|function|fn|fun)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"(?m)^\s*(?:(?:public|internal|private|fileprivate|open|final|static)\s+)*(?:class|struct|enum|actor|func)\s+([A-Za-z_][A-Za-z0-9_]*)",
        r"(?m)^\s*(?:pub(?:\([^)]*\))?\s+)?func\s+(?:\([^)]*\)\s*)?([A-Za-z_][A-Za-z0-9_]*)",
        r"(?m)^\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)\s*=.*=>",
        r"(?m)^\s*(?:(?:public|private|protected|internal|static|final|open|override|suspend|async)\s+)+"
        r"[A-Za-z_][A-Za-z0-9_<>,.?\[\]:]*\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(",
        r"(?m)^\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(\s*\)\s*\{",
    )
    found = []
    for pattern in patterns:
        found.extend(re.findall(pattern, text))
    return list(dict.fromkeys(found))


def task_selection_priority(task: dict) -> int:
    """Rank deterministic evidence above broad exploratory work."""
    priority = int(task.get("ladder_priority") or 0)
    evidence = "\n".join(str(value) for value in (task.get("evidence_sources") or {}).values())
    files = task.get("files") or []
    commands = task.get("verification_commands") or []
    complete_index = "scan_complete=true" in evidence and "identifier_matches=0" in evidence
    owner_aware_gap = (
        "analysis=python-ast" in evidence
        and "call_matches=0" in evidence
        and "scan_complete=true" in evidence
        and bool(re.search(r"(?m)^owner=(?!none$).+", evidence))
    )
    pinned_failed_ci = (
        str(task.get("slug") or "").startswith("failed-ci-")
        and task.get("proof_kind") == "test"
        and bool(task.get("source_ref"))
        and bool(evidence)
        and bool(files)
        and bool(commands)
    )
    if task.get("slug") == "mission-brief" and task.get("kind") == "mission":
        return priority + 2000
    if pinned_failed_ci:
        return priority + 1000
    if owner_aware_gap and files and commands:
        return priority + 800
    if complete_index and files and commands:
        return priority + 500
    return priority + min(100, max(0, int(task.get("signal_strength") or 0)) * 10)


def requests_coverage_work(goal: str) -> bool:
    action = r"(?:add|audit|create|expand|find|fix|identify|improve|increase|locate|review|strengthen|write)"
    target = r"(?:test|tests|testing|coverage|regression)"
    return bool(re.search(rf"\b(?:{action}\b.{{0,128}}\b{target}|{target}\b.{{0,128}}\b{action})\b", goal, re.IGNORECASE))


def unchecked_issue_actions(signal: dict) -> list[str]:
    body = str(signal.get("body") or "")
    return [
        match.group(1).strip()
        for match in re.finditer(r"^\s*[-*]\s*\[\s\]\s+(.+)$", body, re.IGNORECASE | re.MULTILINE)
    ]


def _task_signal(task: dict) -> dict:
    signal = task.get("signal", "")
    if isinstance(signal, dict):
        return signal
    try:
        parsed = json.loads(signal)
    except (TypeError, ValueError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def model_task_readiness_reasons(
    task: dict, mode: str, goal: str = "", permission: str = "brief"
) -> list[str]:
    """Reject low-signal work before it consumes local or LAN model tokens."""
    reasons: list[str] = []
    slug = str(task.get("slug") or "")
    files = task.get("files") or []
    commands = [command for command in task.get("verification_commands") or [] if command != "git status --short"]
    signal = _task_signal(task)
    if not files:
        reasons.append("no exact repo file is tied to the signal")
    if task.get("kind") in {"tests", "issue"} and not commands:
        reasons.append("no deterministic verification command was detected")
    invocation_evidence = [
        str(value) for key, value in (task.get("evidence_sources") or {}).items()
        if str(key).startswith("invocation-index/")
    ]
    if invocation_evidence:
        if any("scan_complete=true" not in value for value in invocation_evidence):
            reasons.append("named-symbol invocation index is incomplete")

    if slug.startswith("failed-ci-"):
        evidence = "\n".join(str(value) for value in (task.get("evidence_sources") or {}).values()).strip()
        if not task.get("source_ref"):
            reasons.append("failed CI is not pinned to a head SHA")
        if not evidence or re.search(r"log not found|no logs? found|unable to (?:fetch|read).*log", evidence, re.IGNORECASE):
            reasons.append("failed CI has no usable failed-step log")
        elif not re.search(r"\b(error|failed|failure|assert(?:ion)?|exception|panic|fatal)", evidence, re.IGNORECASE):
            reasons.append("failed-step log has no concrete failure marker")
        elif files and not any(path in evidence for path in files):
            reasons.append("failed-step log does not name a candidate repo file")
    elif slug.startswith("pr-"):
        checks = signal.get("statusCheckRollup") or []
        failed_check = any(status_check_failed(row) for row in checks)
        if signal.get("reviewDecision") != "CHANGES_REQUESTED" and not failed_check:
            reasons.append("PR has neither requested changes nor failed checks")
        if not task.get("source_ref"):
            reasons.append("PR review is not pinned to its head SHA")
    elif slug.startswith("issue-"):
        actions = unchecked_issue_actions(signal)
        if mode != "afterburner" and len(actions) > 1:
            reasons.append(f"issue is a {len(actions)}-item tracker reserved for afterburner")
    elif slug == "recent-change-test-gap" or slug.startswith("changed-file-proof-"):
        evidence = "\n".join(str(value) for value in (task.get("evidence_sources") or {}).values())
        if "scan_complete=true" not in evidence:
            reasons.append("coverage index is incomplete")
        if "identifier_matches=0" not in evidence:
            reasons.append("coverage index does not prove zero identifier matches")
        if mode != "afterburner" and not requests_coverage_work(goal):
            reasons.append("coverage-index-only work is reserved for afterburner or an explicit coverage goal")
        if (
            slug == "recent-change-test-gap"
            and permission in {"draft-local", "draft-prs"}
            and not task.get("executable")
        ):
            reasons.append("test candidate has no safe automatic patch path")
    elif slug == "mission-brief" and requests_coverage_work(goal):
        if not task.get("evidence_sources"):
            reasons.append("coverage mission has no deterministic gap evidence; use a coverage-index task")

    if (
        permission in {"draft-local", "draft-prs"}
        and task.get("kind") == "tests"
        and task.get("proof_kind") == "test"
        and not task.get("executable")
    ):
        reasons.append("test candidate has no safe automatic patch path")

    broad_kind = task.get("kind") in {"map", "docs", "proof"} or (
        task.get("kind") == "triage" and not slug.startswith("pr-")
    )
    if mode != "afterburner" and broad_kind:
        reasons.append("broad mapping or inspection work is reserved for afterburner")
    return list(dict.fromkeys(reasons))


def model_ready_tasks(
    queue: list[dict], mode: str, goal: str = "", permission: str = "brief"
) -> tuple[list[dict], list[dict]]:
    ready: list[dict] = []
    skipped: list[dict] = []
    for task in queue:
        reasons = model_task_readiness_reasons(task, mode, goal, permission)
        if reasons:
            skipped.append({"slug": task.get("slug", ""), "category": "pre-model", "reason": "; ".join(reasons)})
        else:
            ready.append(task)
    return ready, skipped


def relevant_tests_for_source(
    source_path: str,
    test_paths: list[str],
    read_text: Callable[[str, int], str],
) -> list[str]:
    """Rank tests by path overlap and exact source-path references."""
    source_terms = {
        term for term in re.findall(r"[a-z0-9]+", source_path.lower())
        if len(term) > 2 and term not in IGNORED_PATH_TERMS
    }
    ranked: list[tuple[int, int, str]] = []
    for index, test_path in enumerate(test_paths):
        test_terms = set(re.findall(r"[a-z0-9]+", test_path.lower()))
        score = len(source_terms & test_terms) * 10
        if source_path in read_text(test_path, 131_072):
            score += 100
        ranked.append((-score, index, test_path))
    return [path for _, _, path in sorted(ranked)]
