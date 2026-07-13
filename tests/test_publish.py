import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_policy import RepoProfile
from night_shift_publish import PublishEngine


PATCH = """diff --git a/src/app.py b/src/app.py
index 56a6051..243f978 100644
--- a/src/app.py
+++ b/src/app.py
@@ -1 +1 @@
-return 1
+return 2
"""


def result(rc=0, stdout="", stderr=""):
    return SimpleNamespace(rc=rc, stdout=stdout, stderr=stderr)


def profile():
    return RepoProfile(
        trust="owned",
        execution_enabled=True,
        commands=(("python3", "-m", "unittest"),),
        allowed_paths=("src",),
        protected_paths=(".github", ".env"),
        max_cpu=1,
        max_memory_mb=512,
        max_pids=32,
        max_seconds=60,
        image="sha256:" + "a" * 64,
    )


class PublishTests(unittest.TestCase):
    def proof(self, patch_path):
        return {
            "status": "PROVEN_REPAIR",
            "source_ref": "b" * 40,
            "patch": str(patch_path),
            "files": ["src/app.py"],
            "verification_argv": ["python3", "-m", "unittest"],
            "summary": "repair answer",
            "proof_level": "failing-before and passing-after",
        }

    def test_opens_and_verifies_draft_pr_after_fresh_sandbox_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch_path = root / "repair.patch"
            patch_path.write_text(PATCH, encoding="utf-8")
            calls = []

            def fake(command, **kwargs):
                args = [str(item) for item in command]
                calls.append(args)
                if args[:3] == ["gh", "api", "user"]:
                    return result(stdout="owner\n")
                if args[:3] == ["gh", "repo", "view"]:
                    return result(stdout=json.dumps({"nameWithOwner": "owner/repo", "isFork": False, "defaultBranchRef": {"name": "main"}}))
                if args[:3] == ["git", "diff", "--name-only"]:
                    return result(stdout="src/app.py\n")
                if args[:3] == ["gh", "pr", "create"]:
                    return result(stdout="https://github.com/owner/repo/pull/7\n")
                if args[:3] == ["gh", "pr", "view"]:
                    return result(stdout="true\n")
                return result()

            engine = PublishEngine(fake, root / "worktrees", lambda: "20260712t120000z")
            published = engine.publish(
                root, "owner/repo", self.proof(patch_path), profile(), root / "proof"
            )
            self.assertEqual(published["status"], "DRAFT_PR_OPENED")
            push_index = next(i for i, args in enumerate(calls) if args[:2] == ["git", "push"])
            sandbox_index = next(
                i for i, args in enumerate(calls)
                if args and Path(args[0]).name in {"podman", "docker"}
            )
            self.assertLess(sandbox_index, push_index)
            staged = next(args for args in calls if args[:2] == ["git", "add"])
            self.assertEqual(staged[-1], "src/app.py")
            commit = next(args for args in calls if "commit" in args)
            self.assertIn("user.name=Night Shift", commit)
            self.assertIn("user.email=night-shift@users.noreply.github.com", commit)
            self.assertIn("commit.gpgSign=false", commit)
            self.assertTrue(any(args[:4] == ["git", "worktree", "remove", "--force"] for args in calls))
            push_count = sum(args[:2] == ["git", "push"] for args in calls)
            duplicate = engine.publish(root, "owner/repo", self.proof(patch_path), profile(), root / "proof-2")
            self.assertEqual(duplicate["status"], "REJECT")
            self.assertIn("already published", duplicate["reason"])
            self.assertEqual(sum(args[:2] == ["git", "push"] for args in calls), push_count)

    def test_rejects_non_owner_before_creating_worktree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch_path = root / "repair.patch"
            patch_path.write_text(PATCH, encoding="utf-8")
            calls = []

            def fake(command, **kwargs):
                args = [str(item) for item in command]
                calls.append(args)
                if args[:3] == ["gh", "api", "user"]:
                    return result(stdout="someone-else\n")
                if args[:3] == ["gh", "repo", "view"]:
                    return result(stdout=json.dumps({"nameWithOwner": "owner/repo", "isFork": False, "defaultBranchRef": {"name": "main"}}))
                return result()

            published = PublishEngine(fake, root / "worktrees", lambda: "now").publish(
                root, "owner/repo", self.proof(patch_path), profile(), root / "proof"
            )
            self.assertEqual(published["status"], "REJECT")
            self.assertFalse(any(args[:3] == ["git", "worktree", "add"] for args in calls))

    def test_rejects_when_local_origin_is_a_different_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch_path = root / "repair.patch"
            patch_path.write_text(PATCH, encoding="utf-8")
            calls = []

            def fake(command, **kwargs):
                args = [str(item) for item in command]
                calls.append(args)
                if args[:3] == ["gh", "api", "user"]:
                    return result(stdout="owner\n")
                if args[:3] == ["gh", "repo", "view"]:
                    return result(stdout=json.dumps({"nameWithOwner": "owner/different", "isFork": False, "defaultBranchRef": {"name": "main"}}))
                return result()

            published = PublishEngine(fake, root / "worktrees", lambda: "now").publish(
                root, "owner/repo", self.proof(patch_path), profile(), root / "proof"
            )
            self.assertEqual(published["status"], "REJECT")
            self.assertFalse(any(args[:3] == ["git", "worktree", "add"] for args in calls))

    def test_closes_pr_when_github_does_not_preserve_draft_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch_path = root / "repair.patch"
            patch_path.write_text(PATCH, encoding="utf-8")
            calls = []

            def fake(command, **kwargs):
                args = [str(item) for item in command]
                calls.append(args)
                if args[:3] == ["gh", "api", "user"]:
                    return result(stdout="owner\n")
                if args[:3] == ["gh", "repo", "view"]:
                    return result(stdout=json.dumps({"nameWithOwner": "owner/repo", "isFork": False, "defaultBranchRef": {"name": "main"}}))
                if args[:3] == ["git", "diff", "--name-only"]:
                    return result(stdout="src/app.py\n")
                if args[:3] == ["gh", "pr", "create"]:
                    return result(stdout="https://github.com/owner/repo/pull/8\n")
                if args[:3] == ["gh", "pr", "view"]:
                    return result(stdout="false\n")
                return result()

            published = PublishEngine(fake, root / "worktrees", lambda: "now").publish(
                root, "owner/repo", self.proof(patch_path), profile(), root / "proof"
            )
            self.assertEqual(published["status"], "REJECT")
            self.assertTrue(any(args[:3] == ["gh", "pr", "close"] for args in calls))

    def test_refuses_source_commit_outside_default_branch_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch_path = root / "repair.patch"
            patch_path.write_text(PATCH, encoding="utf-8")
            calls = []

            def fake(command, **kwargs):
                args = [str(item) for item in command]
                calls.append(args)
                if args[:3] == ["gh", "api", "user"]:
                    return result(stdout="owner\n")
                if args[:3] == ["gh", "repo", "view"]:
                    return result(stdout=json.dumps({"nameWithOwner": "owner/repo", "isFork": False, "defaultBranchRef": {"name": "main"}}))
                if args[:3] == ["git", "merge-base", "--is-ancestor"]:
                    return result(rc=1)
                return result()

            published = PublishEngine(fake, root / "worktrees", lambda: "now").publish(
                root, "owner/repo", self.proof(patch_path), profile(), root / "proof"
            )
            self.assertEqual(published["status"], "REJECT")
            self.assertIn("default branch", published["reason"])
            self.assertFalse(any(args[:3] == ["git", "worktree", "add"] for args in calls))

    def test_reports_remote_cleanup_failure_instead_of_claiming_rejection_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch_path = root / "repair.patch"
            patch_path.write_text(PATCH, encoding="utf-8")

            def fake(command, **kwargs):
                args = [str(item) for item in command]
                if args[:3] == ["gh", "api", "user"]:
                    return result(stdout="owner\n")
                if args[:3] == ["gh", "repo", "view"]:
                    return result(stdout=json.dumps({"nameWithOwner": "owner/repo", "isFork": False, "defaultBranchRef": {"name": "main"}}))
                if args[:3] == ["git", "diff", "--name-only"]:
                    return result(stdout="src/app.py\n")
                if args[:3] == ["gh", "pr", "create"]:
                    return result(stdout="https://github.com/owner/repo/pull/9\n")
                if args[:3] == ["gh", "pr", "view"]:
                    return result(stdout="false\n")
                if args[:3] == ["gh", "pr", "close"]:
                    return result(rc=1)
                if args[:3] == ["git", "ls-remote", "--exit-code"]:
                    return result(stdout="abc\trefs/heads/night-shift/test\n")
                if args[:4] == ["git", "push", "origin", "--delete"]:
                    return result(rc=1)
                return result()

            published = PublishEngine(fake, root / "worktrees", lambda: "now").publish(
                root, "owner/repo", self.proof(patch_path), profile(), root / "proof"
            )
            self.assertEqual(published["status"], "REMOTE_CLEANUP_REQUIRED")
            self.assertTrue(published["remote_branch_created"])
            self.assertFalse(published["pr_closed"])

    def test_ambiguous_push_failure_requires_cleanup_when_remote_is_unreachable(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            patch_path = root / "repair.patch"
            patch_path.write_text(PATCH, encoding="utf-8")

            def fake(command, **kwargs):
                args = [str(item) for item in command]
                if args[:3] == ["gh", "api", "user"]:
                    return result(stdout="owner\n")
                if args[:3] == ["gh", "repo", "view"]:
                    return result(stdout=json.dumps({"nameWithOwner": "owner/repo", "isFork": False, "defaultBranchRef": {"name": "main"}}))
                if args[:3] == ["git", "diff", "--name-only"]:
                    return result(stdout="src/app.py\n")
                if len(args) >= 4 and args[:3] == ["git", "push", "origin"] and "--delete" not in args:
                    return result(rc=124, stderr="timeout")
                if args[:3] == ["git", "ls-remote", "--exit-code"]:
                    return result(rc=1, stderr="network unavailable")
                return result()

            published = PublishEngine(fake, root / "worktrees", lambda: "now").publish(
                root, "owner/repo", self.proof(patch_path), profile(), root / "proof"
            )
            self.assertEqual(published["status"], "REMOTE_CLEANUP_REQUIRED")
            self.assertTrue(published["remote_branch_created"])


if __name__ == "__main__":
    unittest.main()
