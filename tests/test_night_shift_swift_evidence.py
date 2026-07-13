import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_swift_evidence import swift_declares_symbol, swift_symbol_call_count_text


class SwiftEvidenceTests(unittest.TestCase):
    def test_counts_direct_type_calls_but_not_declarations(self):
        source = """
public struct EntryStatsSummary {}
func makeSummary() -> EntryStatsSummary { EntryStatsSummary() }
// EntryStatsSummary() in a comment is not a call.
"""
        self.assertTrue(swift_declares_symbol(source, "EntryStatsSummary"))
        self.assertEqual(swift_symbol_call_count_text(source, "EntryStatsSummary"), 1)

    def test_counts_repeated_type_calls_and_ignores_unrelated_symbols(self):
        tests = """
let first = EntryStatsSummary()
let second = EntryStatsSummary()
let other = Other()
"""
        self.assertEqual(swift_symbol_call_count_text(tests, "EntryStatsSummary"), 2)
        self.assertEqual(swift_symbol_call_count_text(tests, "Other"), 1)


if __name__ == "__main__":
    unittest.main()
