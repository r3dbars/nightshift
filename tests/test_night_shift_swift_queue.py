import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_queue import QueueEvidenceIndex, complete_invocation_evidence


class SwiftQueueEvidenceTests(unittest.TestCase):
    def test_skips_swift_module_not_imported_by_test_target(self):
        self.assertFalse(
            QueueEvidenceIndex.swift_source_is_testable(
                "Sources/App/AppDelegate.swift", "import Core\n"
            )
        )
        self.assertTrue(
            QueueEvidenceIndex.swift_source_is_testable(
                "Sources/Core/Stats.swift", "@testable import Core\n"
            )
        )

    def test_swift_invocation_index_is_complete_and_test_scoped(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Sources" / "Core").mkdir(parents=True)
            (repo / "Tests").mkdir()
            (repo / "Sources" / "Core" / "Summary.swift").write_text(
                "public struct EntryStatsSummary { public init() {} }\n",
                encoding="utf-8",
            )
            (repo / "Tests" / "SummaryTests.swift").write_text(
                "import Core\nimport XCTest\nfinal class SummaryTests: XCTestCase {}\n",
                encoding="utf-8",
            )
            scan = {
                "tracked_files": ["Sources/Core/Summary.swift", "Tests/SummaryTests.swift"],
                "coverage_test_files": ["Tests/SummaryTests.swift"],
            }
            evidence = QueueEvidenceIndex(repo, scan).invocation_gap(
                "Sources/Core/Summary.swift", "EntryStatsSummary"
            )
            text = next(iter(evidence.values()))
            self.assertIn("analysis=swift-regex", text)
            self.assertIn("scope=test-files-only", text)
            self.assertIn("call_matches=0", text)
            self.assertIn("scan_complete=true", text)
            self.assertTrue(complete_invocation_evidence(text))

            gaps = QueueEvidenceIndex(repo, scan).coverage_gaps(["Sources/Core/Summary.swift"])
            self.assertEqual(len(gaps), 1)
            self.assertTrue(any(key.startswith("invocation-index/") for key in gaps[0][2]))


if __name__ == "__main__":
    unittest.main()
