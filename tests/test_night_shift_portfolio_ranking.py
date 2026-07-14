import json
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_portfolio import PortfolioEngine


class PortfolioRankingDeterminismTests(unittest.TestCase):
    def test_repo_slug_returns_empty_for_missing_repo(self):
        def unexpected_run(*_args, **_kwargs):
            raise AssertionError("missing repositories must not invoke git")

        engine = PortfolioEngine(
            unexpected_run, Path("/tmp/cache"), Path("/tmp/history"), lambda: "now"
        )

        self.assertEqual(engine.repo_slug(None), "")

    def test_authenticated_owner_returns_empty_without_github_cli(self):
        engine = PortfolioEngine(
            lambda *_args, **_kwargs: _result("unexpected"),
            Path("/tmp/cache"), Path("/tmp/history"), lambda: "now"
        )

        with patch("night_shift_portfolio.shutil.which", return_value=None):
            self.assertEqual(engine.authenticated_owner(), "")

    def test_normalize_priority_repos_strips_git_deduplicates_and_rejects_invalid(self):
        self.assertEqual(
            PortfolioEngine.normalize_priority_repos([
                " owner/repo.git ",
                "OWNER/repo",
                "owner/second-repo",
                "not-a-slug",
                "owner/too/many/segments",
            ]),
            ["owner/repo", "owner/second-repo"],
        )

    def test_repeated_discovery_keeps_the_same_ranked_portfolio(self):
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        repos = [
            "owner/quiet",
            "owner/issue",
            "owner/active",
            "owner/broken",
            "owner/extra",
        ]

        def fake_run(command, **_kwargs):
            command = [str(part) for part in command]
            if command[:3] == ["gh", "api", "user"]:
                return _result("owner\n")
            if command[:3] == ["gh", "repo", "list"]:
                return _result(json.dumps([
                    {
                        "nameWithOwner": slug,
                        "pushedAt": now,
                        "isPrivate": True,
                        "isArchived": False,
                        "isFork": False,
                        "defaultBranchRef": {"name": "main"},
                        "url": "",
                    }
                    for slug in repos
                ]))
            if command[:3] in (["gh", "pr", "list"], ["gh", "issue", "list"], ["gh", "run", "list"]):
                slug = command[command.index("-R") + 1]
                if command[:3] == ["gh", "pr", "list"] and slug == "owner/broken":
                    return _result(json.dumps([{
                        "number": 7,
                        "isDraft": False,
                        "reviewDecision": None,
                        "statusCheckRollup": [{"state": "FAILURE"}],
                    }]))
                if command[:3] == ["gh", "pr", "list"] and slug == "owner/active":
                    return _result(json.dumps([{
                        "number": 8,
                        "isDraft": False,
                        "reviewDecision": None,
                        "statusCheckRollup": [],
                    }]))
                if command[:3] == ["gh", "issue", "list"] and slug == "owner/issue":
                    return _result(json.dumps([{"number": 9}]))
                if command[:3] == ["gh", "run", "list"] and slug == "owner/broken":
                    return _result(json.dumps([{
                        "databaseId": 10,
                        "workflowName": "CI",
                        "headBranch": "main",
                        "status": "completed",
                        "conclusion": "failure",
                        "updatedAt": now,
                    }]))
                return _result("[]")
            raise AssertionError(f"unexpected command: {command}")

        engine = PortfolioEngine(fake_run, Path("/tmp/cache"), Path("/tmp/history"), lambda: "now")
        with patch("night_shift_portfolio.shutil.which", return_value="/usr/bin/gh"):
            snapshots = [
                [(row["slug"], row["score"]) for row in engine.discover(None, max_repos=4)]
                for _ in range(3)
            ]

        self.assertEqual(snapshots[0], [
            ("owner/broken", 340),
            ("owner/active", 130),
            ("owner/issue", 90),
            ("owner/extra", 80),
        ])
        self.assertEqual(snapshots[1:], [snapshots[0], snapshots[0]])

    def test_shuffled_rows_keep_score_and_slug_order(self):
        rows = [
            {"slug": "owner/charlie", "score": 100, "primary": False},
            {"slug": "owner/alpha", "score": 100, "primary": False},
            {"slug": "owner/bravo", "score": 100, "primary": False},
            {"slug": "owner/delta", "score": 10, "primary": False},
        ]

        selected = PortfolioEngine.select_ranked_rows(list(reversed(rows)), 4)

        self.assertEqual(
            [row["slug"] for row in selected],
            ["owner/alpha", "owner/bravo", "owner/charlie", "owner/delta"],
        )

    def test_primary_repo_is_retained_without_changing_rank_order(self):
        rows = [
            {"slug": "owner/high", "score": 500, "primary": False},
            {"slug": "owner/mid", "score": 300, "primary": False},
            {"slug": "owner/current", "score": 1, "primary": True},
        ]

        selected = PortfolioEngine.select_ranked_rows(list(reversed(rows)), 2)

        self.assertEqual(
            [row["slug"] for row in selected],
            ["owner/high", "owner/current"],
        )

    def test_selection_reason_matches_the_github_signal_that_won_the_slot(self):
        self.assertEqual(
            PortfolioEngine.selection_reason({
                "signals": {
                    "prs": [{
                        "reviewDecision": "CHANGES_REQUESTED",
                        "statusCheckRollup": [],
                        "isDraft": False,
                    }],
                },
            }),
            "pull requests need review or fixes",
        )
        self.assertEqual(
            PortfolioEngine.selection_reason({
                "signals": {
                    "prs": [{"reviewDecision": None, "statusCheckRollup": [], "isDraft": False}],
                },
            }),
            "ready-to-merge pull requests",
        )
        self.assertEqual(
            PortfolioEngine.selection_reason({
                "signals": {
                    "prs": [{"reviewDecision": None, "statusCheckRollup": [], "isDraft": True}],
                },
            }),
            "open draft pull requests",
        )

    def test_selection_reason_prefers_actionable_prs_over_ready_or_draft_prs(self):
        reason = PortfolioEngine.selection_reason({
            "signals": {
                "prs": [
                    {"reviewDecision": None, "statusCheckRollup": [], "isDraft": True},
                    {"reviewDecision": None, "statusCheckRollup": [], "isDraft": False},
                    {"reviewDecision": None, "statusCheckRollup": [{"state": "FAILURE"}], "isDraft": True},
                ],
            },
        })
        self.assertEqual(reason, "pull requests need review or fixes")


def _result(stdout: str):
    return type("CommandResult", (), {"stdout": stdout, "stderr": "", "rc": 0})()


if __name__ == "__main__":
    unittest.main()
