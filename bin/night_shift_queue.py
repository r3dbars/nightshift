from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

from night_shift_selection import declared_symbols


MAX_SOURCE_BYTES = 262_144
MAX_TEST_CORPUS_BYTES = 8_388_608


def is_test_path(relative: str) -> bool:
    return bool(re.search(
        r"(^|/)(test|tests|spec|specs)(/|$)|(^|/)(test|spec)_[^/]+\.|(_test|_spec|\.test|\.spec)\.",
        relative,
        re.IGNORECASE,
    ))


def contains_identifier(text: str, term: str) -> bool:
    return bool(re.search(rf"\b{re.escape(term)}\b", text))


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

    def coverage_gaps(self, recent_source: list[str]) -> list[tuple[str, str, dict[str, str]]]:
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
            file_limit = min(MAX_SOURCE_BYTES, MAX_TEST_CORPUS_BYTES - corpus_bytes)
            text, indexed = self._read_coverage_text(path, file_limit)
            if not indexed:
                corpus_complete = False
            corpus_parts.append(text)
            corpus_bytes += len(text.encode("utf-8", errors="replace"))
            corpus_files_scanned += 1
        test_corpus = "\n".join(corpus_parts)
        gaps: list[tuple[str, str, dict[str, str]]] = []
        for path in recent_source:
            symbols = declared_symbols(self.read_current_text(path))
            missing = next(
                (symbol for symbol in symbols if not symbol.startswith("_") and not re.search(rf"\b{re.escape(symbol)}\b", test_corpus)),
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
            gaps.append((path, missing, evidence))
        return gaps

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
