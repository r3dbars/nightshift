import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_reporting import ReportEngine
from night_shift_portfolio import PortfolioEngine
from night_shift_portfolio_reporting import PortfolioReportEngine


def result(label="tests-001", score="KEEP", lane="local", summary="Add focused test"):
    return {
        "label": label, "score": score, "lane": lane, "summary": summary,
        "output": "ACTION_TYPE: patch-plan\nTESTS_TO_RUN: python3 -m unittest",
        "artifact": f"/tmp/{label}.md", "tokens": 100, "input_tokens": 60,
        "output_tokens": 40, "rc": 0, "timed_out": False,
        "evidence": "src/app.py:1 | def app():", "files": ["src/app.py"],
        "evidence_sources": {"invocation-index/app.txt": "scan_complete=true"},
        "tests": "python3 -m unittest", "expected_result": "tests pass",
    }


class ReportingTests(unittest.TestCase):
    def engine(self, feedback=None, states=None):
        return ReportEngine(
            load_feedback=lambda: feedback or [],
            run_cmd=lambda *args, **kwargs: None,
            token_reporter=Path("/bin/token-report"),
            narrow_task_files=lambda files: sorted(files),
            latest_states=lambda path: states or {},
        )

    def test_status_contract(self):
        engine = self.engine()
        self.assertEqual(engine.run_status([], 0, "GREEN"), "YELLOW")
        self.assertEqual(engine.run_status([result()], 100, "GREEN"), "GREEN")
        self.assertEqual(engine.run_status([result(score="MAYBE")], 100, "GREEN"), "YELLOW")
        self.assertEqual(engine.run_status([result()], 101, "GREEN", "afterburner"), "YELLOW")
        self.assertEqual(engine.run_status([result()], 0, "RED"), "RED")

    def test_metrics_and_lifecycle_use_injected_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            engine = self.engine(
                feedback=[{"verdict": "useful"}],
                states={"a": {"state": "VERIFIED"}, "b": {"state": "REJECTED"}},
            )
            engine.write_outcome_metrics(ledger, [result()], [{"category": "pre-model"}, {"category": "repeat"}])
            engine.write_task_lifecycle_summary(ledger)
            metrics = json.loads((ledger / "outcome-metrics.json").read_text())
            self.assertEqual(metrics["accepted_candidates"], 1)
            self.assertEqual(metrics["human_feedback_events"], 1)
            self.assertEqual(metrics["current_feedback_preferences"], 1)
            self.assertEqual(metrics["current_useful_preferences"], 1)
            self.assertEqual(metrics["current_not_useful_preferences"], 0)
            self.assertEqual(metrics["cooldown_or_repeat_skips"], 1)
            lifecycle = (ledger / "task-lifecycle.md").read_text()
            self.assertIn("- VERIFIED: 1", lifecycle)
            self.assertIn("- REJECTED: 1", lifecycle)

    def test_outcome_metrics_snapshot_latest_changed_feedback(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            feedback = [
                {"repo": "/repo", "family": "tests", "fingerprint": "same", "verdict": "useful"},
                {"repo": "/repo", "family": "tests", "fingerprint": "same", "verdict": "not-useful"},
            ]
            self.engine(feedback=feedback).write_outcome_metrics(ledger, [], [])
            metrics = json.loads((ledger / "outcome-metrics.json").read_text())
            self.assertEqual(metrics["human_feedback_events"], 2)
            self.assertEqual(metrics["current_feedback_preferences"], 1)
            self.assertEqual(metrics["current_useful_preferences"], 0)
            self.assertEqual(metrics["current_not_useful_preferences"], 1)

    def test_outcome_metrics_explain_repo_feedback_effect(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            (ledger / "mode.json").write_text(json.dumps({"repo": "/repo"}))
            feedback = [{
                "repo": "/repo", "family": "tests", "fingerprint": "same",
                "verdict": "useful",
            }]
            skipped = [
                {"category": "feedback", "reason": "low-value family"},
                {"category": "review-outcome", "reason": "rejected exact candidate"},
            ]
            (ledger / "planned-work-queue.json").write_text(json.dumps([
                {"feedback_adjustment": 25}, {"feedback_adjustment": 0},
                {"feedback_adjustment": -20},
            ]))
            self.engine(feedback=feedback).write_outcome_metrics(ledger, [], skipped)
            metrics = json.loads((ledger / "outcome-metrics.json").read_text())
            self.assertTrue(metrics["feedback_signal_active"])
            self.assertEqual(metrics["repo_feedback_events"], 1)
            self.assertEqual(metrics["repo_current_feedback_preferences"], 1)
            self.assertEqual(metrics["repo_current_useful_preferences"], 1)
            self.assertEqual(metrics["feedback_skips_before_model"], 1)
            self.assertEqual(metrics["review_outcome_skips_before_model"], 1)
            self.assertEqual(metrics["feedback_adjusted_candidates"], 2)
            self.assertEqual(metrics["feedback_adjustment_total"], 5)
            self.assertEqual(metrics["feedback_positive_adjustments"], 1)
            self.assertEqual(metrics["feedback_negative_adjustments"], 1)

    def test_harvest_and_work_queue_rank_and_dedupe(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            rows = [result("tests-001", lane="local"), result("tests-002", lane="windows")]
            engine = self.engine()
            engine.write_harvest(ledger, rows)
            items = engine.write_work_queue(ledger, rows)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["lanes"], ["local", "windows"])
            self.assertIn("KEEP: 2", (ledger / "harvest.md").read_text())
            queue = json.loads((ledger / "work-queue.json").read_text())
            self.assertEqual(queue[0]["supporting_artifacts"], 2)
            self.assertEqual(queue[0]["evidence_sources"], rows[0]["evidence_sources"])

    def test_work_queue_and_harvest_redact_raw_evidence_and_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            row = result(summary="Authorization: Bearer summarycanary123456789")
            row["evidence"] = "src/app.py:1 | client_secret=evidencecanary123456789"
            row["evidence_sources"] = {
                "github-actions/run.log": "api_key=ledgercanary123456789",
                ".env": "TOKEN=envcanary123456789",
            }
            engine = self.engine()
            engine.write_harvest(ledger, [row])
            engine.write_work_queue(ledger, [row])
            combined = (ledger / "harvest.md").read_text() + (ledger / "work-queue.json").read_text()
            for canary in ("summarycanary", "evidencecanary", "ledgercanary", "envcanary"):
                self.assertNotIn(canary, combined)
            self.assertNotIn('".env"', combined)
            self.assertIn("[REDACTED_SECRET]", combined)

    def test_morning_lists_keep_and_maybe(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            self.engine().write_morning(
                ledger, "quiet",
                [result("tests-001", "KEEP", summary="Keep this"), result("docs-001", "MAYBE", summary="Maybe this")],
                200, "GREEN",
            )
            brief = (ledger / "morning.md").read_text()
            self.assertIn("Good morning - here is the short version:", brief)
            self.assertIn("You do not need to read everything", brief)
            self.assertIn("Keep this [KEEP]", brief)
            self.assertIn("Maybe this [MAYBE]", brief)
            self.assertIn("Deterministically proven worker findings:", brief)
            self.assertIn("Evidence-backed candidates that still need deterministic proof:", brief)
            self.assertIn(
                f"night-shift handoff --ledger {ledger} --item 1 --agent codex --run --allow-cloud",
                brief,
            )
            self.assertIn("Teach Night Shift (one quick vote):", brief)
            self.assertIn(
                f"night-shift feedback --ledger {ledger} --item 1 --useful",
                brief,
            )
            self.assertIn(
                f"night-shift feedback --ledger {ledger} --item 1 --not-useful --note \"one short reason\"",
                brief,
            )
            self.assertIn("stays on this computer", brief)

    def test_morning_reports_current_learning_for_repo(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            feedback = [
                {"repo": "/repo", "family": "tests", "fingerprint": "one", "verdict": "useful", "feedback_delay_seconds": 4.0},
                {"repo": "/repo", "family": "docs", "fingerprint": "two", "verdict": "not-useful"},
                {"repo": "/other", "family": "tests", "fingerprint": "three", "verdict": "useful"},
            ]
            self.engine(feedback=feedback).write_morning(
                ledger, "quiet", [result()], 100, "GREEN", {"status": "ok", "repo": "/repo"}
            )
            brief = (ledger / "morning.md").read_text()
            self.assertIn(
                "Learning signals for this repo: useful=1 not useful=1 history events=2",
                brief,
            )
            self.assertIn("Review timing signals: 1 vote(s), average 4 seconds", brief)

    def test_morning_carries_last_votes_forward_without_leaking_notes(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            feedback = [
                {
                    "repo": "/repo", "family": "tests", "fingerprint": "one",
                    "verdict": "useful", "note": "great test; Authorization: Bearer secret-value-123456",
                    "created_at": "2026-07-14T01:00:00+00:00",
                },
                {
                    "repo": "/repo", "family": "docs", "fingerprint": "two",
                    "verdict": "not-useful", "note": "too generic",
                    "created_at": "2026-07-14T02:00:00+00:00",
                },
            ]
            self.engine(feedback=feedback).write_morning(
                ledger, "quiet", [result()], 100, "GREEN", {"status": "ok", "repo": "/repo"}
            )
            brief = (ledger / "morning.md").read_text()
            self.assertIn("What I learned from your last votes:", brief)
            self.assertIn("You marked tests useful", brief)
            self.assertIn("I will look for more work like this.", brief)
            self.assertIn("You marked docs not-useful", brief)
            self.assertIn("I will cool this kind of work down.", brief)
            self.assertIn("[REDACTED_SECRET]", brief)
            self.assertNotIn("secret-value-123456", brief)

    def test_morning_falls_back_to_factual_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            rejected = result(score="REJECT")
            rejected["quality_reasons"] = ["cited line does not match the pinned source"]
            self.engine().write_morning(
                ledger, "quiet", [rejected], 100, "GREEN",
                {"status": "ok", "recent_files": ["README.md", "bin/night-shift"], "test_commands": ["python3 -m unittest"], "branch": "main", "head": "abc"},
            )
            brief = (ledger / "morning.md").read_text()
            self.assertIn("Recent code/test surface: README.md, bin/night-shift", brief)
            self.assertIn("Detected verification command", brief)
            self.assertIn("dropped because: cited line does not match the pinned source", brief)
            self.assertIn("What I checked:", brief)
            self.assertNotIn("Three useful choices:", brief)

    def test_empty_grounded_run_does_not_blame_compute_setup(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            self.engine().write_morning(
                ledger, "night-shift", [], 100, "GREEN", {"status": "ok"}
            )
            brief = (ledger / "morning.md").read_text()
            self.assertIn("Status: YELLOW", brief)
            self.assertIn("nothing was strong enough to ask an AI", brief)
            self.assertNotIn("Fix the startup gate", brief)


class PortfolioReportingTests(unittest.TestCase):
    def engine(self, root: Path) -> PortfolioReportEngine:
        return PortfolioReportEngine(root / "history.jsonl", lambda label: label.split("-", 1)[0])

    def test_snapshot_and_empty_brief_are_owned_by_module(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = self.engine(root)
            engine.write_snapshot(root, [{
                "slug": "owner/repo", "score": 42,
                "signals": {"prs": [1], "issues": [], "failed_runs": []},
            }])
            engine.write_brief(root, [], "GREEN")
            self.assertIn("owner/repo", (root / "portfolio.md").read_text())
            self.assertEqual(json.loads((root / "morning-items.json").read_text()), [])
            self.assertIn("Status: GREEN", (root / "morning.md").read_text())

    def test_morning_items_returns_rank_then_name_sorted_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            rows = {}
            for repo, rank, score in (
                ("owner/second", "2", 20),
                ("owner/first", "1", 10),
                ("owner/tie", "2", 30),
            ):
                child = root / repo.replace("/", "-")
                child.mkdir()
                (child / "work-queue.json").write_text(json.dumps([{
                    "key": f"tests:{repo}", "labels": ["tests"], "score": "MAYBE",
                    "summary": f"Check {repo}", "evidence": "src/app.py:1",
                    "files": ["src/app.py"], "tests": "python3 -m unittest",
                }]))
                rows[repo] = {
                    "portfolio_rank": rank, "portfolio_score": score,
                    "ledger": str(child), "portfolio_reason": "recent activity",
                }
            items = self.engine(root).morning_items(rows)
            self.assertEqual([item["repo"] for item in items], [
                "owner/first", "owner/tie", "owner/second",
            ])
            self.assertEqual(items[1]["summary"], "Check owner/tie")

    def test_snapshot_preserves_each_cycle_compactly(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            engine = self.engine(root)
            engine.write_snapshot(root, [{
                "slug": "owner/first", "score": 100, "primary": True,
                "checkout": "/cache/first",
                "signals": {"prs": [], "issues": [], "failed_runs": []},
            }], cycle=1)
            engine.write_snapshot(root, [{
                "slug": "owner/new-failure", "score": 500, "primary": False,
                "checkout": "/cache/new-failure",
                "signals": {"prs": [], "issues": [], "failed_runs": [{"id": 1}]},
            }], cycle=2)
            rows = [
                json.loads(line)
                for line in (root / "portfolio-snapshots.jsonl").read_text().splitlines()
            ]
            self.assertEqual([row["cycle"] for row in rows], [1, 2])
            self.assertEqual(rows[1]["repositories"][0]["slug"], "owner/new-failure")
            self.assertEqual(rows[1]["repositories"][0]["failed_runs"], 1)
            self.assertNotIn("signals", rows[1]["repositories"][0])

    def test_snapshot_history_is_bounded_and_keeps_latest(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "portfolio-snapshots.jsonl"
            for cycle in range(1, 5):
                PortfolioReportEngine.append_bounded_snapshot(
                    path, {"cycle": cycle}, limit=2
                )
            rows = [json.loads(line) for line in path.read_text().splitlines()]
            self.assertEqual(rows, [{"cycle": 3}, {"cycle": 4}])

    def test_brief_materializes_exact_child_choice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            child = root / "child"
            child.mkdir()
            (child / "work-queue.json").write_text(json.dumps([{
                "key": "issue-42:tests:patch-plan", "labels": ["issue-42"],
                "fingerprint": "fingerprint", "source_ref": "a" * 40,
                "summary": "Repair issue 42", "score": "MAYBE",
                "evidence": "src/app.py:12 | return value",
                "files": ["src/app.py", "tests/test_app.py"],
                "tests": "python3 -m unittest tests.test_app",
                "proof": "/tmp/proof.json",
            }]))
            self.engine(root).write_brief(root, [{
                "repo": "owner/repo", "checkout": str(root), "ledger": str(child),
                "new_tasks": 1,
            }], "GREEN")
            item = json.loads((root / "morning-items.json").read_text())[0]
            self.assertEqual(item["child_ledger"], str(child))
            self.assertEqual(item["fingerprint"], "fingerprint")
            self.assertEqual(item["source_ref"], "a" * 40)
            self.assertEqual(item["evidence"], "src/app.py:12 | return value")
            self.assertEqual(item["files"], ["src/app.py", "tests/test_app.py"])
            self.assertEqual(item["verification"], "python3 -m unittest tests.test_app")
            self.assertEqual(item["proof"], "/tmp/proof.json")
            self.assertIn("Status: YELLOW", (root / "morning.md").read_text())
            morning = (root / "morning.md").read_text()
            self.assertIn("Evidence: src/app.py:12 | return value", morning)
            self.assertIn("Files: src/app.py, tests/test_app.py", morning)
            self.assertIn("Verify: python3 -m unittest tests.test_app", morning)
            self.assertIn("Proof: /tmp/proof.json", morning)

    def test_morning_status_reads_valid_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "status.txt"
            path.write_text("Line 1\nStatus: GREEN\nLine 2\n", encoding="utf-8")
            from night_shift_portfolio_reporting import PortfolioReportEngine
            self.assertEqual(PortfolioReportEngine.morning_status(path), "GREEN")

    def test_brief_preserves_portfolio_priority_and_explains_selection(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            children = []
            for name, summary in (("owner/z-high", "High priority repair"), ("owner/a-low", "Lower priority repair")):
                child = root / name.replace("/", "-")
                child.mkdir()
                (child / "work-queue.json").write_text(json.dumps([{
                    "key": name + ":tests", "labels": ["tests"], "fingerprint": name,
                    "source_ref": "a" * 40, "summary": summary, "score": "MAYBE",
                    "evidence": "src/app.py:1 | return value", "files": ["src/app.py"],
                    "tests": "python3 -m unittest", "proof": "/tmp/proof.json",
                }]))
                children.append((name, child))
            self.engine(root).write_brief(root, [
                {
                    "repo": "owner/z-high", "checkout": str(root), "ledger": str(children[0][1]),
                    "new_tasks": 1, "portfolio_rank": 1, "portfolio_score": 900,
                    "portfolio_reason": "recent failing checks",
                },
                {
                    "repo": "owner/a-low", "checkout": str(root), "ledger": str(children[1][1]),
                    "new_tasks": 1, "portfolio_rank": 2, "portfolio_score": 100,
                    "portfolio_reason": "recent activity",
                },
            ], "GREEN")
            morning = (root / "morning.md").read_text()
            self.assertIn("Good morning - here is the short version:", morning)
            self.assertLess(morning.index("owner/z-high"), morning.index("owner/a-low"))
            self.assertIn("Why this repo: recent failing checks", morning)
            self.assertIn(
                f"night-shift handoff --ledger {root} --item 1 --agent codex --run --allow-cloud",
                morning,
            )
            items = json.loads((root / "morning-items.json").read_text())
            self.assertEqual([item["repo"] for item in items], ["owner/z-high", "owner/a-low"])
            self.assertEqual(items[0]["selection_reason"], "recent failing checks")

    def test_portfolio_selection_reason_explains_feedback_learning(self):
        self.assertEqual(
            PortfolioEngine.selection_reason({
                "slug": "owner/useful",
                "outcome_summary": {"useful_feedback": 1},
                "signals": {},
            }),
            "you marked recent work here useful",
        )
        self.assertEqual(
            PortfolioEngine.selection_reason({
                "slug": "owner/cooled",
                "outcome_summary": {"not_useful_feedback": 1},
                "signals": {},
            }),
            "cooling down after recent low-value work",
        )
        self.assertEqual(
            PortfolioEngine.selection_reason({
                "primary": True,
                "outcome_summary": {"useful_feedback": 1},
                "signals": {},
            }),
            "your current project; you marked recent work here useful",
        )

if __name__ == "__main__":
    unittest.main()
