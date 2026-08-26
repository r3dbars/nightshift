"""Repository scan, test-command detection, and scan artifacts."""
from __future__ import annotations

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from night_shift_paths import cli_attr, cli_module
from night_shift_policy import command_display
from night_shift_portfolio import parse_json_text
from night_shift_queue import is_test_path
from night_shift_redaction import redact
from night_shift_runtime import run_cmd as _default_run_cmd


def run_cmd(*args, **kwargs):
    return cli_attr("run_cmd", _default_run_cmd)(*args, **kwargs)


def repo_slug(repo):
    cli = cli_module()
    if cli is None:
        raise RuntimeError("night_shift_cli is not loaded")
    return cli.repo_slug(repo)


def repo_context_pack(repo: Path | None) -> str:
    if not repo or not repo.exists():
        return "No repo context. The project path was missing or not provided."

    sections: list[tuple[str, str]] = []
    commands = [
        ("head", ["git", "-C", repo, "log", "--oneline", "--decorate", "--max-count=15"]),
        ("status", ["git", "-C", repo, "status", "--short"]),
        ("branches", ["git", "-C", repo, "branch", "--show-current"]),
        ("recent-files", ["git", "-C", repo, "diff", "--name-only", "HEAD~10..HEAD"]),
    ]
    for title, cmd in commands:
        res = run_cmd(cmd, timeout=40)
        sections.append((title, (res.stdout or res.stderr).strip()))

    if shutil.which("gh"):
        prs = run_cmd(
            [
                "gh",
                "pr",
                "list",
                "--limit",
                "40",
                "--json",
                "number,title,isDraft,mergeStateStatus,headRefName,updatedAt,reviewDecision,statusCheckRollup,files,url",
            ],
            cwd=repo,
            timeout=60,
        )
        sections.append(("github-open-prs", (prs.stdout or prs.stderr).strip()))

    if shutil.which("rg"):
        todo = run_cmd(["rg", "-n", "TODO|FIXME|HACK|XXX", str(repo), "--glob", "!build/**"], timeout=60)
        sections.append(("todo-fixme-sample", "\n".join((todo.stdout or todo.stderr).splitlines()[:80])))

    tracked = run_cmd(["git", "-C", repo, "ls-files"], timeout=60)
    files = tracked.stdout.splitlines()
    interesting = [f for f in files if f.endswith((".swift", ".md", ".yml", ".yaml", ".py", ".sh"))]
    sections.append(("tracked-file-sample", "\n".join(interesting[:220])))

    body = []
    for title, content in sections:
        body.append(f"## {title}\n{content or '(empty)'}")
    return "\n\n".join(body)

def command_lines(repo: Path, commands: list[list[str]], timeout=60) -> list[dict]:
    rows: list[dict] = []
    for cmd in commands:
        res = run_cmd(cmd, cwd=repo, timeout=timeout)
        rows.append(
            {
                "command": " ".join(str(part) for part in cmd),
                "rc": res.rc,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
            }
        )
    return rows

def repo_signal_scan(repo: Path | None) -> dict:
    if not repo or not repo.exists():
        return {"status": "missing", "message": "repo path missing or not provided"}

    scan: dict = {
        "status": "ok",
        "repo": str(repo),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    commands = command_lines(
        repo,
        [
            ["git", "rev-parse", "HEAD"],
            ["git", "branch", "--show-current"],
            ["git", "status", "--short"],
            ["git", "diff", "--name-only", "HEAD~10..HEAD"],
            ["git", "ls-files"],
        ],
        timeout=60,
    )
    scan["git"] = commands
    scan["head"] = commands[0]["stdout"] if commands and commands[0]["rc"] == 0 else ""
    scan["branch"] = commands[1]["stdout"] if len(commands) > 1 and commands[1]["rc"] == 0 else ""
    scan["dirty_lines"] = commands[2]["stdout"].splitlines() if len(commands) > 2 and commands[2]["stdout"] else []
    recent_files = commands[3]["stdout"].splitlines()[:80] if len(commands) > 3 and commands[3]["stdout"] else []
    if not recent_files:
        recent = run_cmd(["git", "log", "--name-only", "--pretty=format:", "--max-count=10"], cwd=repo, timeout=60)
        recent_files = list(dict.fromkeys([line.strip() for line in recent.stdout.splitlines() if line.strip()]))[:80]
    scan["recent_files"] = recent_files
    tracked = commands[4]["stdout"].splitlines() if len(commands) > 4 and commands[4]["stdout"] else []
    scan["tracked_count"] = len(tracked)
    scan["tracked_files"] = tracked[:5000]
    scan["coverage_test_files"] = [path for path in tracked if is_test_path(path)]
    scan["doc_files"] = [f for f in tracked if f.lower().endswith((".md", ".mdx", ".rst"))][:60]
    scan["test_files"] = [
        f
        for f in tracked
        if re.search(r"(^|/)(test|tests|spec|specs)(/|$)|(_test|\.test|\.spec)\.", f, re.IGNORECASE)
    ][:80]
    scan["source_files"] = [
        f
        for f in tracked
        if f.endswith(
            (
                ".py",
                ".js",
                ".ts",
                ".tsx",
                ".jsx",
                ".swift",
                ".go",
                ".rs",
                ".rb",
                ".sh",
                ".java",
                ".kt",
                ".kts",
                ".c",
                ".cc",
                ".cpp",
                ".h",
                ".hpp",
                ".cs",
                ".php",
            )
        )
    ][:120]
    todo_sample: list[str] = []
    if shutil.which("rg"):
        todo = run_cmd(["rg", "-n", "TODO|FIXME|HACK|XXX", str(repo), "--glob", "!build/**"], timeout=60)
        todo_sample = todo.stdout.splitlines()[:80] if todo.stdout else []
    scan["todo_count_sample"] = len(todo_sample)
    scan["todo_sample"] = todo_sample
    scan["test_commands"] = detect_test_commands(repo, tracked)
    scan.update(detect_e2e_inventory(repo, tracked, scan["test_commands"]))
    scan["github_slug"] = repo_slug(repo)
    if shutil.which("gh"):
        prs = run_cmd(
            [
                "gh",
                "pr",
                "list",
                "--limit",
                "40",
                "--json",
                "number,title,isDraft,mergeStateStatus,headRefName,headRefOid,reviewDecision,statusCheckRollup,files,updatedAt,url",
            ],
            cwd=repo,
            timeout=60,
        )
        scan["github_open_prs_raw"] = prs.stdout.strip() if prs.rc == 0 else ""
        scan["github_open_prs_error"] = prs.stderr.strip() if prs.rc != 0 else ""
        issues = run_cmd(
            ["gh", "issue", "list", "--limit", "40", "--json", "number,title,body,labels,updatedAt,url"],
            cwd=repo,
            timeout=60,
        )
        scan["github_open_issues_raw"] = issues.stdout.strip() if issues.rc == 0 else ""
        failed_runs = run_cmd(
            ["gh", "run", "list", "--limit", "30", "--json", "databaseId,name,workflowName,headBranch,headSha,updatedAt,status,conclusion,url"],
            cwd=repo,
            timeout=60,
        )
        latest_runs: dict[str, dict] = {}
        for run in parse_json_text(failed_runs.stdout, []) if failed_runs.rc == 0 else []:
            key = f"{run.get('workflowName') or run.get('name')}:{run.get('headBranch')}"
            if key not in latest_runs:
                latest_runs[key] = run
        current_failures = [
            run for run in latest_runs.values()
            if run.get("status") == "completed" and run.get("conclusion") == "failure"
        ]
        scan["github_failed_runs_raw"] = json.dumps(current_failures)
        failed_logs: list[dict] = []
        for run in parse_json_text(scan["github_failed_runs_raw"], [])[:2]:
            database_id = run.get("databaseId")
            if not database_id:
                continue
            logs = run_cmd(["gh", "run", "view", str(database_id), "--log-failed"], cwd=repo, timeout=120)
            failed_logs.append(
                {
                    "run": run,
                    "log": extract_github_actions_failure_evidence(logs.stdout or logs.stderr)[-24000:],
                    "log_rc": logs.rc,
                }
            )
        scan["github_failed_logs_raw"] = json.dumps(failed_logs)
    return scan

def detect_test_commands(repo: Path, tracked: list[str], source_ref: str = "") -> list[str]:
    """Return display-only suggestions, never commands Night Shift may execute.

    Repositories control package scripts, Makefiles, and shell files. Actual
    execution requires an explicitly approved argv profile and a rootless sandbox.
    """
    commands: list[str] = []
    names = set(tracked)

    def read_text(relative: str) -> str:
        if source_ref:
            shown = run_cmd(["git", "show", f"{source_ref}:{relative}"], cwd=repo, timeout=30)
            if shown.rc != 0:
                raise OSError(shown.stderr or shown.stdout)
            return shown.stdout
        return (repo / relative).read_text(encoding="utf-8")

    if "package.json" in names:
        try:
            package = json.loads(read_text("package.json"))
            scripts = package.get("scripts", {})
            named_checks = [
                script
                for script in scripts
                if re.search(r"(^|:)(test|lint|typecheck|check|verify)(:|$)", script, re.IGNORECASE)
            ]
            behavioral_scripts = [
                script for script in ("test", *sorted(named_checks))
                if script in scripts and (script == "test" or script.startswith("test:"))
            ]
            behavioral_scripts.sort(
                key=lambda script: verification_command_priority(["npm", "run", script])
            )
            static_scripts = [
                script for script in ("lint", "typecheck", "check", "verify", *sorted(named_checks))
                if script in scripts and script not in behavioral_scripts
            ]
            ordered_scripts = list(dict.fromkeys([*behavioral_scripts, *static_scripts]))
            for script in ordered_scripts[:24]:
                if not re.fullmatch(r"[A-Za-z0-9:_-]+", script):
                    continue
                if "pnpm-lock.yaml" in names:
                    commands.append(f"pnpm run {script}")
                elif "yarn.lock" in names:
                    commands.append(f"yarn {script}")
                else:
                    commands.append(f"npm run {script}")
        except Exception:
            commands.append("npm test")
    if "pyproject.toml" in names or "pytest.ini" in names:
        commands.append("python -m pytest")
    elif any(path.startswith("tests/") and path.endswith(".py") for path in names):
        commands.append("python3 -m unittest discover -s tests -p 'test_*.py'")
    if "Makefile" in names:
        commands.append("make test")
    if "scripts/check-package.sh" in names:
        commands.append("bash scripts/check-package.sh")
    for script in ("run-tests.sh", "test.sh", "scripts/test.sh", "scripts/run-tests.sh"):
        if script in names:
            commands.append(f"bash {script}")
    if any(f.endswith(".xcodeproj/project.pbxproj") for f in names):
        commands.append("xcodebuild test")
    if "Package.swift" in names:
        commands.append("swift test")
    if "Cargo.toml" in names:
        commands.append("cargo test")
    if "go.mod" in names:
        commands.append("go test ./...")
    if "Gemfile" in names:
        commands.append("bundle exec rake test")
    if any(path.endswith((".sln", ".csproj")) for path in names):
        commands.append("dotnet test")
    return list(dict.fromkeys(commands))[:24]

def detect_e2e_inventory(repo: Path, tracked: list[str], test_commands: list[str] | None = None) -> dict:
    """Classify an existing E2E surface without inventing an executable command."""
    names = set(tracked)
    e2e_files = [
        path for path in tracked
        if Path(path).name.startswith(("playwright.config", "cypress.config"))
        or Path(path).name == "cypress.json"
        or path.startswith(("e2e/", "tests/e2e/", "test/e2e/", "cypress/", "playwright/"))
    ]
    frameworks: list[str] = []
    if any(Path(path).name.startswith("playwright.config") for path in e2e_files):
        frameworks.append("Playwright")
    if any(Path(path).name.startswith("cypress.config") or Path(path).name == "cypress.json" for path in e2e_files):
        frameworks.append("Cypress")
    if any(path.startswith(("e2e/", "tests/e2e/", "test/e2e/")) for path in e2e_files):
        frameworks.append("repo E2E tests")
    commands = [
        command for command in (test_commands or [])
        if re.search(r"(?:^|\s|:)(?:e2e|smoke|playwright|cypress)(?:$|\s|:)", command, re.IGNORECASE)
    ]
    if "package.json" in names:
        try:
            package = json.loads((repo / "package.json").read_text(encoding="utf-8"))
            scripts = package.get("scripts", {})
            manager = "pnpm run" if "pnpm-lock.yaml" in names else "yarn" if "yarn.lock" in names else "npm run"
            for script in scripts:
                if re.search(r"(?:e2e|smoke|playwright|cypress)", script, re.IGNORECASE) and re.fullmatch(r"[A-Za-z0-9:_-]+", script):
                    commands.append(f"{manager} {script}")
        except (OSError, TypeError, ValueError, json.JSONDecodeError):
            pass
    return {
        "e2e_files": list(dict.fromkeys(e2e_files))[:40],
        "e2e_frameworks": list(dict.fromkeys(frameworks)),
        "e2e_commands": list(dict.fromkeys(commands))[:12],
    }

def verification_command_priority(command: list[str]) -> tuple[int, str]:
    """Prefer focused deterministic tests over broad or environment-heavy checks."""
    display = command_display(command)
    low = display.lower()
    if re.search(r"(?:^|\s)test$", low):
        return 0, low
    if re.search(r"(?:vitest|jest|pytest|unittest)", low):
        return 1, low
    if re.search(r"test:unit:[^\s]+", low):
        return 2, low
    if re.search(r"test:unit(?:\s|$)", low):
        return 3, low
    if re.search(r"test:(?:ai|eval|e2e|smoke|voice)|\b(?:ai|eval|e2e|smoke|headed|deployed|real)\b", low):
        return 3, low
    if "test" in low:
        return 4, low
    return 4, low

def normalize_github_actions_log(raw: str) -> str:
    lines: list[str] = []
    timestamp = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\s?")
    for line in raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3 and timestamp.match(parts[2]):
            line = timestamp.sub("", parts[2], count=1)
        lines.append(line)
    return "\n".join(lines)

def extract_github_actions_failure_evidence(raw: str) -> str:
    ansi = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
    lines = [ansi.sub("", line) for line in normalize_github_actions_log(raw).splitlines()]
    decisive = re.compile(
        r"(?:AssertionError|##\[error\]|Process completed with exit code [1-9]|"
        r"npm ERR!|\berror TS\d+|\bfatal:|\bpanic:|(?:^|\s)FAIL(?:\s|$))",
        re.IGNORECASE,
    )
    markers = [index for index, line in enumerate(lines) if decisive.search(line)]
    if not markers:
        return "\n".join(lines[-220:])
    selected: set[int] = set()
    for index in markers[:12]:
        selected.update(range(max(0, index - 5), min(len(lines), index + 7)))
    return "\n".join(lines[index] for index in sorted(selected))

def write_repo_scan(ledger: Path, scan: dict) -> None:
    (ledger / "repo-scan.json").write_text(redact(json.dumps(scan, indent=2, sort_keys=True)) + "\n", encoding="utf-8")
    lines = ["# Repo Scan", ""]
    lines.append(f"Repo: {scan.get('repo', 'unknown')}")
    lines.append(f"Branch: {scan.get('branch', '(unknown)')}")
    lines.append(f"Head: {scan.get('head', '(unknown)')}")
    lines.append(f"Tracked files: {scan.get('tracked_count', 0)}")
    dirty = scan.get("dirty_lines") or []
    lines.append(f"Dirty checkout: {'yes' if dirty else 'no'}")
    lines.append("")
    lines.append("Recent files:")
    for path in (scan.get("recent_files") or [])[:20]:
        lines.append(f"- {path}")
    if not scan.get("recent_files"):
        lines.append("- None found.")
    lines.append("")
    lines.append("Detected test commands:")
    for command in scan.get("test_commands") or []:
        lines.append(f"- `{command}`")
    if not scan.get("test_commands"):
        lines.append("- None detected.")
    lines.append("")
    lines.append("TODO/FIXME sample:")
    for item in (scan.get("todo_sample") or [])[:20]:
        lines.append(f"- {item}")
    if not scan.get("todo_sample"):
        lines.append("- None found in the sample.")
    for title, key in [
        ("Open pull requests", "github_open_prs_raw"),
        ("Open issues", "github_open_issues_raw"),
        ("Recent failed GitHub runs", "github_failed_runs_raw"),
    ]:
        raw = scan.get(key, "")
        lines.extend(["", f"{title}:"])
        lines.append(raw if raw and raw != "[]" else "- None found.")
    lines.append("")
    (ledger / "repo-scan.md").write_text("\n".join(lines), encoding="utf-8")

