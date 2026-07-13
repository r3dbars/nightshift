"""Validate model-produced patches before an isolated runner ever sees them."""
from __future__ import annotations

import ast
import difflib
import json
import os
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


def typescript_import_path(source_file: str, test_file: str) -> str:
    source = Path(source_file).with_suffix("")
    relative = os.path.relpath(source, Path(test_file).parent).replace(os.sep, "/")
    return relative if relative.startswith(".") else "./" + relative


def extract_unified_diff(output: str) -> str:
    start = output.find("diff --git ")
    if start >= 0:
        patch = output[start:].strip()
    else:
        cleaned = output.replace("```diff\n", "").replace("```\n", "").strip()
        pairs = re.findall(r"(?m)^--- (?:a/)?([^\n]+)\n\+\+\+ (?:b/)?([^\n]+)$", cleaned)
        if len(pairs) != 1 or pairs[0][0] != pairs[0][1]:
            return ""
        path = pairs[0][0]
        normalized = re.sub(
            r"(?m)^--- (?:a/)?[^\n]+\n\+\+\+ (?:b/)?[^\n]+$",
            f"--- a/{path}\n+++ b/{path}", cleaned, count=1,
        )
        patch = f"diff --git a/{path} b/{path}\n{normalized}"
    patch = patch.replace("```diff\n", "").replace("```\n", "")
    patch = "\n".join(
        "+" if line.startswith("+") and line[1:].strip() == "" else line
        for line in patch.splitlines()
    )
    return patch + "\n"


def materialize_test_method_patch(
    output: str, original: str, relative: str,
    allowed_import_modules: set[str] | None = None,
) -> str:
    added = [line[1:] for line in output.splitlines() if line.startswith("+") and not line.startswith("+++")]
    start = next((index for index, line in enumerate(added) if re.match(r"^    def test_[A-Za-z0-9_]+\(self[^)]*\):$", line)), None)
    if start is None:
        return ""
    if any(line.strip() for line in added[:start]):
        return ""
    end = next(
        (
            index for index in range(start + 1, len(added))
            if re.match(r"^    def test_[A-Za-z0-9_]+\(self[^)]*\):$", added[index])
        ),
        len(added),
    )
    method = added[start:end]
    while method and not method[-1].strip():
        method.pop()
    if not method or len(method) > 80:
        return ""
    try:
        tree = ast.parse("class _Generated:\n" + "\n".join(method) + "\n")
    except SyntaxError:
        return ""
    body = tree.body[0].body if tree.body and isinstance(tree.body[0], ast.ClassDef) else []
    if len(body) != 1 or not isinstance(body[0], ast.FunctionDef) or not body[0].name.startswith("test_"):
        return ""
    allowed = set(allowed_import_modules or ())
    dynamic_names = {
        "__builtins__", "__import__", "builtins", "compile", "eval", "exec",
        "getattr", "globals", "locals", "vars",
    }
    for node in ast.walk(body[0]):
        if isinstance(node, ast.Name) and node.id in dynamic_names:
            return ""
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value in dynamic_names:
            return ""
        if isinstance(node, ast.Import):
            return ""
        if isinstance(node, ast.ImportFrom) and (
            node.level != 0
            or node.module not in allowed
            or any(alias.name == "*" for alias in node.names)
        ):
            return ""
        if isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name) and function.id in {
                "__import__", "compile", "eval", "exec"
            }:
                return ""
            if isinstance(function, ast.Attribute) and function.attr in {
                "__import__", "import_module"
            }:
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


def materialize_ts_test_case_patch(
    output: str, original: str, relative: str, symbol: str,
    expected_import: str | None = None,
) -> str:
    """Extract one conservative Vitest/Jest test block into an existing suite."""
    added = [
        line[1:] for line in output.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    ]
    start = next(
        (
            index for index, line in enumerate(added)
            if re.match(r"^\s*(?:it|test)\s*\(", line)
        ),
        None,
    )
    if start is None:
        return ""
    if any(line.strip() for line in added[:start]):
        return ""
    block: list[str] = []
    brace_depth = 0
    opened = False
    end = None
    for index in range(start, len(added)):
        line = added[index]
        block.append(line)
        code = re.sub(r"(['\"])(?:\\.|(?!\1)[^\\])*\1", "", line)
        brace_depth += code.count("{") - code.count("}")
        opened = opened or "{" in code
        if opened and brace_depth == 0 and re.search(r"}\s*\)\s*;?\s*$", code):
            end = index
            break
    if end is None or len(block) > 60:
        return ""
    if any(line.strip() for line in added[end + 1:]):
        return ""
    if not re.search(rf"(?:\b{re.escape(symbol)}|\.{re.escape(symbol)})\s*\(", "\n".join(block)):
        return ""
    block_text = "\n".join(block)
    if re.search(r"(?m)^\s*import\s+|\brequire\s*\(", block_text):
        return ""
    if expected_import:
        imported = rf"await\s+import\(\s*['\"]{re.escape(expected_import)}['\"]\s*\)"
        if not re.search(imported, block_text):
            return ""
        destructured = rf"(?:const|let|var)\s*\{{\s*{re.escape(symbol)}\s*\}}\s*=\s*{imported}"
        namespace = rf"(?:const|let|var)\s+(?P<module>[A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*{imported}"
        if not re.search(destructured, block_text):
            namespace_match = re.search(namespace, block_text)
            if not namespace_match or not re.search(
                rf"\b{re.escape(namespace_match.group('module'))}\s*\.\s*{re.escape(symbol)}\s*\(",
                block_text,
            ):
                return ""
    if re.search(
        r"(?i)\b(?:child_process|exec|spawn|eval|function\s*\(|process\.|fs\.|writefile|unlink|rm\s+-rf)\b",
        "\n".join(block),
    ):
        return ""
    marker = original.rfind("\n});")
    if marker < 0:
        marker = original.rfind("\n})")
    if marker < 0:
        return ""
    revised = original[:marker].rstrip() + "\n\n" + "\n".join(block) + "\n" + original[marker:]
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
    owner = str(contract.get("owner") or "")
    owner = "" if owner == "none" else owner
    symbol = str(contract.get("symbol") or "")
    source_module = Path(str(contract.get("source_file") or "")).stem
    is_typescript = contract.get("analysis") == "typescript-regex"
    if is_typescript and symbol and candidate.get("files") and contract.get("source_file"):
        test_path = Path(str(candidate["files"][0]))
        source_path = Path(str(contract["source_file"]))
        import_path = typescript_import_path(str(source_path), str(test_path))
        import_guidance = (
            f"Inside the new test block, dynamically import the exact source module with "
            f"`const {{ {symbol} }} = await import('{import_path}')`; call `{symbol}` from that binding. "
            "Do not add a module-scope import. "
        )
    else:
        import_guidance = (
        f"If {owner} is not already imported, put `from {source_module} import {owner}` inside the new test method; "
        "do not edit global imports. "
        if owner and source_module else
        f"If {symbol} is not already imported, put `from {source_module} import {symbol}` inside the new test method; "
        "do not add imports at module or class scope. "
        if symbol and source_module else
        "If the target owner is not already imported, import it from the exact source module inside the new test method; do not edit global imports. "
        )
    semantic_guidance: list[str] = []
    if semantic.get("minimum_target_invocations"):
        semantic_guidance.append(
            f"Invoke the target at least {semantic['minimum_target_invocations']} times in the test."
        )
    if symbol:
        signature_scope = ""
        owner = str(contract.get("owner") or "")
        owner = "" if owner == "none" else owner
        if owner:
            owner_class = re.search(
                rf"(?m)^(?P<indent>[ \t]*)class\s+{re.escape(owner)}\b.*$",
                source_excerpt,
            )
            if owner_class:
                indent = owner_class.group("indent")
                owner_start = owner_class.start()
                tail_start = source_excerpt.find("\n", owner_class.end())
                tail_start = len(source_excerpt) if tail_start < 0 else tail_start + 1
                tail = source_excerpt[tail_start:]
                boundary = len(tail)
                for line_match in re.finditer(r"(?m)^[^\n]*", tail):
                    line = line_match.group(0)
                    if not line.strip():
                        continue
                    leading = len(line) - len(line.lstrip(" \t"))
                    if leading <= len(indent):
                        boundary = line_match.start()
                        break
                signature_scope = source_excerpt[owner_start:tail_start + boundary]
        else:
            signature_scope = source_excerpt
        signature_pattern = (
            rf"\b(?:async\s+)?def\s+{re.escape(symbol)}\s*\(.*?\)\s*(?:->\s*[^:]+)?\s*:"
            if owner else
            rf"(?m)^\s*(?:export\s+)?(?:async\s+)?(?:def\s+{re.escape(symbol)}\s*\(.*?\)\s*(?:->\s*[^:]+)?\s*:|function\s+{re.escape(symbol)}\s*\([^)]*\)\s*(?::[^{{]+)?\s*\{{|(?:const|let|var)\s+{re.escape(symbol)}\s*=)"
            if is_typescript else
            rf"(?m)^(?:async\s+)?def\s+{re.escape(symbol)}\s*\(.*?\)\s*(?:->\s*[^:]+)?\s*:"
        )
        signature = re.search(
            signature_pattern,
            signature_scope,
            re.DOTALL,
        )
        if signature:
            signature_text = " ".join(signature.group(0).split()).replace("( ", "(").replace(" )", ")")
            semantic_guidance.append(
                f"Invoke the target using this exact pinned signature: {signature_text}. "
                "Provide every required argument; do not omit parameters or guess a shorter call."
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
        if is_typescript:
            edit_policy = (
                "You may modify only one existing allowed TypeScript or JavaScript TEST file. Add exactly one focused "
                "Vitest/Jest `it(...)` or `test(...)` block inside the existing suite. Dynamically import the exact "
                "source module inside that block, call the exported target, and assert an observable result. Do not "
                "change source, manifests, lockfiles, workflows, configuration, secrets, dependencies, or policy. "
                "Do not add module-scope imports, filesystem or process side effects, network calls, database access, "
                "shell commands, or new dependencies. Keep the patch under 60 added lines. "
                + import_guidance
            )
        else:
            edit_policy = (
            "You may modify only an existing allowed TEST file. Add a focused behavioral test "
            "that invokes the exact owner and symbol in the strengthening contract. Do not change "
            "source, manifests, lockfiles, workflows, configuration, secrets, dependencies, or policy. "
            "Reuse existing imports and test helpers; add no dependency. Use the exact constructor and method "
            "signatures shown in SOURCE EXCERPT; do not monkeypatch attributes that the class does not define. "
            "Fake command results must expose the exact attributes read by source, such as rc rather than a dict. "
            "For fake command results, use an object with attributes such as `SimpleNamespace(rc=0)` and reuse the "
            "existing test import; never return a dict like `{'rc': 0}`. "
            + import_guidance
            + "Any new import must be inside the new test method; the isolated materializer retains only that method, not module or class-scope imports. "
            + "For parser tests, follow the exact source branches shown in SOURCE EXCERPT: assert empty for malformed or mismatched inputs when the source returns empty, and do not invent normalization behavior that the source does not implement. "
            + "If the source return annotation is bool, assert the returned value directly with assertTrue or assertFalse; "
            "do not read attributes such as rc from that boolean. A fake command runner does not create filesystem "
            "side effects unless the fake explicitly implements them, so prove behavior from its recorded calls. "
            "When testing command arguments, record the incoming command itself (for example `calls.append(list(cmd))`) "
            "before returning the fake result; never inspect the result object for command arguments. "
            "Command argv lists may contain Path objects. Compare the complete list to an exact expected list, such as "
            "['git', 'worktree', 'remove', '--force', worktree], and do not apply string membership tests to each raw argument. "
            "Preserve exact argument types: compare a Path as a Path unless source explicitly converts it. "
            "For output-parsing tests, include every expected positive fixture in the sample output before asserting a non-empty result; "
            "to prove deduplication and a maximum limit, include enough matching fixtures to exercise both behaviors and assert the exact ordered result. "
                "Assert exact observed call order, arguments, and both requested outcomes. Use an exact unchanged insertion anchor shown in SOURCE "
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
