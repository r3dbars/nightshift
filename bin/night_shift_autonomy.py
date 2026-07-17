"""Direct, fail-closed policy for autonomous Night Shift patches."""
from __future__ import annotations

import re
import shlex
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType


@dataclass(frozen=True)
class ChangePolicy:
    name: str
    allow_clean_baseline: bool
    allowed_file_kinds: tuple[str, ...]
    max_files: int
    max_changed_lines: int
    minimum_score: str
    prompt_rules: str


REPAIR_POLICY = ChangePolicy(
    name="repair",
    allow_clean_baseline=False,
    allowed_file_kinds=("source", "test"),
    max_files=4,
    max_changed_lines=300,
    minimum_score="MAYBE",
    prompt_rules=(
        "A failing baseline must reproduce before editing. Change only approved source or test files, "
        "repair the reproduced failure, and make the same approved verification pass."
    ),
)
TEST_STRENGTHENING_POLICY = ChangePolicy(
    name="test-strengthening",
    allow_clean_baseline=True,
    allowed_file_kinds=("test",),
    max_files=1,
    max_changed_lines=120,
    minimum_score="MAYBE",
    prompt_rules=(
        "Change exactly one approved test file. Add a focused behavioral assertion without changing "
        "source, dependencies, configuration, or policy."
    ),
)
EXPLICIT_TEST_MISSION_POLICY = ChangePolicy(
    name="explicit-test-mission",
    allow_clean_baseline=True,
    allowed_file_kinds=("test",),
    max_files=1,
    max_changed_lines=120,
    minimum_score="MAYBE",
    prompt_rules=(
        "Follow the explicit test mission in exactly one approved test file. Assert observable behavior "
        "and do not change source, dependencies, configuration, or policy."
    ),
)
E2E_STRENGTHENING_POLICY = ChangePolicy(
    name="e2e-strengthening",
    allow_clean_baseline=True,
    allowed_file_kinds=("e2e",),
    max_files=1,
    max_changed_lines=160,
    minimum_score="MAYBE",
    prompt_rules=(
        "Change exactly one approved end-to-end test file. Reuse the existing runner and fixtures; do "
        "not change product source, dependencies, configuration, credentials, or policy."
    ),
)
DOCS_REPAIR_POLICY = ChangePolicy(
    name="docs-repair",
    allow_clean_baseline=True,
    allowed_file_kinds=("docs",),
    max_files=2,
    max_changed_lines=120,
    minimum_score="MAYBE",
    prompt_rules=(
        "Change only approved documentation files. Keep claims grounded in the repository and do not "
        "change code, generated files, legal terms, security policy, dependencies, or configuration."
    ),
)
ISSUE_FIX_POLICY = ChangePolicy(
    name="issue-fix",
    allow_clean_baseline=True,
    allowed_file_kinds=("source", "test"),
    max_files=2,
    max_changed_lines=180,
    minimum_score="MAYBE",
    prompt_rules=(
        "Implement only the pinned issue's narrow acceptance criteria in at most two approved source or "
        "test files. Add no dependency and do not change configuration, generated files, or policy."
    ),
)
SAFE_REFACTOR_POLICY = ChangePolicy(
    name="safe-refactor",
    allow_clean_baseline=True,
    allowed_file_kinds=("source",),
    max_files=1,
    max_changed_lines=120,
    minimum_score="MAYBE",
    prompt_rules=(
        "Change exactly one approved source file. Preserve observable behavior and public interfaces; do "
        "not change tests, dependencies, configuration, generated files, or policy."
    ),
)
BLOCKED_POLICY = ChangePolicy(
    name="blocked",
    allow_clean_baseline=False,
    allowed_file_kinds=(),
    max_files=0,
    max_changed_lines=0,
    minimum_score="KEEP",
    prompt_rules="No autonomous patch is authorized for this task.",
)

# Short aliases keep callers readable while the *_POLICY names remain explicit.
REPAIR = REPAIR_POLICY
TEST_STRENGTHENING = TEST_STRENGTHENING_POLICY
EXPLICIT_TEST_MISSION = EXPLICIT_TEST_MISSION_POLICY
E2E_STRENGTHENING = E2E_STRENGTHENING_POLICY
DOCS_REPAIR = DOCS_REPAIR_POLICY
ISSUE_FIX = ISSUE_FIX_POLICY
SAFE_REFACTOR = SAFE_REFACTOR_POLICY

POLICIES = MappingProxyType(
    {
        policy.name: policy
        for policy in (
            REPAIR_POLICY,
            TEST_STRENGTHENING_POLICY,
            EXPLICIT_TEST_MISSION_POLICY,
            E2E_STRENGTHENING_POLICY,
            DOCS_REPAIR_POLICY,
            ISSUE_FIX_POLICY,
            SAFE_REFACTOR_POLICY,
        )
    }
)
CHANGE_POLICIES = POLICIES


_FORBIDDEN_SEGMENTS = {
    ".git",
    ".github",
    ".gitlab",
    ".night-shift",
    ".venv",
    "build",
    "coverage",
    "dist",
    "generated",
    "migrations",
    "node_modules",
    "vendor",
}
_FORBIDDEN_NAMES = {
    ".night-shift.json",
    "agents.md",
    "cargo.lock",
    "cargo.toml",
    "claude.md",
    "codeowners",
    "composer.json",
    "composer.lock",
    "dockerfile",
    "gemfile",
    "gemfile.lock",
    "go.mod",
    "go.sum",
    "justfile",
    "makefile",
    "package-lock.json",
    "package.json",
    "package.resolved",
    "pnpm-lock.yaml",
    "poetry.lock",
    "podfile",
    "podfile.lock",
    "procfile",
    "pyproject.toml",
    "requirements.txt",
    "safety.md",
    "security.md",
    "setup.cfg",
    "setup.py",
    "tox.ini",
    "uv.lock",
    "yarn.lock",
}
_E2E_SEGMENTS = {"cypress", "e2e", "end-to-end", "end_to_end", "playwright"}
_TEST_SEGMENTS = {"__tests__", "spec", "specs", "test", "testing", "tests"}
_DOC_SEGMENTS = {"doc", "docs", "documentation"}
_DOC_SUFFIXES = {".adoc", ".md", ".mdx", ".rst", ".txt"}
_DOC_NAMES = {
    "changelog",
    "code_of_conduct",
    "contributing",
    "readme",
}
_SOURCE_SUFFIXES = {
    ".c",
    ".cc",
    ".clj",
    ".cpp",
    ".cs",
    ".css",
    ".ex",
    ".exs",
    ".go",
    ".h",
    ".hpp",
    ".html",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".kts",
    ".m",
    ".mm",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".scss",
    ".sh",
    ".sql",
    ".svelte",
    ".swift",
    ".ts",
    ".tsx",
    ".vue",
}
_SOURCE_ROOTS = {"app", "bin", "lib", "packages", "scripts", "src"}
_AUTHORITY_SCRIPT = re.compile(
    r"(?:^|[._-])(?:appcast|cask|deploy|notarize|publish|release)(?:[._-]|$)",
    re.IGNORECASE,
)
_SCORE_ORDER = {"REJECT": 0, "MAYBE": 1, "KEEP": 2}
_SHELL_METACHARACTERS = re.compile(r"[;&|<>`$(){}\\*?\[\]~!#]|[\x00-\x1f\x7f]")
_INFRASTRUCTURE_MARKERS = (
    "command not found",
    "executable file not found",
    "cannot stat '/source/.'",
    "source mount is empty",
    "permission denied",
    "no such image",
    "no tests ran",
    "no tests collected",
)
_TEST_FAILURE = re.compile(
    r"\b(?:assertionerror|[1-9]\d*\s+(?:tests?\s+)?failed|failures?=[1-9]\d*|"
    r"[1-9]\d*\s+failing|test result:\s*failed|test suite .+ failed)\b|^FAIL:|^FAILED ",
    re.IGNORECASE | re.MULTILINE,
)
_FAILURE_ID = re.compile(
    r"^(?:FAILED\s+\S+|FAIL:\s+\S+|\S.*\s+\.\.\.\s+FAIL(?:ED)?)",
    re.IGNORECASE,
)
_ASSERTION_DETAIL = re.compile(
    r"\b(?:AssertionError|assertion failed|XCTAssert\w* failed|expected .+ (?:but|got|received))\b",
    re.IGNORECASE,
)
_PROCESS_OR_SECRET_ACCESS = re.compile(
    r"\b(?:subprocess\.|child_process|process\.env|os\.environ|os\.(?:system|popen|getenv)\s*\(|"
    r"Deno\.env|System\.getenv|Runtime\.getRuntime|ProcessBuilder|eval\s*\(|exec\s*\(|"
    r"GITHUB_ACTIONS|CI_ONLY)\b",
    re.IGNORECASE,
)
_NETWORK_ACCESS = re.compile(
    r"\b(?:requests\.(?:get|post|put|patch|delete)|urllib\.|socket\.|fetch\s*\(|"
    r"XMLHttpRequest|https?\.request|URLSession\.)",
    re.IGNORECASE,
)
_RELEASE_ACTION = re.compile(
    r"\b(?:deploy|publish|release|notarize|upload_artifact)\s*\(|"
    r"\b(?:gh\s+release|npm\s+publish|cargo\s+publish|twine\s+upload|"
    r"docker\s+push|git\s+tag|kubectl\s+apply|vercel\s+deploy|"
    r"xcrun\s+notarytool)\b",
    re.IGNORECASE,
)


def classify_path(path: str) -> str:
    """Classify one safe repository-relative file path."""
    if not isinstance(path, str) or not path or path != path.strip():
        return "forbidden"
    if path.startswith(("/", "~")) or "\\" in path or path.endswith("/"):
        return "forbidden"
    raw_parts = path.split("/")
    if any(not part or part in {".", ".."} for part in raw_parts):
        return "forbidden"

    parts = tuple(part.lower() for part in raw_parts)
    original_name = raw_parts[-1]
    name = parts[-1]
    _stem, dot, suffix = name.rpartition(".")
    extension = f".{suffix}" if dot else ""

    if any(part in _FORBIDDEN_SEGMENTS for part in parts):
        return "forbidden"
    if (
        name in _FORBIDDEN_NAMES
        or (extension in _SOURCE_SUFFIXES and _AUTHORITY_SCRIPT.search(name))
        or name.startswith(".env")
        or name.endswith((".lock", ".min.js", ".min.css"))
        or ".generated." in name
        or name.startswith("license")
        or name.startswith("requirements-")
        or name.endswith((".pem", ".key", ".p12", ".pfx"))
    ):
        return "forbidden"

    if (
        any(part in _E2E_SEGMENTS for part in parts[:-1])
        or re.search(r"(?:^|[._-])(?:e2e|end[._-]?to[._-]?end|integration)(?:[._-]|$)", name)
        or name.endswith((".cy.js", ".cy.jsx", ".cy.ts", ".cy.tsx"))
    ):
        return "e2e"
    if any(part in _TEST_SEGMENTS for part in parts[:-1]):
        return "test"
    if any(part in _DOC_SEGMENTS for part in parts[:-1]):
        return "docs"
    if extension in _DOC_SUFFIXES or name.split(".", 1)[0] in _DOC_NAMES:
        return "docs"
    if (
        name.startswith("test_")
        or re.search(r"(?:[._-](?:test|tests|spec))\.[^.]+$", name)
        or re.search(r"(?:Test|Tests)\.[^.]+$", original_name)
    ):
        return "test"
    if extension in _SOURCE_SUFFIXES:
        return "source"
    if not extension and parts[0] in _SOURCE_ROOTS:
        return "source"
    return "forbidden"


def policy_for_candidate(candidate: Mapping[str, object]) -> ChangePolicy:
    """Return only a controller-bound policy; unknown work cannot execute."""
    raw_intent = candidate.get("draft_intent")
    intent = str(raw_intent or "").strip().lower().replace("_", "-")
    if intent in POLICIES:
        return POLICIES[intent]
    if (
        not intent
        and candidate.get("kind") == "mission"
        and candidate.get("proof_kind") == "test"
        and bool(candidate.get("semantic_contract"))
    ):
        return EXPLICIT_TEST_MISSION_POLICY
    return BLOCKED_POLICY


def policy_accepts_files(policy: ChangePolicy, files: Iterable[str]) -> bool:
    """Check a non-empty set of changed files against one policy."""
    try:
        paths = tuple(files)
    except TypeError:
        return False
    if not paths or len(paths) > policy.max_files:
        return False
    if not all(isinstance(path, str) for path in paths):
        return False
    if len(set(paths)) != len(paths):
        return False
    return all(classify_path(path) in policy.allowed_file_kinds for path in paths)


def clean_baseline_allowed(candidate: Mapping[str, object]) -> bool:
    return policy_for_candidate(candidate).allow_clean_baseline


def patch_limits(candidate: Mapping[str, object]) -> tuple[int, int]:
    policy = policy_for_candidate(candidate)
    return policy.max_files, policy.max_changed_lines


def candidate_prompt_rules(candidate: Mapping[str, object]) -> str:
    return policy_for_candidate(candidate).prompt_rules


def candidate_score_allowed(candidate: Mapping[str, object]) -> bool:
    policy = policy_for_candidate(candidate)
    score = str(candidate.get("score") or "").strip().upper()
    return _SCORE_ORDER.get(score, -1) >= _SCORE_ORDER[policy.minimum_score]


def verification_outcome(rc: int, output: str) -> str:
    """Classify a check without treating arbitrary nonzero exits as test failures."""
    if rc == 0:
        return "PASS"
    text = str(output or "")
    lowered = text.lower()
    if rc in {125, 126, 127, 137} or any(marker in lowered for marker in _INFRASTRUCTURE_MARKERS):
        return "BLOCKED"
    return "FAILING" if _TEST_FAILURE.search(text) else "BLOCKED"


def test_failure_signature(output: str) -> str:
    """Return a stable, test-specific signature for a classified failure."""
    identifiers: list[str] = []
    assertions: list[str] = []
    for raw in str(output or "").splitlines():
        line = " ".join(raw.strip().split())[:500]
        if not line:
            continue
        if _FAILURE_ID.search(line):
            identifiers.append(line)
        elif _ASSERTION_DETAIL.search(line):
            assertions.append(line)
    selected = identifiers[:10] + assertions[:10]
    return "\n".join(selected)


def patch_risk_reasons(candidate: Mapping[str, object], patch: str) -> tuple[str, ...]:
    """Reject new privileged behavior even when it appears in an allowed file."""
    policy = policy_for_candidate(candidate)
    if policy is DOCS_REPAIR_POLICY:
        return ()
    additions = "\n".join(
        line[1:] for line in str(patch or "").splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    reasons: list[str] = []
    if _PROCESS_OR_SECRET_ACCESS.search(additions):
        reasons.append("patch adds process, environment, secret, or dynamic-code access")
    if _RELEASE_ACTION.search(additions):
        reasons.append("patch adds a release, deploy, publish, or notarization action")
    if policy in {REPAIR_POLICY, ISSUE_FIX_POLICY, SAFE_REFACTOR_POLICY} and _NETWORK_ACCESS.search(additions):
        reasons.append("source patch adds new network access")
    return tuple(reasons)


def _approved_argv(command: Sequence[str] | str) -> tuple[str, ...]:
    if isinstance(command, str):
        try:
            return tuple(shlex.split(command, posix=True))
        except ValueError:
            return ()
    try:
        argv = tuple(command)
    except TypeError:
        return ()
    return argv if argv and all(isinstance(part, str) and part for part in argv) else ()


def select_approved_verification(
    candidate: Mapping[str, object],
    approved_commands: Iterable[Sequence[str] | str],
) -> tuple[str, ...]:
    """Select an exact approved argv command without interpreting shell syntax."""
    approved = tuple(_approved_argv(command) for command in approved_commands)
    approved = tuple(command for command in approved if command)
    if not approved:
        return ()

    proposed_argv = candidate.get("verification_argv")
    if isinstance(proposed_argv, Sequence) and not isinstance(proposed_argv, (str, bytes)):
        parsed_argv = _approved_argv(proposed_argv)
        return parsed_argv if parsed_argv in approved else ()

    proposed = candidate.get("verification")
    if not isinstance(proposed, str) or not proposed.strip() or _SHELL_METACHARACTERS.search(proposed):
        return ()
    try:
        parsed = tuple(shlex.split(proposed.strip(), comments=False, posix=True))
    except ValueError:
        return ()
    return parsed if parsed in approved else ()
