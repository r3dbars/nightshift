import tempfile
import unittest
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_queue import QueueEvidenceIndex, contains_identifier, is_test_path


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


if __name__ == "__main__":
    unittest.main()
