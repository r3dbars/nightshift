from __future__ import annotations

import ast
import json
import os
import posixpath
import re
from collections.abc import Callable
from pathlib import Path

from night_shift_portfolio import parse_json_text, status_check_failed
from night_shift_js_evidence import (
    JS_EXTENSIONS,
    simple_exported_function,
    top_level_symbol_call_count_text as js_symbol_call_count_text,
)
from night_shift_python_evidence import owner_symbol_call_count_text, top_level_symbol_call_count_text
from night_shift_selection import (
    declared_symbols,
    relevant_tests_for_source,
    task_selection_priority,
    unchecked_issue_actions,
)
from night_shift_swift_evidence import swift_symbol_call_count_text


MAX_SOURCE_BYTES = 262_144
MAX_COVERAGE_FILE_BYTES = 524_288
MAX_TEST_CORPUS_BYTES = 8_388_608

CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".swift", ".go", ".rs", ".rb", ".java", ".kt", ".cs", ".c", ".cc", ".cpp", ".h"}

TASK_LADDER = {
    "repair": 500,
    "finish": 400,
    "strengthen": 300,
    "understand": 200,
    "index": 100,
}


def complete_invocation_evidence(value: str) -> bool:
    return any(
        f"analysis={analysis}" in value
        for analysis in ("python-ast", "typescript-regex", "swift-regex")
    ) and "call_matches=0" in value and "scan_complete=true" in value


def complete_invocation_scan(value: str) -> bool:
    return any(
        f"analysis={analysis}" in value
        for analysis in ("python-ast", "typescript-regex", "swift-regex")
    ) and "scan_complete=true" in value


def goal_semantic_contract(goal: str) -> dict:
    low = goal.lower()
    contract: dict[str, object] = {}
    if re.search(
        r"\b(?:behavioral|focused|regression)\s+test\b|"
        r"\btest\b.{0,32}\b(?:exercise|exercises|cover|covers|invoke|invokes|assert|asserts|prove|proves)\b",
        low,
    ):
        contract["minimum_target_invocations"] = 1
    if re.search(r"\bboth\b.{0,40}\b(?:outcomes?|paths?|results?)\b", low):
        contract["minimum_target_invocations"] = 2
    if re.search(r"\btrue\b", low) and re.search(r"\bfalse\b", low) or re.search(r"\bboth boolean\b", low):
        contract["required_boolean_outcomes"] = [True, False]
    ordered = re.search(
        r"\border(?:ed|ing)?\s+([a-z_][a-z0-9_-]*)\s+(?:and|then|before)\s+"
        r"([a-z_][a-z0-9_-]*)\s+(?:calls?|commands?|operations?)\b",
        low,
    )
    if ordered:
        contract["ordered_terms"] = [ordered.group(1), ordered.group(2)]
    return contract


def is_test_path(relative: str) -> bool:
    return bool(re.search(
        r"(^|/)(test|tests|spec|specs)(/|$)|(^|/)(test|spec)_[^/]+\.|(_test|_spec|\.test|\.spec)\.",
        relative,
        re.IGNORECASE,
    ))


def symbol_is_test_addressable(path: str, source: str, symbol: str) -> bool:
    """Reject JS/TS top-level internals that tests cannot import directly."""
    if Path(path).suffix.lower() == ".py":
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return False
        if any(
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == symbol
            for node in tree.body
        ):
            return True
        properties = python_property_methods(source)
        matches: list[tuple[str, str]] = []
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            for child in node.body:
                if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) or child.name != symbol:
                    continue
                matches.append((node.name, child.name))
        return not matches or any(match not in properties for match in matches)
    if Path(path).suffix.lower() not in JS_EXTENSIONS:
        return True
    escaped = re.escape(symbol)
    exported = re.search(
        rf"(?m)^export\s+(?:(?:async|default)\s+)*(?:function|class|const|let|var)\s+{escaped}\b",
        source,
    ) or re.search(rf"(?m)^export\s*\{{[^}}]*\b{escaped}\b[^}}]*\}}", source)
    return bool(exported)


def contains_identifier(text: str, term: str) -> bool:
    return bool(re.search(rf"\b{re.escape(term)}\b", text))


def typescript_gap_is_draftable(
    evidence: dict[str, str], read_current_text: Callable[[str], str]
) -> bool:
    """Keep automatic JS/TS test patches limited to small pure exports."""
    invocation = next(
        (
            value
            for key, value in evidence.items()
            if key.startswith("invocation-index/")
            and "analysis=typescript-regex" in value
        ),
        "",
    )
    source_match = re.search(r"(?m)^source_file=([^\n]+)", invocation)
    symbol_match = re.search(r"(?m)^symbol=([^\n]+)", invocation)
    if not source_match or not symbol_match:
        return False
    source = read_current_text(source_match.group(1).strip())
    return bool(source and simple_exported_function(source, symbol_match.group(1).strip()))


def python_owned_methods(text: str) -> list[tuple[str, str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    properties = python_property_methods(text)
    methods: list[tuple[str, str]] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        methods.extend(
            (node.name, child.name)
            for child in node.body
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            and not child.name.startswith("_")
            and (node.name, child.name) not in properties
        )
    return methods


def python_property_methods(text: str) -> set[tuple[str, str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return set()
    cached_aliases = {"cached_property"}
    cached_aliases.update(
        alias.asname or alias.name
        for node in tree.body if isinstance(node, ast.ImportFrom)
        for alias in node.names if alias.name == "cached_property"
    )
    properties: set[tuple[str, str]] = set()
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for child in node.body:
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            decorators = {
                decorator.id if isinstance(decorator, ast.Name) else decorator.attr
                for decorator in child.decorator_list
                if isinstance(decorator, (ast.Name, ast.Attribute))
            }
            if "property" in decorators or decorators & cached_aliases:
                properties.add((node.name, child.name))
    return properties


def task_file_priority(path: str) -> int:
    name = Path(path).name.lower()
    suffix = Path(path).suffix.lower()
    if name.startswith("test_") or "/test" in path.lower() or "/spec" in path.lower():
        return 0
    if suffix in CODE_EXTENSIONS or path.startswith("bin/"):
        return 1
    if path.startswith((".github/", "docs/")) or suffix in {".md", ".rst"}:
        return 3
    if name.startswith(".") or suffix in {".json", ".lock", ".png", ".jpg", ".jpeg"}:
        return 4
    return 2


def narrow_task_files(files: list[str], limit: int = 6) -> list[str]:
    unique = list(dict.fromkeys(path for path in files if path and not path.startswith(".git/")))
    ranked = sorted(enumerate(unique), key=lambda row: (task_file_priority(row[1]), row[0]))
    return [path for _, path in ranked[:limit]]


def imported_source_paths(relative: str, text: str, available: set[str]) -> list[str]:
    """Resolve repo-local TypeScript/JavaScript imports to tracked files."""
    found: list[str] = []
    for specifier in re.findall(r"(?:from|import)\s*[\"']([^\"']+)[\"']", text):
        if specifier.startswith("@/"):
            base = specifier[2:]
        elif specifier.startswith("."):
            base = posixpath.normpath(posixpath.join(posixpath.dirname(relative), specifier))
        else:
            continue
        candidates = [base] if posixpath.splitext(base)[1] else [
            base,
            *(f"{base}{suffix}" for suffix in (".ts", ".tsx", ".js", ".jsx")),
            *(f"{base}/index{suffix}" for suffix in (".ts", ".tsx", ".js", ".jsx")),
        ]
        found.extend(candidate for candidate in candidates if candidate in available)
    return list(dict.fromkeys(found))


class RepoRevisionAdapter:
    """Resolve immutable Git evidence without accepting arbitrary refs or paths."""

    def __init__(self, repo: Path | None, run_cmd: Callable):
        self.repo = repo
        self.run_cmd = run_cmd

    def file_exists(self, relative: str, ref: str) -> bool:
        if not self.repo or not self._valid_sha(ref) or not self._valid_path(relative):
            return False
        result = self.run_cmd(["git", "cat-file", "-e", f"{ref}:{relative}"], cwd=self.repo, timeout=20)
        return result.rc == 0

    def ensure_pr_ref(self, number: str, ref: str) -> bool:
        if not self.repo or not self._valid_sha(ref):
            return False
        if self._commit_exists(ref):
            return True
        if not str(number).isdigit():
            return False
        fetched = self.run_cmd(
            ["git", "fetch", "--quiet", "--no-tags", "origin", f"refs/pull/{number}/head"],
            cwd=self.repo,
            timeout=120,
        )
        return fetched.rc == 0 and self._commit_exists(ref)

    def ensure_branch_ref(self, branch: str, ref: str) -> bool:
        if not self.repo or not self._valid_sha(ref):
            return False
        if self._commit_exists(ref):
            return True
        if not branch or branch.startswith("-") or ".." in branch or not re.fullmatch(r"[A-Za-z0-9._/-]+", branch):
            return False
        fetched = self.run_cmd(
            ["git", "fetch", "--quiet", "--no-tags", "origin", f"refs/heads/{branch}"],
            cwd=self.repo,
            timeout=120,
        )
        return fetched.rc == 0 and self._commit_exists(ref)

    def list_files(self, ref: str) -> list[str] | None:
        if not self.repo or not self._valid_sha(ref):
            return None
        result = self.run_cmd(["git", "ls-tree", "-r", "--name-only", ref], cwd=self.repo, timeout=60)
        return result.stdout.splitlines() if result.rc == 0 else None

    @staticmethod
    def log_paths(log_text: str) -> list[str]:
        found = re.findall(
            r"(?<![A-Za-z0-9_.@+-])((?:[A-Za-z0-9_.@+-]+/)+[A-Za-z0-9_.@+-]+\.[A-Za-z0-9]+)",
            log_text,
        )
        suffixes: list[str] = []
        for value in found:
            parts = value.lstrip("/").split("/")
            suffixes.extend("/".join(parts[index:]) for index in range(len(parts)))
        return list(dict.fromkeys(suffixes))

    def _commit_exists(self, ref: str) -> bool:
        result = self.run_cmd(["git", "cat-file", "-e", f"{ref}^{{commit}}"], cwd=self.repo, timeout=20)
        return result.rc == 0

    @staticmethod
    def _valid_sha(ref: str) -> bool:
        return bool(ref and re.fullmatch(r"[0-9a-fA-F]{40}", ref))

    @staticmethod
    def _valid_path(relative: str) -> bool:
        return bool(relative and not relative.startswith(("/", ".git/")) and ".." not in Path(relative).parts)


class QueueEvidenceIndex:
    """Build bounded source evidence without executing repository code."""

    def __init__(self, repo: Path | None, scan: dict):
        self.repo = repo
        self.scan = scan
        self.tracked_files = scan.get("tracked_files") or []
        self.source_files = scan.get("source_files") or []
        self.test_files = scan.get("test_files") or []
        self._source_text_cache: dict[str, str] = {}

    def read_current_text(self, relative: str, max_bytes: int = MAX_SOURCE_BYTES) -> str:
        if not self.repo:
            return ""
        try:
            with (self.repo / relative).open("rb") as handle:
                raw = handle.read(max_bytes + 1)
        except OSError:
            return ""
        if b"\x00" in raw[:4096]:
            return ""
        return raw[:max_bytes].decode("utf-8", errors="replace")

    def issue_candidate_files(self, issue: dict) -> tuple[list[str], int]:
        issue_text = f"{issue.get('title', '')}\n{issue.get('body', '')}"
        direct = [path for path in self.tracked_files if path and path in issue_text]
        quoted = re.findall(r"`([^`\n]{4,120})`", issue_text)
        terms = [
            term for term in dict.fromkeys(quoted)
            if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_:.()]*", term)
            and not term.startswith(("http", "TODO", "FIXME"))
        ][:20]
        matched_terms: set[str] = set()
        matched_files: list[tuple[str, int]] = []
        for path in self.source_files[:120]:
            if path not in self._source_text_cache:
                self._source_text_cache[path] = self.read_current_text(path)
            text = self._source_text_cache[path]
            file_terms = [term for term in terms if contains_identifier(text, term.rstrip("()"))]
            if file_terms:
                matched_files.append((path, len(file_terms)))
                matched_terms.update(file_terms)
        matched_files.sort(key=lambda row: -row[1])
        files = list(dict.fromkeys([*(path for path, _ in matched_files), *direct]))[:12]
        return files, len(matched_terms)

    def coverage_gaps(
        self, recent_source: list[str], preferred_symbols: list[str] | None = None
    ) -> list[tuple[str, str, dict[str, str]]]:
        coverage_test_paths = self.scan.get("coverage_test_files") or [
            path for path in self.tracked_files if is_test_path(path)
        ]
        corpus_parts: list[str] = []
        corpus_bytes = 0
        corpus_files_scanned = 0
        corpus_complete = True
        for path in coverage_test_paths:
            if corpus_bytes >= MAX_TEST_CORPUS_BYTES:
                corpus_complete = False
                break
            file_limit = min(MAX_COVERAGE_FILE_BYTES, MAX_TEST_CORPUS_BYTES - corpus_bytes)
            text, indexed = self._read_coverage_text(path, file_limit)
            if not indexed:
                corpus_complete = False
            corpus_parts.append(text)
            corpus_bytes += len(text.encode("utf-8", errors="replace"))
            corpus_files_scanned += 1
        test_corpus = "\n".join(corpus_parts)
        gaps: list[tuple[str, str, dict[str, str]]] = []
        for path in recent_source:
            if is_test_path(path):
                continue
            if Path(path).suffix.lower() == ".swift" and not self.swift_source_is_testable(path, test_corpus):
                continue
            source_text = self.read_current_text(path)
            symbols = declared_symbols(source_text)
            preferred = [symbol for symbol in (preferred_symbols or []) if symbol in symbols]
            owned_methods = python_owned_methods(source_text) if Path(path).suffix == ".py" else []
            ordered_symbols = list(dict.fromkeys(
                preferred + [symbol for _owner, symbol in owned_methods] + symbols
            ))
            ordered_symbols = [
                symbol for symbol in ordered_symbols
                if symbol_is_test_addressable(path, source_text, symbol)
            ]
            owner = ""
            owned_invocation: dict[str, str] = {}
            preferred_owned = sorted(
                owned_methods,
                key=lambda row: (0 if row[1] in preferred else 1, owned_methods.index(row)),
            )
            missing = ""
            for candidate_owner, candidate_symbol in preferred_owned:
                invocation = self.invocation_gap(path, candidate_symbol, candidate_owner)
                invocation_text = "\n".join(invocation.values())
                if "call_matches=0" in invocation_text and "scan_complete=true" in invocation_text:
                    owner, missing, owned_invocation = candidate_owner, candidate_symbol, invocation
                    break
            if not missing:
                missing = next(
                    (
                        symbol for symbol in ordered_symbols
                        if not symbol.startswith("_")
                        and not re.search(rf"\b{re.escape(symbol)}\b", test_corpus)
                    ),
                    "",
                )
            if not missing:
                continue
            safe_source = re.sub(r"[^A-Za-z0-9_.-]+", "-", path).strip("-")
            safe_symbol = re.sub(r"[^A-Za-z0-9_.-]+", "-", missing)
            evidence_path = f"coverage-index/{safe_source}-{safe_symbol}.txt"
            evidence = {evidence_path: "\n".join([
                f"symbol={missing}",
                f"source_file={path}",
                f"tracked_test_files={len(coverage_test_paths)}",
                f"files_scanned={corpus_files_scanned}",
                "identifier_matches=0",
                f"scan_complete={'true' if corpus_complete and corpus_files_scanned == len(coverage_test_paths) else 'false'}",
            ])}
            if owner:
                evidence.update(owned_invocation)
            elif Path(path).suffix == ".py":
                evidence.update(self.invocation_gap(path, missing))
            elif Path(path).suffix.lower() in {".ts", ".tsx"}:
                evidence.update(self.invocation_gap(path, missing))
            elif Path(path).suffix.lower() == ".swift":
                evidence.update(self.invocation_gap(path, missing))
            evidence.update(self.symbol_source_evidence(path, missing, owner))
            gaps.append((path, missing, evidence))
        return gaps

    @staticmethod
    def swift_source_is_testable(source_path: str, test_corpus: str) -> bool:
        """Only queue Swift sources whose module is imported by existing tests."""
        parts = Path(source_path).parts
        try:
            module = parts[parts.index("Sources") + 1]
        except (ValueError, IndexError):
            return True
        return bool(re.search(rf"(?m)^\s*(?:@testable\s+)?import\s+{re.escape(module)}\b", test_corpus))

    def invocation_gap(self, source_path: str, symbol: str, owner: str = "") -> dict[str, str]:
        """Prove that tracked tests contain no executable call to a named symbol."""
        if symbol not in declared_symbols(self.read_current_text(source_path)):
            return {}
        coverage_test_paths = self.scan.get("coverage_test_files") or [
            path for path in self.tracked_files if is_test_path(path)
        ]
        if Path(source_path).suffix == ".py":
            coverage_test_paths = [path for path in coverage_test_paths if Path(path).suffix == ".py"]
        calls = 0
        scanned = 0
        complete = True
        total_bytes = 0
        if Path(source_path).suffix == ".py":
            analysis = "python-ast" if coverage_test_paths and all(
                Path(path).suffix == ".py" for path in coverage_test_paths
            ) else "mixed-regex"
        elif Path(source_path).suffix.lower() in {".ts", ".tsx"}:
            analysis = "typescript-regex" if coverage_test_paths and all(
                Path(path).suffix.lower() in JS_EXTENSIONS
                for path in coverage_test_paths
            ) else "mixed-regex"
        elif Path(source_path).suffix.lower() == ".swift":
            analysis = "swift-regex" if coverage_test_paths and all(
                Path(path).suffix.lower() == ".swift"
                for path in coverage_test_paths
            ) else "mixed-regex"
        else:
            analysis = "mixed-regex"
        for path in coverage_test_paths:
            if total_bytes >= MAX_TEST_CORPUS_BYTES:
                complete = False
                break
            limit = min(MAX_COVERAGE_FILE_BYTES, MAX_TEST_CORPUS_BYTES - total_bytes)
            text, indexed = self._read_coverage_text(path, limit)
            if not indexed:
                complete = False
            total_bytes += len(text.encode("utf-8", errors="replace"))
            scanned += 1
            if Path(path).suffix == ".py":
                if owner:
                    counted = owner_symbol_call_count_text(text, owner, symbol)
                else:
                    counted = top_level_symbol_call_count_text(text, symbol)
                if counted is None:
                    complete = False
                    continue
                calls += counted
            elif analysis == "typescript-regex":
                counted = js_symbol_call_count_text(text, symbol)
                if counted is None:
                    complete = False
                    continue
                calls += counted
            elif analysis == "swift-regex":
                calls += swift_symbol_call_count_text(text, symbol)
            else:
                calls += len(re.findall(rf"(?:\.|\b){re.escape(symbol)}\s*\(", text))
        safe_source = re.sub(r"[^A-Za-z0-9_.-]+", "-", source_path).strip("-")
        safe_symbol = re.sub(r"[^A-Za-z0-9_.-]+", "-", symbol)
        return {f"invocation-index/{safe_source}-{safe_symbol}.txt": "\n".join([
            f"symbol={symbol}",
            f"source_file={source_path}",
            f"owner={owner or 'none'}",
            f"analysis={analysis}",
            "scope=test-files-only",
            f"tracked_test_files={len(coverage_test_paths)}",
            f"files_scanned={scanned}",
            f"symbol={symbol} call_matches={calls}",
            f"scan_complete={'true' if coverage_test_paths and complete and scanned == len(coverage_test_paths) else 'false'}",
        ])}

    def symbol_source_evidence(
        self, source_path: str, symbol: str, owner: str = ""
    ) -> dict[str, str]:
        lines = self.read_current_text(source_path).splitlines()
        declaration = None
        if Path(source_path).suffix == ".py":
            try:
                tree = ast.parse("\n".join(lines))
                if owner:
                    owner_node = next(
                        value for value in tree.body
                        if isinstance(value, ast.ClassDef) and value.name == owner
                    )
                    node = next(
                        value for value in owner_node.body
                        if isinstance(value, (ast.FunctionDef, ast.AsyncFunctionDef))
                        and value.name == symbol
                    )
                else:
                    node = next(
                        value for value in tree.body
                        if isinstance(value, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                        and value.name == symbol
                    )
                declaration = node.lineno - 1
            except (SyntaxError, StopIteration):
                return {}
        else:
            declaration = next(
                (index for index, line in enumerate(lines) if contains_identifier(line, symbol)),
                None,
            )
        if declaration is None:
            return {}
        start = max(0, declaration)
        excerpt = [f"source_file={source_path}"]
        excerpt.extend(
            f"source_line={index + 1} | {lines[index].strip()}"
            for index in range(start, min(len(lines), start + 6))
            if lines[index].strip()
        )
        safe_source = re.sub(r"[^A-Za-z0-9_.-]+", "-", source_path).strip("-")
        safe_symbol = re.sub(r"[^A-Za-z0-9_.-]+", "-", symbol)
        return {f"goal-source/{safe_source}-{safe_symbol}.txt": "\n".join(excerpt)}

    def _read_coverage_text(self, relative: str, max_bytes: int) -> tuple[str, bool]:
        if not self.repo:
            return "", False
        try:
            with (self.repo / relative).open("rb") as handle:
                raw = handle.read(max_bytes + 1)
        except OSError:
            return "", False
        if len(raw) > max_bytes or b"\x00" in raw[:4096]:
            return "", False
        return raw.decode("utf-8", errors="replace"), True


def build_repo_work_queue(
    repo: Path | None,
    scan: dict,
    mode: str,
    permission: str,
    guidance: str = "scan",
    goal_text: str = "",
    *,
    run_cmd: Callable,
    detect_test_commands: Callable,
) -> list[dict]:
    queue: list[dict] = []

    def add(
        slug: str,
        kind: str,
        prompt: str,
        reason: str,
        files: list[str] | None = None,
        ladder: str = "strengthen",
        preferred_lane: str = "local",
        proof_kind: str = "source",
        signal: str = "",
        evidence_sources: dict[str, str] | None = None,
        source_ref: str = "",
        commands: list[str] | None = None,
        executable: bool = False,
        signal_strength: int = 0,
        semantic_contract: dict | None = None,
    ) -> None:
        if slug in {item["slug"] for item in queue}:
            return
        queue.append(
            {
                "slug": slug,
                "kind": kind,
                "prompt": prompt,
                "reason": reason,
                "files": narrow_task_files(files or []),
                "verification_commands": commands if commands is not None else test_commands,
                "ladder": ladder,
                "ladder_priority": TASK_LADDER[ladder],
                "preferred_lane": preferred_lane,
                "proof_kind": proof_kind,
                "signal": signal,
                "evidence_sources": evidence_sources or {},
                "source_ref": source_ref,
                "executable": executable,
                "signal_strength": signal_strength,
                "semantic_contract": semantic_contract or {},
            }
        )

    recent = scan.get("recent_files") or []
    tests = list(dict.fromkeys([
        *(scan.get("test_files") or []),
        *(scan.get("coverage_test_files") or []),
    ]))
    docs = scan.get("doc_files") or []
    todos = scan.get("todo_sample") or []
    test_commands = scan.get("test_commands") or []
    source_files = scan.get("source_files") or []
    tracked_files = scan.get("tracked_files") or []
    recent_source = [path for path in recent if path in source_files]
    pull_requests = parse_json_text(scan.get("github_open_prs_raw", ""), [])
    issues = parse_json_text(scan.get("github_open_issues_raw", ""), [])
    failed_runs = sorted(
        parse_json_text(scan.get("github_failed_runs_raw", ""), []),
        key=lambda run: run.get("updatedAt", ""),
        reverse=True,
    )
    failed_logs = parse_json_text(scan.get("github_failed_logs_raw", ""), [])

    evidence_index = QueueEvidenceIndex(repo, scan)
    read_current_text = evidence_index.read_current_text
    issue_candidate_files = evidence_index.issue_candidate_files
    coverage_gaps = evidence_index.coverage_gaps(recent_source)
    revisions = RepoRevisionAdapter(repo, run_cmd)
    todo_files = []
    for line in todos:
        match = re.match(r"^(.+?):\d+:", line)
        if match:
            value = match.group(1)
            if repo and value.startswith(str(repo) + os.sep):
                value = str(Path(value).relative_to(repo))
            todo_files.append(value)
    todo_files = list(dict.fromkeys(todo_files))

    if guidance == "goal" and goal_text.strip():
        ignored_goal_terms = {
            "add", "assert", "behavioral", "existing", "focused", "method", "patterns",
            "return", "returned", "test", "tests", "using", "value", "verify", "verifies",
        }
        goal_terms = list(dict.fromkeys(
            term for term in re.findall(r"[A-Za-z_][A-Za-z0-9_]*", goal_text)
            if len(term) >= 4 and term.lower() not in ignored_goal_terms
        ))
        dotted_references = re.findall(
            r"\b[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\b", goal_text
        )
        identity_terms = list(dict.fromkeys(
            segment for reference in dotted_references for segment in reference.split(".")
        ))
        goal_matches: list[tuple[int, str]] = []
        for path in [value for value in source_files if not is_test_path(value)][:120]:
            text = read_current_text(path)
            identity_score = sum(1 for term in identity_terms if contains_identifier(text, term))
            declared_goal_score = sum(
                1 for term in goal_terms if term in declared_symbols(text)
            )
            broad_score = sum(1 for term in goal_terms if contains_identifier(text, term))
            score = (identity_score + declared_goal_score) * 100 + broad_score
            if score:
                goal_matches.append((score, path))
        goal_matches.sort(key=lambda row: (-row[0], row[1]))
        mission_sources = [path for _score, path in goal_matches[:4]]
        dotted_symbols = [
            match.rsplit(".", 1)[-1]
            for match in dotted_references
        ]
        preferred_goal_symbols = list(dict.fromkeys(dotted_symbols + goal_terms))
        mission_gaps = evidence_index.coverage_gaps(mission_sources, preferred_goal_symbols)
        mission_evidence: dict[str, str] = {}
        mission_symbol = ""
        mission_owner = ""
        if mission_sources:
            source_symbols = declared_symbols(read_current_text(mission_sources[0]))
            mission_symbol = next(
                (
                    symbol for symbol in preferred_goal_symbols
                    if symbol in source_symbols
                    and ("_" in symbol or len(symbol) >= 8 or symbol in dotted_symbols)
                ),
                "",
            )
            if dotted_symbols and dotted_symbols[0] == mission_symbol:
                mission_owner = dotted_references[0].rsplit(".", 1)[0].rsplit(".", 1)[-1]
        if mission_sources and mission_symbol:
            mission_evidence.update(
                evidence_index.invocation_gap(mission_sources[0], mission_symbol, mission_owner)
            )
            mission_evidence.update(
                evidence_index.symbol_source_evidence(mission_sources[0], mission_symbol, mission_owner)
            )
        for _path, symbol, evidence in mission_gaps:
            if symbol in preferred_goal_symbols:
                mission_evidence.update(evidence)
        mission_tests: list[str] = []
        for path in mission_sources:
            mission_tests.extend(relevant_tests_for_source(path, tests, read_current_text)[:2])
        mission_files = list(dict.fromkeys(mission_sources + mission_tests + recent_source[:6]))
        approved_test_files = [path for path in mission_files if is_test_path(path)]
        mission_semantic_contract = goal_semantic_contract(goal_text)
        mission_draftable = True
        if mission_sources and Path(mission_sources[0]).suffix.lower() in JS_EXTENSIONS:
            mission_draftable = simple_exported_function(
                read_current_text(mission_sources[0]), mission_symbol
            ) if mission_symbol else False
        mission_executable = bool(
            mission_symbol
            and mission_evidence
            and test_commands
            and mission_draftable
            and any(
                key.startswith("invocation-index/")
                and complete_invocation_scan(value)
                for key, value in mission_evidence.items()
            )
        )
        mission_prompt = f"Turn this user mission into the smallest safe repo task: {goal_text.strip()}"
        if approved_test_files:
            mission_prompt += (
                f" Use the existing approved test file `{approved_test_files[0]}`. "
                "Do not create a new test file; FILES_TO_TOUCH may contain only the listed candidate files."
            )
        if mission_executable and mission_semantic_contract:
            mission_prompt += (
                " Return ACTION_TYPE: draft-pr-candidate only if the requested behavior is safe and can be "
                "proved in the approved test file; otherwise return ACTION_TYPE: reject."
            )
        add(
            "mission-brief",
            "mission",
            mission_prompt,
            "User supplied a specific mission.",
            mission_files,
            ladder="repair",
            preferred_lane="local",
            proof_kind="test" if mission_evidence else "source",
            signal=goal_text.strip(),
            evidence_sources=mission_evidence,
            executable=mission_executable,
            semantic_contract=mission_semantic_contract,
        )
    if coverage_gaps:
        gap_path, gap_symbol, gap_evidence = coverage_gaps[0]
        add(
            "recent-change-test-gap",
            "tests",
            f"Inspect only `{gap_symbol}` in `{gap_path}`. Cite that exact source line plus the supplied coverage-index evidence. Reject if the index is incomplete or this exact gap is unsupported.",
            "This declared symbol has no textual match in the tracked test corpus.",
            [gap_path] + relevant_tests_for_source(gap_path, tests, read_current_text)[:4],
            ladder="strengthen",
            preferred_lane="local",
            evidence_sources=gap_evidence,
        )
    if test_commands:
        add(
            "test-command-proof",
            "proof",
            "Check whether the detected test commands are the right proof path for a small morning PR. Identify the fastest command and the gap it proves.",
            "Night Shift should hand the user exact verification commands.",
            (tests + recent)[:12],
            ladder="strengthen",
        )
    if docs:
        add(
            "docs-command-drift",
            "docs",
            "Find one stale or confusing setup command, quickstart step, or report command in the docs. Prefer beginner-facing fixes.",
            "Docs are safe overnight work and make the project easier to run.",
            docs[:20],
            ladder="strengthen",
        )
    if todos:
        add(
            "todo-risk-triage",
            "triage",
            "Cluster TODO/FIXME/HACK comments into one morning-ready issue candidate with exact files and risk.",
            "TODOs often contain real small chores if they are deduped.",
            todo_files[:20],
            ladder="understand",
        )
    for run in failed_runs[:2]:
        database_id = run.get("databaseId") or "unknown"
        source_ref = str(run.get("headSha") or "")
        log_row = next((row for row in failed_logs if (row.get("run") or {}).get("databaseId") == run.get("databaseId")), {})
        log_text = str(log_row.get("log", ""))
        log_evidence_path = f"github-actions/run-{database_id}.log"
        matching_pr = next(
            (pr for pr in pull_requests if pr.get("headRefName") == run.get("headBranch")),
            {},
        )
        if source_ref and repo:
            if matching_pr.get("number"):
                revisions.ensure_pr_ref(str(matching_pr["number"]), source_ref)
            else:
                revisions.ensure_branch_ref(str(run.get("headBranch") or ""), source_ref)
        pr_files = [row.get("path", "") for row in matching_pr.get("files") or [] if row.get("path")]
        signal_files = [path for path in revisions.log_paths(log_text) if revisions.file_exists(path, source_ref)][:8]
        workflow_files = [path for path in scan.get("tracked_files") or [] if path.startswith(".github/workflows/")][:4]
        candidate_files = list(dict.fromkeys(signal_files + pr_files + workflow_files + recent[:8]))
        if source_ref:
            candidate_files = [path for path in candidate_files if revisions.file_exists(path, source_ref)]
        candidate_files = candidate_files[:32]
        branch_commands = test_commands
        if repo and source_ref:
            ref_files = revisions.list_files(source_ref)
            if ref_files is not None:
                branch_commands = detect_test_commands(repo, ref_files, source_ref) or test_commands
        add(
            f"failed-ci-{database_id}",
            "tests",
            f"Use failed GitHub run {database_id} and its supplied failed-step log to identify one narrow repair. Reject if the log does not name a concrete failing file, test, or command.",
            "A recent failed workflow is a stronger signal than a generic code scan.",
            candidate_files,
            ladder="repair",
            preferred_lane="windows",
            proof_kind="test",
            signal=json.dumps({"run": run, "failed_log_evidence": log_evidence_path}, sort_keys=True),
            evidence_sources={log_evidence_path: log_text} if log_text else {},
            source_ref=source_ref,
            commands=branch_commands,
            executable=True,
        )
    issue_rows = []
    for issue in issues[:20]:
        candidate_files, matched_terms = issue_candidate_files(issue)
        issue_rows.append((issue, candidate_files, matched_terms, len(unchecked_issue_actions(issue))))
    issue_rows.sort(key=lambda row: (row[3] > 1, -row[2], -len(row[1])))
    selected_issue_rows = issue_rows[:3]
    if mode == "afterburner":
        tracker = next((row for row in issue_rows if row[3] > 1), None)
        if tracker and tracker not in selected_issue_rows:
            selected_issue_rows = [*selected_issue_rows[:2], tracker]
    for issue, issue_files, matched_terms, _ in selected_issue_rows:
        number = issue.get("number") or "unknown"
        add(
            f"issue-{number}-next-action",
            "issue",
            f"Map GitHub issue #{number} to supplied source and propose the smallest verifiable next action. Reject it if the issue is stale or the source does not support it.",
            "Open issues describe work a maintainer has already chosen to track.",
            issue_files,
            ladder="finish",
            preferred_lane="windows",
            signal=json.dumps(issue, sort_keys=True),
            signal_strength=matched_terms,
        )
    for pr in pull_requests[:5]:
        number = pr.get("number") or "unknown"
        pr_files = [row.get("path", "") for row in pr.get("files") or [] if row.get("path")]
        pr_source_ref = str(pr.get("headRefOid") or "")
        if pr_source_ref and revisions.ensure_pr_ref(str(number), pr_source_ref):
            pr_files = [path for path in pr_files if revisions.file_exists(path, pr_source_ref)]
            ref_files = set(revisions.list_files(pr_source_ref) or [])
            for relative in list(pr_files):
                shown = run_cmd(["git", "show", f"{pr_source_ref}:{relative}"], cwd=repo, timeout=30)
                if shown.rc == 0:
                    pr_files.extend(imported_source_paths(relative, shown.stdout, ref_files))
        elif pr_source_ref:
            pr_files = []
            pr_source_ref = ""
        checks = pr.get("statusCheckRollup") or []
        failed_checks = [row for row in checks if status_check_failed(row)]
        failed_check = bool(failed_checks)
        status_evidence: dict[str, str] = {}
        if failed_checks:
            evidence_lines = [f"pull_request={number}"]
            for index, check in enumerate(failed_checks, start=1):
                name = str(check.get("name") or check.get("context") or "unknown")
                state = str(check.get("conclusion") or check.get("state") or "unknown").upper()
                url = str(check.get("detailsUrl") or check.get("targetUrl") or "")
                evidence_lines.append(f"check_{index}={name} state={state} url={url}")
            status_evidence = {f"github-status/pr-{number}.txt": "\n".join(evidence_lines)}
        state = "requested changes" if pr.get("reviewDecision") == "CHANGES_REQUESTED" else "failed checks" if failed_check else "open draft" if pr.get("isDraft") else "open review"
        add(
            f"pr-{number}-review",
            "triage",
            f"Review PR #{number} as a {state}. Compare its supplied files and checks with current source, then name one exact next action or reject it as already healthy.",
            "Open PRs are real repo work, not generic suggestions.",
            pr_files[:12] or recent[:8],
            ladder="finish",
            preferred_lane="windows" if failed_check or pr.get("reviewDecision") == "CHANGES_REQUESTED" else "local",
            signal=json.dumps(pr, sort_keys=True),
            evidence_sources=status_evidence,
            commands=test_commands or ["git status --short"],
            source_ref=pr_source_ref,
        )
    for index, (path, symbol, gap_evidence) in enumerate(coverage_gaps[:12], start=1):
        safe = re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-").lower()[:48]
        has_supported_gap = any(
            key.startswith("invocation-index/")
            and complete_invocation_evidence(value)
            for key, value in gap_evidence.items()
        )
        is_typescript_gap = any(
            key.startswith("invocation-index/") and "analysis=typescript-regex" in value
            for key, value in gap_evidence.items()
        )
        draftable_gap = has_supported_gap and (
            not is_typescript_gap
            or typescript_gap_is_draftable(gap_evidence, read_current_text)
        )
        add(
            f"changed-file-proof-{index:02d}-{safe}",
            "tests",
            (
                (
                    f"Add one focused behavioral test for `{symbol}` in `{path}` using the supplied "
                    f"{'exact imported' if is_typescript_gap else 'owner-aware'} direct-test-call and source evidence. "
                    "Return ACTION_TYPE: draft-pr-candidate and name the existing test file to change. "
                    "Reject if a safe observable behavior cannot be asserted."
                    if has_supported_gap else
                    f"Inspect only `{symbol}` in `{path}`. Cite that exact source line plus the supplied coverage-index evidence. Do not discuss another function; reject when the index is incomplete or this exact gap is unsupported."
                )
            ),
            "A declared source symbol with no textual test match is a bounded coverage lead, not proof of a gap.",
            [path] + relevant_tests_for_source(path, tests, read_current_text)[:5],
            ladder="strengthen",
            preferred_lane="local",
            proof_kind="test",
            executable=bool(test_commands and draftable_gap),
            evidence_sources=gap_evidence,
            semantic_contract={"minimum_target_invocations": 1} if has_supported_gap else {},
        )

    for index in range(0, min(len(tests), 24), 4):
        batch = tests[index : index + 4]
        add(
            f"test-contract-map-{index // 4 + 1:02d}",
            "map",
            "Map what these tests actually prove, which production files they exercise, and one evidence-backed blind spot. Reject invented gaps.",
            "A durable test-to-code map makes future overnight work faster and less repetitive.",
            batch + recent_source[:4],
            ladder="understand",
            preferred_lane="local",
            proof_kind="source",
            commands=["git status --short"],
        )

    for index, path in enumerate(docs[:12], start=1):
        safe = re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-").lower()[:48]
        add(
            f"docs-command-check-{index:02d}-{safe}",
            "docs",
            "Check this documentation file for commands, paths, or promises that can be compared directly with tracked files and CLI help. Report only exact contradictions.",
            "Documentation verification is safe background work with a clear source of truth.",
            [path] + recent[:4],
            ladder="strengthen",
            preferred_lane="local",
            proof_kind="source",
            commands=["git status --short"],
        )

    for index in range(0, min(len(source_files), 60), 6):
        batch = source_files[index : index + 6]
        add(
            f"source-map-{index // 6 + 1:02d}",
            "map",
            "Build a compact ownership and dependency map for only these files. Name public entry points, tests, and risky boundaries using exact citations; do not propose changes without evidence.",
            "Repository understanding compounds across nights and gives later coding tasks better context.",
            batch + tests[:3],
            ladder="index",
            preferred_lane="local",
            proof_kind="source",
            commands=["git status --short"],
        )

    limit = {"quiet": 10, "night-shift": 40, "afterburner": 100}.get(mode, 40)
    for item in queue:
        item["selection_priority"] = task_selection_priority(item)
    # Python's sort is stable, so equal-priority tasks keep live-signal recency
    # and insertion order instead of being reordered by arbitrary IDs.
    return sorted(queue, key=lambda item: -item["selection_priority"])[:limit]
