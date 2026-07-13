import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_autopilot import AutopilotCycleState


class AutopilotCycleStateTests(unittest.TestCase):
    def test_child_transition_tracks_status_work_and_durable_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            state = AutopilotCycleState(ledger)
            self.assertEqual(state.start_cycle(), 1)
            row = state.record_child(
                repo="owner/repo", checkout=ledger, child_ledger=ledger / "child",
                return_code=0, child_is_green=False, planned_count=2,
            )
            state.append(row)
            self.assertEqual(state.status, "YELLOW")
            self.assertTrue(state.cycle_had_work)
            self.assertEqual(json.loads((ledger / "cycles.json").read_text())[0], row)

    def test_draft_and_publish_transitions_are_bounded_per_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = AutopilotCycleState(Path(tmp))
            state.start_cycle()
            row = {"repo": "owner/repo", "rc": 0}
            self.assertTrue(state.may_draft("owner/repo", True, "draft-prs"))
            state.finish_draft_attempt(row, {"status": "VERIFIED_DRAFT"})
            self.assertFalse(state.may_draft("owner/repo", True, "draft-prs"))
            state.attach_publish(row, {"status": "REMOTE_CLEANUP_REQUIRED"})
            state.append(row)
            self.assertEqual(state.status, "YELLOW")
            self.assertTrue(state.action_required())

    def test_clean_rows_need_no_action_but_empty_run_does(self):
        with tempfile.TemporaryDirectory() as tmp:
            state = AutopilotCycleState(Path(tmp))
            self.assertTrue(state.action_required())
            state.rows.append({"repo": "owner/repo", "rc": 0, "new_tasks": 0})
            self.assertFalse(state.action_required())
            state.no_prepared_repositories()
            self.assertEqual(state.status, "YELLOW")


if __name__ == "__main__":
    unittest.main()
