"""Validate model-produced patches before an isolated runner ever sees them."""
from __future__ import annotations

import ast
import difflib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from night_shift_policy import RepoProfile, path_is_allowed, path_is_protected


DIFF_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")
PATH_LINE = re.compile(r"^(---|\+\+\+) (?:a|b)/(.+)$")


@dataclass(frozen=True)
class PatchCheck:
    patch: str
    paths: tuple[str, ...]
    reasons: tuple[str, ...]

    @property
    def valid(self) -> bool:
        return bool(self.patch and self.paths and not self.reasons)


def extract_unified_diff(output: str) -> str:
    start = output.find("diff --git ")
    if start < 0:
        return ""
    patch = output[start:].strip()
    patch = patch.replace("```diff\n", "").replace("```\n", "")
    return patch + "\n"


def materialize_test_method_patch(output: str, original: str, relative: str) -> str:
    added = [line[1:] for line in output.splitlines() if line.startswith("+") and not line.startswith("+++")]
    start = next((index for index, line in enumerate(added) if re.match(r"^    def test_[A-Za-z0-9_]+\(self[^)]*\):$", line)), None)
    if start is None:
        return ""
    method = added[start:]
    while method and not method[-1].strip():
        method.pop()
    if not method or len(method) > 80 or any(re.match(r"^\s*(?:from\s+\S+\s+)?import\s+", line) for line in method):
        return ""
    try:
        tree = ast.parse("class _Generated:\n" + "\n".join(method) + "\n")
    except SyntaxError:
        return ""
    body = tree.body[0].body if tree.body and isinstance(tree.body[0], ast.ClassDef) else []
    if len(body) != 1 or not isinstance(body[0], ast.FunctionDef) or not body[0].name.startswith("test_"):
        return ""
    marker = original.rfind('\nif __name__ == "__main__":')
    if marker < 0:
        return ""
    revised = original[:marker].rstrip() + "\n\n" + "\n".join(method) + "\n" + original[marker:]
    unified = "".join(difflib.unified_diff(
        original.splitlines(keepends=True), revised.splitlines(keepends=True),
        fromfile=f"a/{relative}", tofile=f"b/{relative}", n=3,
    ))
    return f"diff --git a/{relative} b/{relative}\n{unified}" if unified else ""


def _safe_path(path: str) -> bool:
    pure = Path(path)
    return bool(path) and not pure.is_absolute() and ".." not in pure.parts and "\\" not in path


def validate_patch(
    output: str,
    allowed_files: list[str],
    profile: RepoProfile,
    max_changed_lines: int = 500,
) -> PatchCheck:
    patch = extract_unified_diff(output)
    reasons: list[str] = []
    if not patch:
        return PatchCheck("", (), ("model did not return a unified diff",))
    if len(patch.encode("utf-8")) > 180_000:
        reasons.append("patch exceeds 180 KB")
    if "GIT binary patch" in patch or "new file mode" in patch or "deleted file mode" in patch:
        reasons.append("binary, added, and deleted files are not permitted overnight")
    paths: list[str] = []
    before_paths: list[str] = []
    after_paths: list[str] = []
    has_hunk = False
    for line in patch.splitlines():
        match = DIFF_HEADER.match(line)
        if match:
            before, after = match.groups()
            if before != after or not _safe_path(before):
                reasons.append("patch contains an unsafe rename or path")
            else:
                paths.append(before)
        path_match = PATH_LINE.match(line)
        if path_match:
            marker, path = path_match.groups()
            if not _safe_path(path):
                reasons.append("patch contains an unsafe file header")
            (before_paths if marker == "---" else after_paths).append(path)
        if line.startswith("@@"):
            has_hunk = True
    paths = list(dict.fromkeys(paths))
    if not paths:
        reasons.append("patch has no file headers")
    if not before_paths or not after_paths or before_paths != after_paths:
        reasons.append("patch needs matching --- and +++ file headers")
    if before_paths != paths or after_paths != paths:
        reasons.append("patch file headers must match diff --git paths")
    if not has_hunk:
        reasons.append("patch has no hunk header")
    if len(paths) > 6:
        reasons.append("patch touches more than six files")
    allowed = set(allowed_files)
    for path in paths:
        if path not in allowed:
            reasons.append(f"patch touches unapproved file: {path}")
        if path_is_protected(path, profile.protected_paths):
            reasons.append(f"patch touches immutable file: {path}")
        if not path_is_allowed(path, profile.allowed_paths):
            reasons.append(f"patch touches path outside repo allowlist: {path}")
    changed = sum(1 for line in patch.splitlines() if line.startswith(("+", "-")) and not line.startswith(("+++", "---")))
    if changed > max_changed_lines:
        reasons.append("patch exceeds 500 changed lines")
    hunks: list[tuple[list[str], list[str]]] = []
    removed: list[str] | None = None
    added: list[str] | None = None
    for line in patch.splitlines():
        if line.startswith("@@"):
            removed, added = [], []
            hunks.append((removed, added))
        elif removed is not None and line.startswith("-") and not line.startswith("---"):
            removed.append(line[1:])
        elif added is not None and line.startswith("+") and not line.startswith("+++"):
            added.append(line[1:])
    if hunks and all(removed and added and removed == added for removed, added in hunks):
        reasons.append("patch makes no textual change")
    additions = "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
    if re.search(r"(?i)(api[_-]?key|secret|password|private[_-]?key)\s*[:=]", additions):
        reasons.append("patch appears to add a secret")
    if re.search(r"(?i)(allowlist|allow_list|ignore|skip|disable).{0,80}(check|test|lint|security|policy)", additions):
        reasons.append("patch appears to bypass a check or policy")
    return PatchCheck(patch, tuple(paths), tuple(dict.fromkeys(reasons)))


def patch_prompt(candidate: dict, source_excerpt: str, command: tuple[str, ...]) -> str:
    contract = candidate.get("strengthening_contract") or {}
    semantic = candidate.get("semantic_contract") or {}
    semantic_guidance: list[str] = []
    if semantic.get("minimum_target_invocations"):
        semantic_guidance.append(
            f"Invoke the target at least {semantic['minimum_target_invocations']} times in the test."
        )
    if semantic.get("required_boolean_outcomes") == [True, False]:
        semantic_guidance.append(
            "Arrange distinct fake or fixture preconditions so one target invocation actually returns True "
            "and another actually returns False, then assert each result; do not reuse an unchanged fake."
        )
    if len(semantic.get("ordered_terms") or []) == 2:
        first, second = semantic["ordered_terms"]
        semantic_guidance.append(
            f"Record calls and assert {first} occurs before {second} using separate ordered assertions."
        )
    if candidate.get("draft_intent") == "test-strengthening":
        edit_policy = (
            "You may modify only an existing allowed TEST file. Add a focused behavioral test "
            "that invokes the exact owner and symbol in the strengthening contract. Do not change "
            "source, manifests, lockfiles, workflows, configuration, secrets, dependencies, or policy. "
            "Reuse existing imports and test helpers; add no dependency. Assert exact observed call order, "
            "arguments, and both requested outcomes. Use an exact unchanged insertion anchor shown in SOURCE "
            "EXCERPT, preferably near the test file tail. Keep the patch under 80 changed lines."
        )
    else:
        edit_policy = (
            "You may modify only an existing allowed file. Do not change tests, manifests, "
            "lockfiles, workflows, configuration, secrets, dependencies, or policy."
        )
    return f"""ROLE: isolated patch author. Return ONLY a standard unified git diff.
TASK: {candidate.get('summary', '')}
EVIDENCE: {candidate.get('evidence', '')}
EXPECTED RESULT: {candidate.get('expected_result', '')}
STRENGTHENING CONTRACT: {contract.get('owner', '')}.{contract.get('symbol', '')}
SEMANTIC CONTRACT: {json.dumps(semantic, sort_keys=True)}
SEMANTIC PROOF REQUIREMENTS: {' '.join(semantic_guidance) or 'none'}
ALLOWED FILES: {', '.join(candidate.get('files', []))}
VERIFICATION ARGV: {' '.join(command)}
SOURCE EXCERPT:
{source_excerpt[:24000]}

{edit_policy} Do not
include prose, markdown fences, commands, or explanations. If a safe patch is
not possible, return an empty response."""
