import json
import tempfile
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_queue import (
    QueueEvidenceIndex,
    RepoRevisionAdapter,
    TASK_LADDER,
    build_repo_work_queue,
    contains_identifier,
    goal_semantic_contract,
    is_test_path,
    python_owned_methods,
)
from night_shift_portfolio import PortfolioEngine


class QueueEvidenceTests(unittest.TestCase):
    def test_python_owned_methods_ignore_top_level_and_private_functions(self):
        self.assertEqual(
            python_owned_methods(
                "def top(): pass\nclass Engine:\n    def run(self): pass\n    def _private(self): pass\n"
            ),
            [("Engine", "run")],
        )

    def test_goal_semantic_contract_preserves_explicit_outcome_and_order_requirements(self):
        contract = goal_semantic_contract(
            "Add a test proving ordered remove and prune calls and both boolean return outcomes"
        )
        self.assertEqual(contract["minimum_target_invocations"], 2)
        self.assertEqual(contract["required_boolean_outcomes"], [True, False])
        self.assertEqual(contract["ordered_terms"], ["remove", "prune"])
        self.assertEqual(goal_semantic_contract("Add a cleanup test"), {})
        self.assertNotIn(
            "required_boolean_outcomes",
            goal_semantic_contract("Test the truthful and falsehood labels"),
        )

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

    def test_python_method_coverage_gap_includes_owner_aware_invocation_and_source_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "src.py").write_text(
                "class Engine:\n    def cleanup(self):\n        return True\n", encoding="utf-8"
            )
            (repo / "test_src.py").write_text("def test_other(): pass\n", encoding="utf-8")
            scan = {
                "tracked_files": ["src.py", "test_src.py"], "source_files": ["src.py"],
                "test_files": ["test_src.py"], "coverage_test_files": ["test_src.py"],
            }
            gap = QueueEvidenceIndex(repo, scan).coverage_gaps(["src.py"])[0]
            self.assertEqual(gap[:2], ("src.py", "cleanup"))
            evidence = gap[2]
            invocation = next(value for key, value in evidence.items() if key.startswith("invocation-index/"))
            self.assertIn("owner=Engine", invocation)
            self.assertIn("analysis=python-ast", invocation)
            self.assertIn("call_matches=0", invocation)
            self.assertTrue(any(key.startswith("goal-source/") for key in evidence))

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


class BuildRepoWorkQueueTests(unittest.TestCase):
    def _run_cmd(self, argv, cwd=None, timeout=60, env=None, pid_log=None):
        return SimpleNamespace(rc=1, stdout="", stderr="")

    def _detect_test_commands(self, repo, tracked, source_ref=""):
        return []

    def test_quiet_mode_limits_queue_to_ten_and_ranks_by_ladder(self):
        scan = {
            "recent_files": ["src/app.py"],
            "source_files": ["src/app.py"],
            "test_files": ["test_app.py"],
            "doc_files": ["README.md"],
            "todo_sample": ["src/app.py:3: TODO fix this"],
            "test_commands": ["python -m pytest"],
            "tracked_files": ["src/app.py", "test_app.py", "README.md"],
        }
        queue = build_repo_work_queue(
            None, scan, "quiet", "brief",
            run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
        )
        self.assertLessEqual(len(queue), 10)
        priorities = [item["selection_priority"] for item in queue]
        self.assertEqual(priorities, sorted(priorities, reverse=True))
        for item in queue:
            self.assertIn(item["ladder"], TASK_LADDER)
            self.assertEqual(item["ladder_priority"], TASK_LADDER[item["ladder"]])

    def test_slugs_are_deduped_and_insertion_order_preserved_within_ties(self):
        scan = {
            "recent_files": [],
            "source_files": [f"src/f{i}.py" for i in range(6)],
            "test_files": [],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": [],
            "tracked_files": [f"src/f{i}.py" for i in range(6)],
        }
        queue = build_repo_work_queue(
            None, scan, "night-shift", "brief",
            run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
        )
        slugs = [item["slug"] for item in queue]
        self.assertEqual(len(slugs), len(set(slugs)))
        source_map_items = [item for item in queue if item["slug"].startswith("source-map-")]
        self.assertEqual([item["slug"] for item in source_map_items], sorted(item["slug"] for item in source_map_items))

    def test_goal_guidance_inserts_mission_brief_first_by_priority(self):
        scan = {
            "recent_files": ["src/app.py"],
            "source_files": ["src/app.py"],
            "test_files": [],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": [],
            "tracked_files": ["src/app.py"],
        }
        queue = build_repo_work_queue(
            None, scan, "quiet", "brief", guidance="goal", goal_text="Fix the login bug",
            run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
        )
        self.assertEqual(queue[0]["slug"], "mission-brief")
        self.assertEqual(queue[0]["ladder"], "repair")

    def test_goal_guidance_grounding_finds_named_symbol_outside_recent_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "recent.py").write_text("def unrelated():\n    return 1\n", encoding="utf-8")
            (repo / "drafts.py").write_text(
                "class DraftEngine:\n    def cleanup(self):\n        return True\n", encoding="utf-8"
            )
            (repo / "test_drafts.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
            scan = {
                "recent_files": ["recent.py"],
                "source_files": ["recent.py", "drafts.py"],
                "test_files": ["test_drafts.py"],
                "doc_files": [], "todo_sample": [],
                "test_commands": ["python -m unittest"],
                "tracked_files": ["recent.py", "drafts.py", "test_drafts.py"],
            }
            queue = build_repo_work_queue(
                repo, scan, "afterburner", "draft-local", guidance="goal",
                goal_text="Add a behavioral test for DraftEngine.cleanup return value",
                run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
            )
            mission = next(item for item in queue if item["slug"] == "mission-brief")
            self.assertIn("drafts.py", mission["files"])
            self.assertIn("test_drafts.py", mission["files"])
            source_evidence = "\n".join(
                value for key, value in mission["evidence_sources"].items()
                if key.startswith("goal-source/")
            )
            self.assertIn("source_file=drafts.py", source_evidence)
            evidence = "\n".join(mission["evidence_sources"].values())
            self.assertIn("symbol=cleanup", evidence)
            self.assertIn("symbol=cleanup call_matches=0", evidence)
            self.assertIn("owner=DraftEngine", evidence)
            self.assertIn("analysis=python-ast", evidence)
            self.assertIn("def cleanup(self):", evidence)
            self.assertIn("return True", evidence)
            self.assertTrue(mission["executable"])
            self.assertEqual(
                mission["signal"], "Add a behavioral test for DraftEngine.cleanup return value"
            )

            changed = build_repo_work_queue(
                repo, scan, "afterburner", "draft-local", guidance="goal",
                goal_text="Add a behavioral test for DraftEngine.cleanup failure path",
                run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
            )
            changed_mission = next(item for item in changed if item["slug"] == "mission-brief")
            self.assertNotEqual(mission["signal"], changed_mission["signal"])
            self.assertNotEqual(
                PortfolioEngine.task_fingerprint("owner/repo", "a" * 40, mission),
                PortfolioEngine.task_fingerprint("owner/repo", "a" * 40, changed_mission),
            )

    def test_invocation_gap_is_owner_aware_and_understands_import_aliases(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "drafts.py").write_text(
                "class DraftEngine:\n    def cleanup(self):\n        return True\n", encoding="utf-8"
            )
            (repo / "test_drafts.py").write_text(
                "from drafts import DraftEngine as DE\n"
                "class Other:\n    def cleanup(self): pass\n"
                "Other().cleanup()\n"
                "engine = DE()\n"
                "engine.cleanup()\n",
                encoding="utf-8",
            )
            index = QueueEvidenceIndex(repo, {
                "tracked_files": ["drafts.py", "test_drafts.py"],
                "source_files": ["drafts.py"], "test_files": ["test_drafts.py"],
                "coverage_test_files": ["test_drafts.py"],
            })
            evidence = "\n".join(index.invocation_gap("drafts.py", "cleanup", "DraftEngine").values())
            self.assertIn("symbol=cleanup call_matches=1", evidence)

    def test_incomplete_invocation_index_blocks_model_readiness(self):
        task = {
            "slug": "mission-brief", "kind": "mission", "files": ["src.py"],
            "verification_commands": ["python -m unittest"],
            "evidence_sources": {
                "invocation-index/src-cleanup.txt": "scan_complete=false",
                "coverage-index/other.txt": "scan_complete=true\nidentifier_matches=0",
            },
        }
        from night_shift_selection import model_task_readiness_reasons
        self.assertIn(
            "named-symbol invocation index is incomplete",
            model_task_readiness_reasons(task, "afterburner", "test cleanup"),
        )

    def test_empty_test_corpus_never_claims_complete_invocation_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "drafts.py").write_text(
                "class DraftEngine:\n    def cleanup(self): return True\n", encoding="utf-8"
            )
            index = QueueEvidenceIndex(repo, {
                "tracked_files": ["drafts.py"], "source_files": ["drafts.py"],
                "test_files": [], "coverage_test_files": [],
            })
            evidence = "\n".join(index.invocation_gap("drafts.py", "cleanup", "DraftEngine").values())
            self.assertIn("tracked_test_files=0", evidence)
            self.assertIn("scan_complete=false", evidence)

    def test_non_dotted_goal_never_enables_ast_backed_execution(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("def cleanup():\n    return True\n", encoding="utf-8")
            (repo / "test_app.py").write_text("def test_other():\n    pass\n", encoding="utf-8")
            scan = {
                "recent_files": ["app.py"], "source_files": ["app.py"],
                "test_files": ["test_app.py"], "coverage_test_files": ["test_app.py"],
                "tracked_files": ["app.py", "test_app.py"], "doc_files": [],
                "todo_sample": [], "test_commands": ["python -m unittest"],
            }
            queue = build_repo_work_queue(
                repo, scan, "afterburner", "draft-local", guidance="goal",
                goal_text="Add a cleanup behavioral test",
                run_cmd=self._run_cmd, detect_test_commands=self._detect_test_commands,
            )
            mission = next(item for item in queue if item["slug"] == "mission-brief")
            self.assertFalse(mission["executable"])

    def test_failed_ci_uses_injected_run_cmd_and_detect_test_commands(self):
        calls = []

        def run_cmd(argv, cwd=None, timeout=60, env=None, pid_log=None):
            calls.append(argv)
            if argv[:3] == ["git", "cat-file", "-e"]:
                return SimpleNamespace(rc=0, stdout="", stderr="")
            if argv[:3] == ["git", "ls-tree", "-r"]:
                return SimpleNamespace(rc=0, stdout="src/app.py\n", stderr="")
            return SimpleNamespace(rc=0, stdout="", stderr="")

        detect_calls = []

        def detect_test_commands(repo, tracked, source_ref=""):
            detect_calls.append((repo, tracked, source_ref))
            return ["custom test command"]

        source_ref = "a" * 40
        scan = {
            "recent_files": [],
            "source_files": [],
            "test_files": [],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": ["fallback test"],
            "tracked_files": [],
            "github_failed_runs_raw": json.dumps([
                {"databaseId": 42, "headSha": source_ref, "headBranch": "fix-branch", "updatedAt": "2026-01-01T00:00:00Z"}
            ]),
            "github_failed_logs_raw": json.dumps([
                {"run": {"databaseId": 42}, "log": "AssertionError in src/app.py"}
            ]),
        }
        queue = build_repo_work_queue(
            Path("/repo"), scan, "quiet", "brief",
            run_cmd=run_cmd, detect_test_commands=detect_test_commands,
        )
        failed_ci = next(item for item in queue if item["slug"] == "failed-ci-42")
        self.assertEqual(failed_ci["verification_commands"], ["custom test command"])
        self.assertEqual(failed_ci["source_ref"], source_ref)
        self.assertTrue(detect_calls)
        self.assertTrue(any(argv[:3] == ["git", "ls-tree", "-r"] for argv in calls))


if __name__ == "__main__":
    unittest.main()
