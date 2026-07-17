import json
import stat
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_trust import approval_path, load_effective_profile, save_approval


def profile(image="sha256:" + "a" * 64):
    return {
        "version": 1,
        "trust": "owned",
        "execution": "sandbox-only",
        "image": image,
        "commands": [["python3", "-m", "pytest"]],
        "allowed_paths": ["src", "tests"],
        "protected_paths": [".github", ".env"],
        "limits": {"cpu": 2, "memory_mb": 2048, "pids": 128, "seconds": 900},
    }


class RepoTrustTests(unittest.TestCase):
    def test_external_approval_is_remote_bound_and_private(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            approvals = root / "approvals"
            remote = "git@github.com:owner/repo.git"
            path = save_approval(approvals, remote, "owner/repo", profile())
            self.assertEqual(path, approval_path(approvals, remote))
            self.assertEqual(stat.S_IMODE(approvals.stat().st_mode), 0o700)
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
            loaded, detail = load_effective_profile(repo, approvals, lambda _: remote, lambda *_: True)
            self.assertTrue(loaded.may_execute)
            self.assertEqual(detail, "external repo approval loaded")
            missing, detail = load_effective_profile(repo, approvals, lambda _: "git@github.com:owner/other.git", lambda *_: True)
            self.assertIsNone(missing)
            self.assertIn("missing external owned-repo approval", detail)

    def test_tampered_remote_binding_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            approvals = root / "approvals"
            remote = "https://github.com/owner/repo.git"
            path = save_approval(approvals, remote, "owner/repo", profile())
            record = json.loads(path.read_text())
            record["remote"] = "https://github.com/attacker/repo.git"
            path.write_text(json.dumps(record), encoding="utf-8")
            loaded, detail = load_effective_profile(repo, approvals, lambda _: remote, lambda *_: True)
            self.assertIsNone(loaded)
            self.assertIn("does not match", detail)

    def test_repo_local_profile_cannot_authorize_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            (repo / ".night-shift.json").write_text(json.dumps(profile()), encoding="utf-8")
            loaded, detail = load_effective_profile(repo, root / "approvals", lambda _: "", lambda *_: False)
            self.assertIsNone(loaded)
            self.assertIn("proposals only", detail)

    def test_spoofed_remote_without_advertised_head_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            repo = root / "repo"
            repo.mkdir()
            approvals = root / "approvals"
            remote = "git@github.com:owner/repo.git"
            save_approval(approvals, remote, "owner/repo", profile())
            loaded, detail = load_effective_profile(repo, approvals, lambda _: remote, lambda *_: False)
            self.assertIsNone(loaded)
            self.assertIn("not advertised", detail)

    def test_symlinked_approval_target_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            approvals = root / "approvals"
            approvals.mkdir()
            remote = "git@github.com:owner/repo.git"
            target = root / "outside.json"
            target.write_text("untouched", encoding="utf-8")
            approval_path(approvals, remote).symlink_to(target)
            with self.assertRaisesRegex(OSError, "symlinked"):
                save_approval(approvals, remote, "owner/repo", profile())
            self.assertEqual(target.read_text(encoding="utf-8"), "untouched")

    def test_symlinked_approval_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            outside = root / "outside"
            outside.mkdir()
            approvals = root / "approvals"
            approvals.symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(OSError, "directory"):
                save_approval(approvals, "git@github.com:owner/repo.git", "owner/repo", profile())


if __name__ == "__main__":
    unittest.main()
