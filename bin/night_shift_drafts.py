from __future__ import annotations

import json
import os
import re
import shutil
import textwrap
import time
from pathlib import Path
from typing import Callable

from night_shift_policy import RepoProfile, path_is_allowed, path_is_protected
from night_shift_models import output_token_budget
from night_shift_sandbox import sandbox_command, sandbox_patch_command
from night_shift_patch_protocol import (
    materialize_test_method_patch,
    materialize_ts_test_case_patch,
    patch_prompt,
    typescript_import_path,
    validate_patch,
)
from night_shift_js_evidence import (
    JS_EXTENSIONS,
    simple_exported_function,
    top_level_symbol_call_count_text as js_symbol_call_count_text,
)
from night_shift_python_evidence import owner_symbol_call_count_text, semantic_test_contract_reasons
from night_shift_queue import is_test_path
from night_shift_state import record_state

MAX_VERIFICATION_REPAIRS = 2


def draft_proof_status(baseline_rc: int, after_rc: int, guards: list[str]) -> tuple[str, str]:
    if guards:
        return "REJECT", "not proven"
    if baseline_rc != 0 and after_rc == 0:
        return "PROVEN_REPAIR", "failing-before and passing-after"
    return "VERIFIED_DRAFT", "passing repository check after a bounded patch"


def remaining_draft_timeout(
    timeout: int,
    deadline: float | None = None,
    stop_file: Path | None = None,
) -> int:
    if stop_file and stop_file.exists():
        return 0
    if deadline is None:
        return max(1, timeout)
    return max(0, min(timeout, int(deadline - time.time())))


def patch_format_correction(files: list[str]) -> str:
    if len(files) == 1:
        header = f"The first line must be exactly `diff --git a/{files[0]} b/{files[0]}`."
    else:
        approved = ", ".join(files)
        header = (
            "The first line must be `diff --git a/<path> b/<path>` using the same path on both sides. "
            f"Choose only from these approved paths: {approved}."
        )
    return (
        "CORRECTION: Return the complete patch again with no markdown fence or prose. "
        + header
        + " Include the matching `--- a/...`, `+++ b/...`, and `@@` lines."
    )


def verification_correction_prompt(patch: str, failure_output: str) -> str:
    return (
        "VERIFICATION CORRECTION: The patch applied but the approved repository check failed. "
        "Return a complete corrected unified diff against the original pinned source. Change only "
        "the allowed test file and preserve every semantic proof requirement. Match every fake result "
        "attribute to the exact attribute consumed by the pinned source (for example, rc is not "
        "returncode). Match exact source argument types too: a Path object is not its string form. "
        "The corrected diff must make a real textual change; never replace a line with identical text. "
        "Fix the exact latest failure without weakening assertions.\n\n"
        f"CURRENT PATCH:\n{patch[-4000:]}\n\nFAILURE OUTPUT:\n{failure_output[-3000:]}"
    )


def parse_test_strengthening_contract(evidence_sources: dict[str, str] | None) -> dict[str, str] | None:
    contracts: list[dict[str, str]] = []
    for path, text in (evidence_sources or {}).items():
        if not path.startswith("invocation-index/"):
            continue
        fields: dict[str, str] = {}
        for line in text.splitlines():
            if "=" in line:
                key, value = line.split("=", 1)
                fields[key.strip()] = value.strip()
        call_match = re.search(r"^symbol=([^\s]+) call_matches=(\d+)$", text, re.MULTILINE)
        if call_match:
            fields["symbol"] = call_match.group(1)
            fields["call_matches"] = call_match.group(2)
        if (
            fields.get("analysis") in {"python-ast", "typescript-regex"}
            and fields.get("scan_complete") == "true"
            and fields.get("call_matches") == "0"
            and fields.get("symbol")
            and Path(fields.get("source_file", "")).suffix.lower() in {".py", ".ts", ".tsx"}
            and re.fullmatch(r"(?:none|[A-Za-z_][A-Za-z0-9_]*)", fields.get("owner", ""))
        ):
            contracts.append(fields)
    return contracts[0] if len(contracts) == 1 else None


def owner_symbol_call_count(paths: list[Path], owner: str, symbol: str) -> int | None:
    owner = "" if owner == "none" else owner
    calls = 0
    for path in paths:
        try:
            count = owner_symbol_call_count_text(path.read_text(encoding="utf-8"), owner, symbol)
        except (OSError, UnicodeError):
            return None
        if count is None:
            return None
        calls += count
    return calls


def javascript_symbol_call_count(paths: list[Path], symbol: str) -> int | None:
    calls = 0
    for path in paths:
        try:
            count = js_symbol_call_count_text(path.read_text(encoding="utf-8"), symbol)
        except (OSError, UnicodeError):
            return None
        if count is None:
            return None
        calls += count
    return calls


def valid_test_strengthening_candidate(candidate: dict, worktree: Path) -> dict[str, str] | None:
    contract = candidate.get("strengthening_contract")
    files = candidate.get("files") or []
    if candidate.get("draft_intent") != "test-strengthening" or not isinstance(contract, dict):
        return None
    if not files or any(not is_test_path(path) for path in files):
        return None
    analysis = contract.get("analysis")
    if (
        analysis not in {"python-ast", "typescript-regex"}
        or contract.get("scan_complete") != "true"
        or contract.get("call_matches") != "0"
        or not contract.get("symbol")
        or not re.fullmatch(
            r"(?:none|[A-Za-z_][A-Za-z0-9_]*)", str(contract.get("owner") or "")
        )
        or contract.get("source_file") not in (candidate.get("context_files") or [])
    ):
        return None
    source_file = str(contract.get("source_file") or "")
    if analysis == "python-ast":
        if any(not path.endswith(".py") for path in files) or not source_file.endswith(".py"):
            return None
        baseline_calls = owner_symbol_call_count(
            [worktree / path for path in files], contract["owner"], contract["symbol"]
        )
    else:
        try:
            source_text = (worktree / source_file).read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            return None
        if (
            str(contract.get("owner") or "none") != "none"
            or any(Path(path).suffix.lower() not in JS_EXTENSIONS for path in files)
            or Path(source_file).suffix.lower() not in {".ts", ".tsx"}
            or not simple_exported_function(source_text, contract["symbol"])
        ):
            return None
        baseline_calls = javascript_symbol_call_count(
            [worktree / path for path in files], contract["symbol"]
        )
    return contract if baseline_calls == 0 else None


def materialize_strengthening_output(
    output: str, original: str, relative: str, strengthening: dict[str, str] | None,
) -> str:
    if strengthening and strengthening.get("analysis") == "typescript-regex":
        return materialize_ts_test_case_patch(
            output,
            original,
            relative,
            strengthening["symbol"],
            typescript_import_path(str(strengthening["source_file"]), relative),
        )
    return materialize_test_method_patch(
        output,
        original,
        relative,
        {Path(strengthening["source_file"]).stem} if strengthening else set(),
    )


class DraftEngine:
    def __init__(self, run_cmd: Callable, worktree_root: Path, now_stamp: Callable[[], str]) -> None:
        self.run_cmd = run_cmd
        self.worktree_root = worktree_root
        self.now_stamp = now_stamp

    def select_candidate(
        self,
        child_ledger: Path,
        repo: Path,
        repo_signal_scan: Callable[[Path], dict],
        task_ladder: dict[str, int],
    ) -> dict | None:
        try:
            items = json.loads((child_ledger / "work-queue.json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        default_commands = repo_signal_scan(repo).get("test_commands") or []
        items.sort(key=lambda item: (-task_ladder.get(item.get("ladder", "strengthen"), 0), item.get("rank", 999)))
        for item in items:
            if not item.get("executable") or item.get("proof_kind") != "test":
                continue
            if item.get("score") not in {"KEEP", "MAYBE"}:
                continue
            if item.get("action_type") not in {"patch-plan", "draft-pr-candidate"}:
                continue
            source_ref = str(item.get("source_ref") or "")
            if source_ref:
                files = [
                    path
                    for path in item.get("files") or []
                    if self.run_cmd(["git", "cat-file", "-e", f"{source_ref}:{path}"], cwd=repo, timeout=20).rc == 0
                ]
            else:
                files = [path for path in item.get("files") or [] if (repo / path).is_file()]
            known_commands = item.get("verification_commands") or default_commands
            verification = next((command for command in known_commands if command in (item.get("tests") or "")), "")
            contract = parse_test_strengthening_contract(item.get("evidence_sources"))
            if contract:
                extensions = {".py"} if contract.get("analysis") == "python-ast" else JS_EXTENSIONS
                test_files = [
                    path for path in files
                    if is_test_path(path) and Path(path).suffix.lower() in extensions
                ]
                source_file = contract["source_file"]
                source_exists = (
                    self.run_cmd(["git", "cat-file", "-e", f"{source_ref}:{source_file}"], cwd=repo, timeout=20).rc == 0
                    if source_ref else (repo / source_file).is_file()
                )
                if not source_exists or not test_files:
                    continue
                if contract.get("analysis") == "typescript-regex":
                    source_text = (
                        self.run_cmd(["git", "show", f"{source_ref}:{source_file}"], cwd=repo, timeout=30).stdout
                        if source_ref else (repo / source_file).read_text(encoding="utf-8")
                    )
                    if not simple_exported_function(source_text, contract["symbol"]):
                        continue
                files = test_files
                item = {
                    **item,
                    "draft_intent": "test-strengthening",
                    "strengthening_contract": contract,
                    "context_files": [source_file, *test_files],
                }
            if files and verification:
                return {**item, "files": files[:6], "verification": verification}
        return None

    def guard_reasons(
        self, worktree: Path, allowed_files: list[str], profile: RepoProfile | None = None
    ) -> list[str]:
        changed = self.run_cmd(["git", "diff", "--name-only"], cwd=worktree, timeout=30)
        paths = [line.strip() for line in changed.stdout.splitlines() if line.strip()]
        reasons: list[str] = []
        if not paths:
            return ["no patch was produced"]
        if len(paths) > 6:
            reasons.append("patch touched more than 6 files")
        if any(path not in set(allowed_files) for path in paths):
            reasons.append("patch touched a file outside the approved candidate set")
        if profile and any(path_is_protected(path, profile.protected_paths) for path in paths):
            reasons.append("patch touched an immutable verifier, dependency, or policy file")
        if profile and any(not path_is_allowed(path, profile.allowed_paths) for path in paths):
            reasons.append("patch touched a path outside the repo profile allowlist")
        forbidden_names = {
            ".env",
            ".env.local",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "poetry.lock",
            "Cargo.lock",
        }
        if any(Path(path).name in forbidden_names for path in paths):
            reasons.append("patch changed a credential or dependency lock file")
        stats = self.run_cmd(["git", "diff", "--numstat"], cwd=worktree, timeout=30)
        changed_lines = 0
        for line in stats.stdout.splitlines():
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
                changed_lines += int(parts[0]) + int(parts[1])
        if changed_lines > 500:
            reasons.append("patch exceeded the 500-line overnight limit")
        diff = self.run_cmd(["git", "diff", "--unified=0"], cwd=worktree, timeout=30).stdout
        additions = "\n".join(line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++"))
        if re.search(r"(?i)(api[_-]?key|secret|password|private[_-]?key)\s*[:=]\s*['\"][^'\"]+", additions):
            reasons.append("patch appears to add a secret")
        if re.search(r"(?i)\b(merge|release|publish|deploy|notarize|appcast|cask)\b", additions):
            reasons.append("patch adds a forbidden release or deployment action")
        if re.search(
            r"(?i)(allowlist|allow_list|ignore|skip|disable).{0,80}(check|test|lint|security|policy)|"
            r"(check|test|lint|security|policy).{0,80}(allowlist|allow_list|ignore|skip|disable)",
            additions,
        ):
            reasons.append("patch appears to bypass a test, check, or security policy")
        return reasons

    def cleanup(self, repo: Path, worktree: Path) -> bool:
        removed = self.run_cmd(["git", "worktree", "remove", "--force", worktree], cwd=repo, timeout=120)
        self.run_cmd(["git", "worktree", "prune"], cwd=repo, timeout=60)
        return removed.rc == 0

    def source_excerpt(
        self, repo: Path, source_ref: str, files: list[str], focus_symbol: str = ""
    ) -> str:
        sections: list[str] = []
        for path in files:
            shown = self.run_cmd(["git", "show", f"{source_ref}:{path}"], cwd=repo, timeout=30)
            if shown.rc == 0:
                text = shown.stdout
                if is_test_path(path) and len(text) > 10_000:
                    text = text[:2000] + "\n# ... pinned middle omitted ...\n" + text[-4000:]
                elif focus_symbol and not is_test_path(path):
                    names = focus_symbol.split(".")
                    owner, symbol = names[-2:] if len(names) > 1 else ("", names[-1])
                    lines = text.splitlines()
                    anchors: list[int] = []
                    for index, line in enumerate(lines):
                        if owner and re.match(rf"^\s*class\s+{re.escape(owner)}\b", line):
                            anchors.extend(range(index, min(len(lines), index + 18)))
                        if re.match(rf"^\s*(?:async\s+)?def\s+{re.escape(symbol)}\s*\(", line):
                            anchors.extend(range(max(0, index - 4), min(len(lines), index + 16)))
                    if anchors:
                        selected = set(anchors)
                        focused = [lines[index] for index in sorted(selected)]
                        text = "# ... focused source excerpt ...\n" + "\n".join(focused)
                    else:
                        text = text[:6000]
                else:
                    text = text[:6000]
                sections.append(f"## {path}\n{text}")
        return "\n\n".join(sections)

    def ask_for_patch(
        self,
        repo: Path,
        source_ref: str,
        candidate: dict,
        command: tuple[str, ...],
        timeout: int,
        worker_url: str,
        worker_model: str,
        parent_ledger: Path,
        safe_task: str,
        correction: str = "",
        patch_lane: str = "windows",
        max_tokens: int | None = None,
    ):
        codex_home = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
        delegate = shutil.which("maestro-delegate") or str(codex_home / "bin" / "maestro-delegate")
        context_files = candidate.get("context_files") or candidate["files"]
        contract = candidate.get("strengthening_contract") or {}
        focus_symbol = ".".join(
            value for value in (str(contract.get("owner") or ""), str(contract.get("symbol") or "")) if value
        )
        source = self.source_excerpt(repo, source_ref, context_files, focus_symbol)
        if correction:
            # Keep bounded repair calls below small local model context limits.
            source = source[:10000]
        prompt = patch_prompt(candidate, source, command)
        if correction:
            prompt += "\n\n" + correction
        env = os.environ.copy()
        if patch_lane == "local":
            env["MAESTRO_LOCAL_BASE_URL"] = worker_url.rstrip("/")
            env["MAESTRO_LOCAL_MODEL"] = worker_model
            budget = output_token_budget(worker_model, 4096)
            env["MAESTRO_LOCAL_MAX_TOKENS"] = str(min(budget, max_tokens) if max_tokens else budget)
        else:
            env["WINDOWS_WORKER_BASE_URL"] = worker_url.rstrip("/")
            env["WINDOWS_WORKER_MODEL"] = worker_model
            budget = output_token_budget(worker_model, 4096)
            env["MAESTRO_WINDOWS_MAX_TOKENS"] = str(min(budget, max_tokens) if max_tokens else budget)
        return self.run_cmd(
            [delegate, patch_lane, "--label", f"{safe_task}-patch", "--", prompt],
            cwd=repo,
            timeout=timeout,
            env=env,
            pid_log=parent_ledger / "processes.tsv",
        )

    def run_draft(
        self,
        repo: Path,
        repo_name: str,
        candidate: dict,
        parent_ledger: Path,
        timeout: int,
        worker_url: str,
        worker_model: str,
        deadline: float | None = None,
        stop_file: Path | None = None,
        profile: RepoProfile | None = None,
        patch_lane: str = "windows",
        dependency_source: Path | None = None,
    ) -> dict:
        safe_repo = re.sub(r"[^A-Za-z0-9._-]+", "--", repo_name)
        safe_task = re.sub(r"[^A-Za-z0-9._-]+", "-", candidate.get("key", "draft"))[:80]
        worktree = self.worktree_root / safe_repo / f"{self.now_stamp()}-{safe_task}"
        proof_dir = parent_ledger / "drafts" / safe_repo
        proof_dir.mkdir(parents=True, exist_ok=True)
        proof_path = proof_dir / f"{safe_task}.json"
        patch_path = proof_dir / f"{safe_task}.patch"
        lifecycle_path = parent_ledger / "task-lifecycle.jsonl"
        fingerprint = str(candidate.get("fingerprint") or candidate.get("key") or safe_task)
        initial_timeout = remaining_draft_timeout(timeout, deadline, stop_file)
        if initial_timeout <= 0:
            result = {"status": "REJECT", "reason": "stop limit reached before draft execution"}
            proof_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result
        if profile is None:
            result = {"status": "REJECT", "reason": "missing trusted repo profile", "proof_level": "not executed"}
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            proof_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result
        dependency_source = dependency_source or repo / "node_modules"
        worktree.parent.mkdir(parents=True, exist_ok=True)
        source_ref = str(candidate.get("source_ref") or "HEAD")
        if not re.fullmatch(r"[0-9a-f]{40}", source_ref):
            resolved = self.run_cmd(["git", "rev-parse", f"{source_ref}^{{commit}}"], cwd=repo, timeout=30)
            if resolved.rc != 0 or not re.fullmatch(r"[0-9a-f]{40}", resolved.stdout.strip()):
                result = {"status": "REJECT", "reason": "candidate source could not be pinned to an exact commit"}
                proof_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
                return result
            source_ref = resolved.stdout.strip()
        record_state(lifecycle_path, fingerprint, "DISCOVERED", repo=repo_name, source_ref=source_ref, reason="draft candidate selected")
        added = self.run_cmd(
            ["git", "worktree", "add", "--detach", worktree, source_ref],
            cwd=repo,
            timeout=min(initial_timeout, 120),
            pid_log=parent_ledger / "processes.tsv",
        )
        if added.rc != 0:
            removed = self.cleanup(repo, worktree) if worktree.exists() else True
            result = {
                "status": "REJECT",
                "reason": (added.stderr or added.stdout)[:300],
                "worktree": str(worktree),
                "source_ref": source_ref,
                "worktree_removed": removed,
            }
            proof_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
            return result

        def finish(result: dict) -> dict:
            result["worktree_removed"] = self.cleanup(repo, worktree)
            proof_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            return result

        verification_argv = tuple(candidate.get("verification_argv") or ())
        if verification_argv not in profile.commands:
            return finish({"status": "REJECT", "reason": "verification is not approved by the repo profile"})
        verification = " ".join(verification_argv)
        baseline_timeout = remaining_draft_timeout(timeout, deadline, stop_file)
        if baseline_timeout <= 0:
            return finish({"status": "REJECT", "reason": "stop limit reached before baseline verification"})
        baseline = self.run_cmd(
            sandbox_command(worktree, verification_argv, profile, dependency_source),
            cwd=worktree,
            timeout=min(baseline_timeout, profile.max_seconds),
            pid_log=parent_ledger / "processes.tsv",
        )
        (proof_dir / f"{safe_task}.baseline.txt").write_text(
            (baseline.stdout + "\n" + baseline.stderr).strip() + "\n",
            encoding="utf-8",
        )
        baseline_dirty = self.run_cmd(["git", "status", "--porcelain"], cwd=worktree, timeout=30)
        if baseline_dirty.stdout.strip():
            record_state(lifecycle_path, fingerprint, "REJECTED", reason="baseline modified worktree")
            return finish(
                {
                    "status": "REJECT",
                    "reason": "baseline verification modified the disposable worktree",
                    "worktree": str(worktree),
                    "baseline_rc": baseline.rc,
                }
            )
        strengthening = valid_test_strengthening_candidate(candidate, worktree)
        if baseline.rc == 0 and not strengthening:
            record_state(lifecycle_path, fingerprint, "REJECTED", reason="baseline did not reproduce a failure")
            return finish({
                "status": "REJECT",
                "reason": "baseline verification passed; Night Shift only patches reproduced failures",
                "baseline_rc": baseline.rc,
                "proof_level": "baseline clean",
            })
        if baseline.rc == 0:
            record_state(
                lifecycle_path, fingerprint, "GAP_CONFIRMED", baseline_rc=baseline.rc,
                verification=verification, reason="complete zero-invocation gap reproduced",
            )
            record_state(lifecycle_path, fingerprint, "DIAGNOSED", reason="complete zero-invocation proof handed to bounded test worker")
        else:
            record_state(lifecycle_path, fingerprint, "REPRODUCED", baseline_rc=baseline.rc, verification=verification)
            record_state(lifecycle_path, fingerprint, "DIAGNOSED", reason="reproduced failure handed to bounded patch worker")
        if strengthening and not candidate.get("semantic_contract"):
            record_state(
                lifecycle_path, fingerprint, "REJECTED",
                reason="test-strengthening mission has no explicit semantic contract",
            )
            return finish({
                "status": "REJECT",
                "reason": "test-strengthening mission has no explicit semantic contract",
                "baseline_rc": baseline.rc,
                "semantic_contract": {},
                "proof_level": "gap confirmed only",
            })
        if not worker_url or not worker_model:
            record_state(lifecycle_path, fingerprint, "REJECTED", reason="sandboxed coding lane is not configured")
            return finish(
                {
                    "status": "REJECT",
                    "reason": "sandboxed coding lane is not configured",
                    "worktree": str(worktree),
                    "baseline_rc": baseline.rc,
                }
            )
        patch_timeout = remaining_draft_timeout(timeout, deadline, stop_file)
        if patch_timeout <= 0:
            record_state(lifecycle_path, fingerprint, "REJECTED", reason="stop limit reached before patch worker")
            return finish({"status": "REJECT", "reason": "stop limit reached before patch worker", "baseline_rc": baseline.rc})
        model = self.ask_for_patch(
            worktree, source_ref, candidate, verification_argv, patch_timeout,
            worker_url, worker_model, parent_ledger, safe_task, patch_lane=patch_lane,
        )
        worker_path = proof_dir / f"{safe_task}.patch-worker.txt"
        first_model_output = model.stdout
        worker_path.write_text(
            (model.stdout + "\n" + model.stderr).strip() + "\n", encoding="utf-8"
        )
        test_file = candidate["files"][0] if len(candidate["files"]) == 1 else ""
        try:
            original_test = (worktree / test_file).read_text(encoding="utf-8") if test_file else ""
        except (OSError, UnicodeError):
            original_test = ""
        proposed_output = (
            materialize_strengthening_output(model.stdout, original_test, test_file, strengthening)
            if strengthening and strengthening.get("analysis") == "typescript-regex"
            else model.stdout
        )
        proposed = validate_patch(proposed_output, candidate["files"], profile)
        apply_reason = ""
        patch_recovered = False
        if proposed.valid:
            patch_path.write_text(proposed.patch, encoding="utf-8")
            applies = self.run_cmd(["git", "apply", "--check", patch_path], cwd=worktree, timeout=30)
            if applies.rc != 0:
                apply_reason = "patch does not apply to the pinned source"
        if model.rc == 0 and (not proposed.valid or apply_reason) and model.stdout.strip():
            retry_timeout = remaining_draft_timeout(timeout, deadline, stop_file)
            if retry_timeout > 0:
                correction = patch_format_correction(candidate["files"])
                if candidate.get("draft_intent") == "test-strengthening":
                    correction += (
                        " Insert the one test method immediately before the exact final runner lines shown at "
                        "the end of SOURCE EXCERPT. Keep those final lines unchanged as the hunk anchor, and "
                        "ensure every @@ old/new line count matches the actual hunk body."
                    )
                    if strengthening and strengthening.get("analysis") == "typescript-regex":
                        correction += (
                            " For TypeScript, the only accepted import is inside the new test block: "
                            f"`const {{ {strengthening['symbol']} }} = await import('{typescript_import_path(str(strengthening['source_file']), test_file)}')`. "
                            "Never add a module-scope import and never use require."
                        )
                if apply_reason:
                    correction += (
                        " The previous patch did not apply to the pinned commit. Use only exact unchanged "
                        "context copied from SOURCE EXCERPT; do not invent a function, class, line number, or import."
                    )
                retry = self.ask_for_patch(
                    worktree, source_ref, candidate, verification_argv, retry_timeout,
                    worker_url, worker_model, parent_ledger, f"{safe_task}-retry", correction, patch_lane,
                )
                (proof_dir / f"{safe_task}.patch-worker-attempt-1.txt").write_text(
                    worker_path.read_text(encoding="utf-8"), encoding="utf-8"
                )
                worker_path.write_text(
                    (retry.stdout + "\n" + retry.stderr).strip() + "\n", encoding="utf-8"
                )
                model = retry
                proposed_output = (
                    materialize_strengthening_output(model.stdout, original_test, test_file, strengthening)
                    if strengthening and strengthening.get("analysis") == "typescript-regex"
                    else model.stdout
                )
                proposed = validate_patch(proposed_output, candidate["files"], profile)
                apply_reason = ""
                if proposed.valid:
                    patch_path.write_text(proposed.patch, encoding="utf-8")
                    applies = self.run_cmd(["git", "apply", "--check", patch_path], cwd=worktree, timeout=30)
                    if applies.rc != 0:
                        apply_reason = "patch does not apply to the pinned source"
        if candidate.get("draft_intent") == "test-strengthening" and (not proposed.valid or apply_reason):
            for recovery_output in (first_model_output, model.stdout):
                recovered = materialize_strengthening_output(
                    recovery_output, original_test, test_file, strengthening,
                )
                if not recovered:
                    continue
                recovered_check = validate_patch(recovered, candidate["files"], profile)
                patch_path.write_text(recovered, encoding="utf-8")
                applies = self.run_cmd(["git", "apply", "--check", patch_path], cwd=worktree, timeout=30)
                if recovered_check.valid and applies.rc == 0:
                    proposed = recovered_check
                    apply_reason = ""
                    patch_recovered = True
                    break
        if (model.rc != 0 and not patch_recovered) or not proposed.valid or apply_reason:
            rejection = "; ".join(proposed.reasons) or apply_reason or "patch worker failed"
            record_state(lifecycle_path, fingerprint, "REJECTED", reason=rejection)
            return finish({
                "status": "REJECT",
                "reason": rejection,
                "baseline_rc": baseline.rc,
                "patch_worker_rc": model.rc,
                "proof_level": "reproduced only",
            })
        patch_path.write_text(proposed.patch, encoding="utf-8")
        record_state(lifecycle_path, fingerprint, "PATCHED", patch=str(patch_path), paths=list(proposed.paths))
        sandbox_dir = proof_dir / f"{safe_task}-sandbox"
        sandbox_dir.mkdir(parents=True, exist_ok=True)
        verify_timeout = remaining_draft_timeout(timeout, deadline, stop_file)
        if verify_timeout <= 0:
            record_state(lifecycle_path, fingerprint, "REJECTED", reason="stop limit reached before isolated verification")
            return finish({"status": "REJECT", "reason": "stop limit reached before isolated verification", "baseline_rc": baseline.rc})
        verified = self.run_cmd(
            sandbox_patch_command(
                worktree, patch_path, sandbox_dir, verification_argv, profile, dependency_source,
            ),
            cwd=worktree,
            timeout=min(verify_timeout, profile.max_seconds),
            pid_log=parent_ledger / "processes.tsv",
        )
        if verified.rc != 0 and strengthening:
            repair_sandbox = sandbox_dir
            for attempt in range(1, MAX_VERIFICATION_REPAIRS + 1):
                verification_output_path = repair_sandbox / "verification.txt"
                retry_timeout = remaining_draft_timeout(timeout, deadline, stop_file)
                if retry_timeout <= 0:
                    break
                failure_output = (
                    verification_output_path.read_text(encoding="utf-8", errors="replace")[-5000:]
                    if verification_output_path.exists() else (verified.stderr or verified.stdout)[-5000:]
                )
                current_patch = patch_path.read_text(encoding="utf-8", errors="replace")[-8000:]
                correction = verification_correction_prompt(current_patch, failure_output)
                if strengthening and strengthening.get("analysis") == "typescript-regex":
                    correction += (
                        "\nFor this TypeScript test, preserve the exact in-test dynamic import and imported binding: "
                        f"`const {{ {strengthening['symbol']} }} = await import('{typescript_import_path(str(strengthening['source_file']), candidate['files'][0])}')`. "
                        "Never use a module-scope import or require."
                    )
                repair = self.ask_for_patch(
                    worktree, source_ref, candidate, verification_argv, retry_timeout,
                    worker_url, worker_model, parent_ledger,
                    f"{safe_task}-verification-{attempt}", correction, patch_lane, max_tokens=2048,
                )
                (proof_dir / f"{safe_task}.verification-worker-attempt-{attempt}.txt").write_text(
                    (repair.stdout + "\n" + repair.stderr).strip() + "\n", encoding="utf-8"
                )
                if attempt == 1:
                    (proof_dir / f"{safe_task}.verification-worker.txt").write_text(
                        (repair.stdout + "\n" + repair.stderr).strip() + "\n", encoding="utf-8"
                    )
                repaired_output = (
                    materialize_strengthening_output(repair.stdout, original_test, candidate["files"][0], strengthening)
                    if strengthening and strengthening.get("analysis") == "typescript-regex"
                    else repair.stdout
                )
                repaired = validate_patch(repaired_output, candidate["files"], profile)
                repaired_patch = repaired.patch
                repair_applies = False
                if repaired.valid:
                    patch_path.write_text(repaired_patch, encoding="utf-8")
                    repair_applies = self.run_cmd(
                        ["git", "apply", "--check", patch_path], cwd=worktree, timeout=30
                    ).rc == 0
                if (not repaired.valid or not repair_applies) and len(candidate["files"]) == 1:
                    try:
                        original_test = (worktree / candidate["files"][0]).read_text(encoding="utf-8")
                    except (OSError, UnicodeError):
                        original_test = ""
                    repaired_patch = materialize_strengthening_output(
                        repair.stdout, original_test, candidate["files"][0], strengthening,
                    )
                    repaired = validate_patch(repaired_patch, candidate["files"], profile)
                    if repaired.valid:
                        patch_path.write_text(repaired_patch, encoding="utf-8")
                        repair_applies = self.run_cmd(
                            ["git", "apply", "--check", patch_path], cwd=worktree, timeout=30
                        ).rc == 0
                if repair.rc != 0 or not repaired.valid or not repair_applies:
                    continue
                patch_path.write_text(repaired_patch, encoding="utf-8")
                retry_sandbox = proof_dir / f"{safe_task}-verification-sandbox-{attempt}"
                retry_sandbox.mkdir(parents=True, exist_ok=True)
                verified = self.run_cmd(
                    sandbox_patch_command(
                        worktree, patch_path, retry_sandbox, verification_argv, profile, dependency_source,
                    ),
                    cwd=worktree, timeout=min(retry_timeout, profile.max_seconds),
                    pid_log=parent_ledger / "processes.tsv",
                )
                sandbox_dir = retry_sandbox
                repair_sandbox = retry_sandbox
                proposed = repaired
                model = repair
                if verified.rc == 0:
                    break
        (sandbox_dir / "runner.txt").write_text(
            (verified.stdout + "\n" + verified.stderr).strip() + "\n",
            encoding="utf-8",
        )
        changed_path = sandbox_dir / "changed-paths.txt"
        applied_path = sandbox_dir / "applied.patch"
        verification_rc = sandbox_dir / "verification.rc"
        paths = changed_path.read_text(encoding="utf-8").splitlines() if changed_path.exists() else []
        applied = applied_path.read_text(encoding="utf-8") if applied_path.exists() else ""
        applied_check = validate_patch(applied, candidate["files"], profile)
        after_rc = int(verification_rc.read_text(encoding="utf-8").strip()) if verification_rc.exists() else -1
        guards = list(applied_check.reasons)
        if not paths:
            guards.append("isolated runner did not report changed paths")
        if set(paths) != set(proposed.paths):
            guards.append("isolated runner changed a different file set")
        if verified.rc != 0 or after_rc != 0:
            guards.append("isolated verification did not pass")
        if strengthening:
            is_typescript = strengthening.get("analysis") == "typescript-regex"
            allowed_extensions = JS_EXTENSIONS if is_typescript else {".py"}
            if any(
                not is_test_path(path) or Path(path).suffix.lower() not in allowed_extensions
                for path in paths
            ):
                guards.append("test strengthening changed a non-test file")
            applied_host = self.run_cmd(["git", "apply", "--check", applied_path], cwd=worktree, timeout=30)
            if applied_host.rc != 0:
                guards.append("verified patch could not be replayed for invocation proof")
            else:
                replayed = self.run_cmd(["git", "apply", applied_path], cwd=worktree, timeout=30)
                count = (
                    javascript_symbol_call_count(
                        [worktree / path for path in candidate["files"]], strengthening["symbol"]
                    )
                    if is_typescript and replayed.rc == 0 else
                    owner_symbol_call_count(
                        [worktree / path for path in candidate["files"]],
                        strengthening["owner"], strengthening["symbol"],
                    ) if replayed.rc == 0 else None
                )
                if count is None or count <= 0:
                    guards.append(
                        "test strengthening did not add a proven target invocation"
                        if is_typescript else
                        "test strengthening did not add a proven owner-aware invocation"
                    )
                if (
                    not is_typescript and replayed.rc == 0 and count is not None
                    and candidate.get("semantic_contract")
                ):
                    try:
                        patched_texts = [
                            (worktree / path).read_text(encoding="utf-8") for path in candidate["files"]
                        ]
                    except (OSError, UnicodeError):
                        guards.append("patched tests could not be read for semantic proof")
                    else:
                        guards.extend(semantic_test_contract_reasons(
                            patched_texts, candidate["semantic_contract"],
                            strengthening["owner"], strengthening["symbol"],
                        ))
        status, proof_level = draft_proof_status(baseline.rc, after_rc, guards)
        record_state(
            lifecycle_path, fingerprint, "VERIFIED" if status != "REJECT" else "REJECTED",
            patch=str(applied_path if applied_path.exists() else patch_path), after_rc=after_rc, guards=guards,
            semantic_contract=candidate.get("semantic_contract") or {},
        )
        return finish({
            "status": status,
            "repo": repo_name,
            "source_ref": source_ref,
            "summary": candidate.get("summary", ""),
            "patch": str(applied_path if applied_path.exists() else patch_path),
            "verification": verification,
            "baseline_rc": baseline.rc,
            "after_rc": after_rc,
            "proof_level": proof_level,
            "patch_worker_rc": model.rc,
            "patch_lane": patch_lane,
            "files": list(proposed.paths),
            "verification_argv": list(verification_argv),
            "sandbox_rc": verified.rc,
            "sandbox_output": str(sandbox_dir / "runner.txt"),
            "guard_reasons": guards,
            "semantic_contract": candidate.get("semantic_contract") or {},
            "proof": str(proof_path),
        })
