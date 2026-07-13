import tempfile
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_queue import QueueEvidenceIndex, RepoRevisionAdapter, contains_identifier, is_test_path


class QueueEvidenceTests(unittest.TestCase):
    def test_issue_symbols_rank_exact_source_matches(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src").mkdir()
            (repo / "src" / "primary.py").write_text("def repair_session():\n    pass\n", encoding="utf-8")
            (repo / "src" / "secondary.py").write_text("def other():\n    pass\n", encoding="utf-8")
            index = QueueEvidenceIndex(repo, {
                "tracked_files": ["src/primary.py", "src/secondary.py"],
                "source_files": ["src/primary.py", "src/secondary.py"],
            })
            files, matches = index.issue_candidate_files({
                "title": "Repair `repair_session()`",
                "body": "The failure is in src/secondary.py but `repair_session` is the exact symbol.",
            })
            self.assertEqual(files, ["src/primary.py", "src/secondary.py"])
            self.assertEqual(matches, 2)

    def test_coverage_evidence_is_complete_only_when_every_test_is_indexed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src.py").write_text("def public_api():\n    return 1\n", encoding="utf-8")
            (repo / "test_src.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
            scan = {
                "tracked_files": ["src.py", "test_src.py"],
                "source_files": ["src.py"],
                "test_files": ["test_src.py"],
                "coverage_test_files": ["test_src.py"],
            }
            gaps = QueueEvidenceIndex(repo, scan).coverage_gaps(["src.py"])
            self.assertEqual(gaps[0][0:2], ("src.py", "public_api"))
            evidence = next(iter(gaps[0][2].values()))
            self.assertIn("identifier_matches=0", evidence)
            self.assertIn("scan_complete=true", evidence)
            scan["coverage_test_files"] = ["test_src.py", "missing_test.py"]
            incomplete = QueueEvidenceIndex(repo, scan).coverage_gaps(["src.py"])
            self.assertIn("scan_complete=false", next(iter(incomplete[0][2].values())))

    def test_binary_source_is_not_treated_as_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "binary.py").write_bytes(b"def fake():\x00ignored")
            index = QueueEvidenceIndex(repo, {"tracked_files": ["binary.py"], "source_files": ["binary.py"]})
            self.assertEqual(index.read_current_text("binary.py"), "")
            self.assertEqual(index.issue_candidate_files({"title": "Fix `fake`"}), ([], 0))

    def test_shared_path_and_identifier_rules_preserve_boundaries(self):
        self.assertTrue(is_test_path("src/test_app.py"))
        self.assertFalse(is_test_path("src/contest_app.py"))
        self.assertTrue(contains_identifier("run()", "run"))
        self.assertFalse(contains_identifier("runtime = 1", "run"))

    def test_malicious_refs_branches_and_paths_never_reach_git(self):
        calls = []

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            return SimpleNamespace(rc=1, stdout="", stderr="")

        adapter = RepoRevisionAdapter(Path("/repo"), runner)
        self.assertFalse(adapter.ensure_pr_ref("1;touch /tmp/pwn", "a" * 40))
        self.assertFalse(adapter.ensure_pr_ref("1", "HEAD"))
        self.assertFalse(adapter.ensure_branch_ref("--upload-pack=evil", "a" * 40))
        self.assertFalse(adapter.ensure_branch_ref("feature/../main", "a" * 40))
        self.assertFalse(adapter.file_exists("../secret", "a" * 40))
        self.assertFalse(adapter.file_exists(".git/config", "a" * 40))
        self.assertEqual(
            [argv for argv, _ in calls],
            [
                ["git", "cat-file", "-e", f"{'a' * 40}^{{commit}}"],
                ["git", "cat-file", "-e", f"{'a' * 40}^{{commit}}"],
                ["git", "cat-file", "-e", f"{'a' * 40}^{{commit}}"],
            ],
        )
        self.assertFalse(any("fetch" in argv for argv, _ in calls))

    def test_fetch_uses_literal_allowlisted_refs_and_rechecks_commit(self):
        calls = []
        availability = iter([1, 0])

        def runner(argv, **kwargs):
            calls.append((argv, kwargs))
            if argv[1:3] == ["cat-file", "-e"]:
                return SimpleNamespace(rc=next(availability), stdout="", stderr="")
            return SimpleNamespace(rc=0, stdout="", stderr="")

        ref = "b" * 40
        adapter = RepoRevisionAdapter(Path("/repo"), runner)
        self.assertTrue(adapter.ensure_pr_ref("42", ref))
        self.assertEqual(calls[1][0], ["git", "fetch", "--quiet", "--no-tags", "origin", "refs/pull/42/head"])
        self.assertEqual(calls[1][1]["timeout"], 120)

    def test_log_paths_are_deduped_suffixes_and_list_files_requires_sha(self):
        adapter = RepoRevisionAdapter(Path("/repo"), lambda *_args, **_kwargs: None)
        self.assertEqual(
            adapter.log_paths("error /workspace/src/app.py:4\nagain src/app.py"),
            ["workspace/src/app.py", "src/app.py", "app.py"],
        )
        self.assertIsNone(adapter.list_files("HEAD"))


if __name__ == "__main__":
    unittest.main()
