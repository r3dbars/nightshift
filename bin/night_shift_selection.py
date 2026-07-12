from __future__ import annotations

import ast
import re
from collections.abc import Callable


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
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                found.append(node.name)
            if isinstance(node, ast.ClassDef):
                found.extend(
                    child.name
                    for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and not child.name.startswith("_")
                )
        return list(dict.fromkeys(found))

    patterns = (
        r"(?m)^\s*(?:(?:export|pub(?:\([^)]*\))?)\s+)?(?:async\s+)?(?:def|class|function|fn|fun)\s+([A-Za-z_][A-Za-z0-9_]*)",
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
    pinned_failed_ci = (
        str(task.get("slug") or "").startswith("failed-ci-")
        and task.get("proof_kind") == "test"
        and bool(task.get("source_ref"))
        and bool(evidence)
        and bool(files)
        and bool(commands)
    )
    if pinned_failed_ci:
        return priority + 1000
    if complete_index and files and commands:
        return priority + 500
    return priority


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
