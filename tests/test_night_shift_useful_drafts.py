import difflib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_drafts import DraftEngine
from night_shift_policy import RepoProfile


class UsefulDraftExecutionTests(unittest.TestCase):
    def test_clean_baseline_intents_execute_and_repeat_their_proof(self):
        cases = (
            (
                "docs-repair",
                "README.md",
                "Run `python old.py`.\n",
                "Run `python3 -m app`.\n",
                2,
            ),
            (
                "safe-refactor",
                "src/app.py",
                "def active(value):\n    if value:\n        return True\n    return False\n",
                "def active(value):\n    return bool(value)\n",
                2,
            ),
            (
                "issue-fix",
                "src/app.py",
                "def normalize(value):\n    return value.strip()\n",
                "def normalize(value):\n    return value.strip().lower()\n",
                2,
            ),
            (
                "e2e-strengthening",
                "tests/e2e/smoke.spec.ts",
                "test('home', async ({ page }) => { await page.goto('/'); });\n",
                "test('home', async ({ page }) => { await page.goto('/'); await expect(page).toHaveTitle(/App/); });\n",
                3,
            ),
        )
        for intent, relative, before, after, expected_passes in cases:
            with self.subTest(intent=intent), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                repo = root / "repo"
                ledger = root / "ledger"
                repo.mkdir()
                target = repo / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(before, encoding="utf-8")
                subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
                subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
                subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
                subprocess.run(["git", "add", "."], cwd=repo, check=True)
                subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
                source_ref = subprocess.run(
                    ["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                    text=True, capture_output=True,
                ).stdout.strip()
                patch = (
                    f"diff --git a/{relative} b/{relative}\n"
                    + "".join(difflib.unified_diff(
                        before.splitlines(keepends=True),
                        after.splitlines(keepends=True),
                        fromfile=f"a/{relative}",
                        tofile=f"b/{relative}",
                        n=3,
                    ))
                )
                worker_calls = 0

                def fake_run(args, cwd=None, timeout=60, env=None, pid_log=None):
                    nonlocal worker_calls
                    parts = [str(part) for part in args]
                    if parts[0] == "git":
                        result = subprocess.run(
                            parts, cwd=cwd, text=True, capture_output=True, timeout=timeout, env=env,
                        )
                        return SimpleNamespace(rc=result.returncode, stdout=result.stdout, stderr=result.stderr)
                    if "maestro-delegate" in parts[0]:
                        worker_calls += 1
                        return SimpleNamespace(rc=0, stdout=patch, stderr="")
                    if Path(parts[0]).name in {"docker", "podman"}:
                        volumes = [parts[index + 1] for index, value in enumerate(parts) if value == "--volume"]
                        if any(value.endswith(":/patch-input:ro") for value in volumes):
                            artifact_dir = Path(next(
                                value for value in volumes if value.endswith(":/artifacts:rw")
                            ).removesuffix(":/artifacts:rw"))
                            artifact_dir.mkdir(parents=True, exist_ok=True)
                            (artifact_dir / "changed-paths.txt").write_text(relative + "\n", encoding="utf-8")
                            (artifact_dir / "applied.patch").write_text(patch, encoding="utf-8")
                            (artifact_dir / "verification.txt").write_text("passed\n", encoding="utf-8")
                            (artifact_dir / "verification.rc").write_text("0\n", encoding="utf-8")
                        return SimpleNamespace(rc=0, stdout="passed", stderr="")
                    raise AssertionError(parts)

                profile = RepoProfile(
                    trust="owned",
                    execution_enabled=True,
                    commands=(("true",),),
                    allowed_paths=(relative.split("/", 1)[0] if "/" in relative else relative,),
                    protected_paths=(".github", ".env"),
                    max_cpu=1,
                    max_memory_mb=512,
                    max_pids=32,
                    max_seconds=60,
                    image="sha256:" + "a" * 64,
                )
                result = DraftEngine(fake_run, root / "worktrees", lambda: "now").run_draft(
                    repo,
                    "owner/repo",
                    {
                        "key": intent,
                        "source_ref": source_ref,
                        "summary": f"prove {intent}",
                        "evidence": f"{relative}:1",
                        "expected_result": "approved check stays green",
                        "files": [relative],
                        "verification_argv": ["true"],
                        "draft_intent": intent,
                    },
                    ledger,
                    900,
                    "http://localhost/v1",
                    "local-coder",
                    profile=profile,
                    patch_lane="local",
                )
                self.assertEqual(result["status"], "VERIFIED_DRAFT")
                self.assertEqual(result["draft_intent"], intent)
                self.assertEqual(result["verification_passes"], expected_passes)
                self.assertEqual(result["verification_passes_required"], expected_passes)
                self.assertEqual(worker_calls, 1)


if __name__ == "__main__":
    unittest.main()
