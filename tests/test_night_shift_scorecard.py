import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_scorecard import below_target, parse_scores


class ScorecardTests(unittest.TestCase):
    def test_parse_ignores_header_and_reads_dimensions(self):
        rows = parse_scores("""# Scores
| Dimension | Score | Evidence |
| --- | ---: | --- |
| Product idea | 95 | proof |
| Cloud handoff | 88 | consent needed |
""")
        self.assertEqual(rows, [
            {"dimension": "Product idea", "score": 95},
            {"dimension": "Cloud handoff", "score": 88},
        ])

    def test_below_target_is_explicit(self):
        rows = [{"dimension": "A", "score": 95}, {"dimension": "B", "score": 94}]
        self.assertEqual(below_target(rows), [{"dimension": "B", "score": 94}])


if __name__ == "__main__":
    unittest.main()
