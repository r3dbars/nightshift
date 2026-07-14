import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_repo_outcomes import append_repo_outcome, load_repo_outcomes, outcome_ledger_summary, repo_outcome_adjustment


class RepoOutcomeTests(unittest.TestCase):
    def test_productive_and_wasted_runs_adjust_ranking_with_caps(self):
        productive = [
            {"repo": "owner/good", "verified_drafts": 1, "estimated_tokens": 5000}
            for _ in range(5)
        ]
        wasted = [
            {"repo": "owner/weak", "accepted_candidates": 0, "estimated_tokens": 5000}
            for _ in range(8)
        ]
        good, good_summary = repo_outcome_adjustment(productive, "owner/good")
        weak, weak_summary = repo_outcome_adjustment(wasted, "owner/weak")
        self.assertEqual(good, 50)
        self.assertEqual(weak, -40)
        self.assertEqual(good_summary["productive_runs"], 5)
        self.assertEqual(weak_summary["wasted_token_runs"], 8)

    def test_zero_token_empty_run_is_neutral(self):
        adjustment, summary = repo_outcome_adjustment(
            [{"repo": "owner/repo", "accepted_candidates": 0, "estimated_tokens": 0}],
            "owner/repo",
        )
        self.assertEqual(adjustment, 0)
        self.assertEqual(summary["wasted_token_runs"], 0)

    def test_candidate_only_runs_do_not_look_like_verified_productivity(self):
        adjustment, summary = repo_outcome_adjustment(
            [{
                "repo": "owner/repo",
                "accepted_candidates": 3,
                "candidate_only_candidates": 3,
                "estimated_tokens": 5000,
            }],
            "owner/repo",
        )
        self.assertEqual(adjustment, 0)
        self.assertEqual(summary["productive_runs"], 0)
        self.assertEqual(summary["verified_runs"], 0)
        self.assertEqual(summary["candidate_only_runs"], 1)
        self.assertEqual(summary["candidate_only_candidates"], 3)

    def test_feedback_changes_portfolio_ranking(self):
        useful, useful_summary = repo_outcome_adjustment(
            [{"repo": "owner/useful", "feedback_useful": 1}], "owner/useful"
        )
        not_useful, not_useful_summary = repo_outcome_adjustment(
            [{"repo": "owner/not-useful", "feedback_not_useful": 1}], "owner/not-useful"
        )
        self.assertEqual(useful, 25)
        self.assertEqual(not_useful, -25)
        self.assertEqual(useful_summary["useful_feedback"], 1)
        self.assertEqual(not_useful_summary["not_useful_feedback"], 1)

    def test_feedback_summary_keeps_verified_and_candidate_value_separate(self):
        _, summary = repo_outcome_adjustment([
            {
                "repo": "owner/repo",
                "feedback_useful": 1,
                "feedback_verified": 1,
            },
            {
                "repo": "owner/repo",
                "feedback_useful": 1,
                "feedback_outcome_status": "MAYBE",
            },
            {
                "repo": "owner/repo",
                "draft_pr_opened": 1,
                "hosted_checks_state": "passed",
            },
        ], "owner/repo")
        self.assertEqual(summary["useful_verified_feedback"], 1)
        self.assertEqual(summary["useful_candidate_feedback"], 1)
        self.assertEqual(summary["hosted_draft_prs"], 1)
        self.assertEqual(summary["hosted_green_draft_prs"], 1)

    def test_aggregate_outcome_summary_excludes_feedback_rows_from_run_count(self):
        summary = outcome_ledger_summary([
            {
                "repo": "owner/repo", "verified_drafts": 1,
                "verified_outcome_tokens": 3400, "candidate_only_candidates": 2,
                "estimated_tokens": 4000, "draft_pr_opened": 1,
                "hosted_checks_state": "pass",
            },
            {
                "kind": "feedback", "feedback_useful": 1,
                "useful_verified_feedback": 1,
            },
        ])
        self.assertEqual(summary["runs"], 1)
        self.assertEqual(summary["verified_drafts"], 1)
        self.assertEqual(summary["candidate_only_candidates"], 2)
        self.assertEqual(summary["tokens_per_verified_draft"], 3400)
        self.assertEqual(summary["useful_verified_feedback"], 1)
        self.assertEqual(summary["hosted_green_draft_prs"], 1)

    def test_human_outcomes_only_count_verified_feedback(self):
        summary = outcome_ledger_summary([
            {
                "repo": "owner/repo", "kind": "feedback", "feedback_verified": 1,
                "human_outcome_accepted": 1,
            },
            {
                "repo": "owner/repo", "kind": "feedback", "feedback_verified": 0,
                "human_outcome_accepted": 1,
            },
        ])
        self.assertEqual(summary["accepted_verified_outcomes"], 1)
        self.assertEqual(summary["revised_verified_outcomes"], 0)
        self.assertEqual(summary["rejected_verified_outcomes"], 0)

    def test_accepted_verified_outcome_has_more_ranking_weight_than_a_candidate_vote(self):
        adjustment, summary = repo_outcome_adjustment([
            {
                "repo": "owner/repo", "feedback_verified": 1,
                "human_outcome_accepted": 1,
            },
        ], "owner/repo")
        self.assertEqual(adjustment, 35)
        self.assertEqual(summary["accepted_verified_outcomes"], 1)

    def test_outcome_ledger_is_bounded_and_keeps_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repo-outcomes.jsonl"
            for index in range(4):
                append_repo_outcome(path, {"repo": "owner/repo", "index": index}, limit=2)
            rows = load_repo_outcomes(path)
            self.assertEqual([row["index"] for row in rows], [2, 3])
            self.assertEqual(len(path.read_text().splitlines()), 2)

    def test_outcome_ledger_preserves_existing_rows_when_atomic_replace_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "repo-outcomes.jsonl"
            append_repo_outcome(path, {"repo": "owner/repo", "index": 0})
            before = path.read_text(encoding="utf-8")
            with patch("night_shift_repo_outcomes.os.replace", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    append_repo_outcome(path, {"repo": "owner/repo", "index": 1})
            self.assertEqual(path.read_text(encoding="utf-8"), before)
            self.assertEqual([row["index"] for row in load_repo_outcomes(path)], [0])
            self.assertEqual(list(path.parent.glob(f".{path.name}.*")), [])


if __name__ == "__main__":
    unittest.main()
