#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import shlex
from pathlib import Path
from typing import Callable

from night_shift_evidence import action_type, artifact_priority
from night_shift_feedback import latest_feedback_events
from night_shift_redaction import redact, sanitize_evidence_sources, sanitize_task_for_ledger


ACTION_THEMES = (
    ("tests", re.compile(r"\b(test|tests|fixture|fixtures|smoke|regression|coverage)\b", re.IGNORECASE)),
    ("docs", re.compile(r"\b(readme|docs?|documentation|quickstart|troubleshooting|copy|example)\b", re.IGNORECASE)),
    ("install", re.compile(r"\b(install|path|linked mode|package|doctor|setup wizard|first-run|first run)\b", re.IGNORECASE)),
    ("telemetry", re.compile(r"\b(telemetry|analytics|event|events|dashboard|posthog|sentry)\b", re.IGNORECASE)),
    ("pr-triage", re.compile(r"\b(pr|pull request|branch|merge|stale)\b", re.IGNORECASE)),
    ("safety", re.compile(r"\b(safety|privacy|secret|credential|billing|release|deploy|publish)\b", re.IGNORECASE)),
    ("cleanup", re.compile(r"\b(duplicate|dedupe|refactor|oversized|smell|cleanup|ownership)\b", re.IGNORECASE)),
)


class ReportEngine:
    def __init__(
        self,
        *,
        load_feedback: Callable[[], list[dict]],
        run_cmd: Callable[..., object],
        token_reporter: Path,
        narrow_task_files: Callable[[list[str]], list[str]],
        latest_states: Callable[[Path], dict],
    ) -> None:
        self.load_feedback = load_feedback
        self.run_cmd = run_cmd
        self.token_reporter = token_reporter
        self.narrow_task_files = narrow_task_files
        self.latest_states = latest_states

    @staticmethod
    def label_family(label: str) -> str:
        return re.sub(r"-\d{3}$", "", label)

    @staticmethod
    def summary_theme(text: str) -> str:
        text = redact(text)
        for name, regex in ACTION_THEMES:
            if regex.search(text):
                return name
        words = re.findall(r"[a-z0-9]+", text.lower())
        stop = {"the", "and", "for", "with", "that", "this", "from", "into", "night", "shift", "add", "update"}
        useful = [word for word in words if len(word) > 2 and word not in stop]
        return "-".join(useful[:4]) or "general"

    def dedupe_key(self, row: dict) -> str:
        return f"{self.label_family(row.get('label', 'task'))}:{self.summary_theme(row.get('summary', ''))}:{action_type(row.get('output', ''))}"

    def feedback_adjustment(self, key: str, repo: str = "") -> int:
        adjustment = 0
        for row in latest_feedback_events(self.load_feedback()):
            if row.get("key") != key or (repo and row.get("repo") != repo):
                continue
            adjustment += 20 if row.get("verdict") == "useful" else -120
        return max(-240, min(40, adjustment))

    def feedback_snapshot(self, repo: str = "") -> tuple[int, int, int, int, float | None]:
        """Return current votes, history, and optional review timing for one repo."""
        history = self.load_feedback()
        if repo:
            history = [row for row in history if row.get("repo") == repo]
        current = latest_feedback_events(history)
        delays = []
        for row in current:
            try:
                delay = float(row.get("feedback_delay_seconds"))
            except (TypeError, ValueError):
                continue
            if delay >= 0:
                delays.append(delay)
        return (
            sum(row.get("verdict") == "useful" for row in current),
            sum(row.get("verdict") == "not-useful" for row in current),
            len(history),
            len(delays),
            round(sum(delays) / len(delays), 3) if delays else None,
        )

    @staticmethod
    def ranked_results(results: list[dict], include_reject: bool = False) -> list[dict]:
        rows = [row for row in results if include_reject or row["score"] != "REJECT"]
        return sorted(rows, key=lambda row: (-artifact_priority(row), row["score"], row["label"]))

    def deduped_work_items(self, results: list[dict], limit: int | None = None) -> list[dict]:
        clusters: dict[str, dict] = {}
        for row in self.ranked_results(results):
            key = self.dedupe_key(row)
            if key not in clusters:
                clusters[key] = {
                    "key": key, "primary": row, "supporting": [], "lanes": set(), "labels": set(),
                    "priority": artifact_priority(row) + self.feedback_adjustment(key, row.get("repo", "")),
                    "action_type": action_type(row.get("output", "")),
                    "theme": self.summary_theme(row.get("summary", "")),
                }
            cluster = clusters[key]
            cluster["supporting"].append(row)
            cluster["lanes"].add(row.get("lane", "unknown"))
            cluster["labels"].add(row.get("label", "unknown"))
            cluster["priority"] = max(
                cluster["priority"], artifact_priority(row) + self.feedback_adjustment(key, row.get("repo", ""))
            ) + min(len(cluster["supporting"]) - 1, 5)
            if artifact_priority(row) > artifact_priority(cluster["primary"]):
                cluster["primary"] = row
        items = sorted(clusters.values(), key=lambda item: (-item["priority"], item["key"]))
        for item in items:
            item["lanes"] = sorted(item["lanes"])
            item["labels"] = sorted(item["labels"])
        return items[:limit] if limit else items

    @staticmethod
    def token_totals_by_lane(results: list[dict]) -> dict[str, dict[str, int]]:
        totals: dict[str, dict[str, int]] = {}
        for row in results:
            lane = row["lane"]
            totals.setdefault(lane, {"calls": 0, "input": 0, "output": 0, "total": 0})
            totals[lane]["calls"] += 1
            totals[lane]["input"] += int(row.get("input_tokens") or 0)
            totals[lane]["output"] += int(row.get("output_tokens") or 0)
            totals[lane]["total"] += int(row.get("tokens") or 0)
        return totals

    def write_harvest(self, ledger: Path, results: list[dict]) -> None:
        lines = ["# Harvest", ""]
        for row in results:
            row["priority"] = artifact_priority(row)
        groups = {score: [row for row in results if row["score"] == score] for score in ("KEEP", "MAYBE", "REJECT")}
        lines.extend([f"KEEP: {len(groups['KEEP'])}", f"MAYBE: {len(groups['MAYBE'])}", f"REJECT: {len(groups['REJECT'])}", "", "## Top Ranked Artifacts", ""])
        ranked = self.ranked_results(results)
        if ranked:
            lines.extend(["| rank | score | priority | lane | label | action | artifact |", "| ---: | --- | ---: | --- | --- | --- | --- |"])
            for index, row in enumerate(ranked[:10], 1):
                summary = redact(row["summary"]).replace("|", "\\|")
                lines.append(f"| {index} | {row['score']} | {row['priority']} | {row['lane']} | {row['label']} | {summary} | {row['artifact']} |")
        else:
            lines.append("No KEEP or MAYBE artifacts survived scoring.")
        lines.extend(["", "## Deduped Work Queue", ""])
        items = self.deduped_work_items(results, limit=10)
        if items:
            lines.extend(["| rank | action | support | lanes | candidate | primary artifact |", "| ---: | --- | ---: | --- | --- | --- |"])
            for index, item in enumerate(items, 1):
                row = item["primary"]
                summary = redact(row["summary"]).replace("|", "\\|")
                lines.append(f"| {index} | {item['action_type']} | {len(item['supporting'])} | {', '.join(item['lanes'])} | {summary} | {row['artifact']} |")
        else:
            lines.append("No work queue items survived dedupe.")
        lines.extend(["", "## Full Scorecard", "", "| score | priority | lane | label | tokens | artifact |", "| --- | ---: | --- | --- | ---: | --- |"])
        for row in sorted(results, key=lambda value: (-value["priority"], value["label"])):
            lines.append(f"| {row['score']} | {row['priority']} | {row['lane']} | {row['label']} | {row['tokens']} | {row['artifact']} |")
        lines.append("")
        for score, rows in groups.items():
            lines.extend([f"## {score} Summary", ""])
            if not rows:
                lines.extend(["- None.", ""])
                continue
            for row in sorted(rows, key=lambda value: (-value["priority"], value["label"]))[:12]:
                lines.append(f"- {row['label']} ({row['lane']}, priority {row['priority']}): {redact(row['summary'])}")
            lines.append("")
        (ledger / "harvest.md").write_text("\n".join(lines), encoding="utf-8")

    def write_outcome_metrics(self, ledger: Path, results: list[dict], skipped: list[dict]) -> None:
        tokens = sum(int(row.get("tokens") or 0) for row in results)
        accepted = sum(1 for row in results if row.get("score") in {"KEEP", "MAYBE"})
        feedback_history = self.load_feedback()
        current_feedback = latest_feedback_events(feedback_history)
        metrics = {
            "attempted": len(results), "accepted_candidates": accepted,
            "rejected": sum(1 for row in results if row.get("score") == "REJECT"),
            "pre_model_skips": sum(1 for row in skipped if row.get("category") == "pre-model"),
            "feedback_skips": sum(1 for row in skipped if row.get("category") == "feedback"),
            "cooldown_or_repeat_skips": sum(1 for row in skipped if row.get("category") in {"cooldown", "repeat"}),
            "estimated_tokens": tokens,
            "accepted_per_1000_tokens": round(accepted * 1000 / tokens, 4) if tokens else 0,
            "patches_promoted": 0,
            "human_feedback_events": len(feedback_history),
            "current_feedback_preferences": len(current_feedback),
            "current_useful_preferences": sum(
                row.get("verdict") == "useful" for row in current_feedback
            ),
            "current_not_useful_preferences": sum(
                row.get("verdict") == "not-useful" for row in current_feedback
            ),
        }
        (ledger / "outcome-metrics.json").write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def write_task_lifecycle_summary(self, ledger: Path) -> None:
        counts: dict[str, int] = {}
        for event in self.latest_states(ledger / "task-lifecycle.jsonl").values():
            counts[event["state"]] = counts.get(event["state"], 0) + 1
        lines = ["# Task Lifecycle", ""]
        for state in ("DISCOVERED", "GAP_CONFIRMED", "REPRODUCED", "DIAGNOSED", "PATCHED", "VERIFIED", "REVIEWED", "PROMOTED", "REJECTED"):
            lines.append(f"- {state}: {counts.get(state, 0)}")
        (ledger / "task-lifecycle.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def write_work_queue(self, ledger: Path, results: list[dict]) -> list[dict]:
        items = self.deduped_work_items(results, limit=12)
        serializable = []
        for item in items:
            row = sanitize_task_for_ledger(item["primary"])
            serializable.append({
                "rank": len(serializable) + 1, "key": item["key"], "action_type": item["action_type"],
                "theme": item["theme"], "supporting_artifacts": len(item["supporting"]), "lanes": item["lanes"],
                "labels": item["labels"], "ladder": row.get("ladder", "strengthen"),
                "proof_kind": row.get("proof_kind", "source"), "executable": bool(row.get("executable", False)),
                "source_ref": row.get("source_ref", ""), "fingerprint": row.get("fingerprint", ""),
                "kind": row.get("kind", ""),
                "evidence_sources": sanitize_evidence_sources(row.get("evidence_sources", {})),
                "semantic_contract": row.get("semantic_contract", {}),
                "verification_commands": row.get("verification_commands", []), "priority": item["priority"],
                "summary": redact(row["summary"]), "score": row["score"], "evidence": redact(row.get("evidence", "")),
                "files": row.get("files", []), "tests": row.get("tests", ""),
                "expected_result": row.get("expected_result", ""), "primary_artifact": row["artifact"],
                "proof": row.get("proof", ""),
            })
        (ledger / "work-queue.json").write_text(json.dumps(serializable, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        lines = ["# Work Queue", ""]
        if not serializable:
            lines.append("No usable work queue items survived scoring and dedupe.")
        for item in serializable:
            lines.extend([f"## {item['rank']}. {item['summary']}", "", f"- Action: {item['action_type']}", f"- Score: {item['score']}", f"- Support: {item['supporting_artifacts']} artifact(s)", f"- Lanes: {', '.join(item['lanes']) or 'unknown'}", f"- Evidence: {item['evidence'] or 'not captured'}", f"- Files: {', '.join(item['files']) or 'none'}", f"- Verify: `{item['tests']}`" if item["tests"] else "- Verify: not captured", f"- Expected: {item['expected_result'] or 'not captured'}", f"- Primary artifact: {item['primary_artifact']}", ""])
        (ledger / "work-queue.md").write_text("\n".join(lines), encoding="utf-8")
        return items

    def write_token_report(self, ledger: Path, results: list[dict]) -> str:
        proofs: list[str] = []
        for row in results:
            proofs.extend(row.get("proofs") or ([row["proof"]] if row.get("proof") else []))
        if proofs:
            result = self.run_cmd([self.token_reporter, *proofs], timeout=120)
            text = result.stdout or result.stderr or "No token report output.\n"
        else:
            text = "No delegate proof paths captured.\n"
        (ledger / "token-report.txt").write_text(text, encoding="utf-8")
        return text

    @staticmethod
    def run_status(results: list[dict], target_tokens: int, overall: str, mode: str = "night-shift") -> str:
        if overall == "RED": return "RED"
        if not results: return "YELLOW"
        failed = any(row["rc"] != 0 or row["timed_out"] for row in results)
        useful = any(row["score"] == "KEEP" for row in results)
        if failed or not useful: return "YELLOW"
        if mode == "afterburner" and sum(row["tokens"] for row in results) < target_tokens: return "YELLOW"
        return "GREEN"

    def factual_change_surface(self, scan: dict | None) -> list[str]:
        if not scan or scan.get("status") != "ok": return []
        lines: list[str] = []
        changed = self.narrow_task_files(scan.get("recent_files") or [])
        if changed: lines.append(f"- Recent code/test surface: {', '.join(changed)}")
        commands = scan.get("test_commands") or []
        if commands: lines.append(f"- Detected verification command: `{commands[0]}`")
        branch, head = scan.get("branch"), scan.get("head")
        if branch or head: lines.append(f"- Repository revision: {branch or '(detached)'} at {head or 'unknown'}")
        return lines

    def write_morning(self, ledger: Path, mode: str, results: list[dict], target_tokens: int, overall: str, scan: dict | None = None) -> None:
        local = [row for row in results if row["lane"] == "local"]
        windows = [row for row in results if row["lane"] == "windows"]
        for row in results: row["priority"] = artifact_priority(row)
        total_tokens = sum(row["tokens"] for row in results)
        keep = sum(row["score"] == "KEEP" for row in results)
        maybe = sum(row["score"] == "MAYBE" for row in results)
        reject = sum(row["score"] == "REJECT" for row in results)
        status = self.run_status(results, target_tokens, overall, mode)
        work_items = self.deduped_work_items(results, limit=3)
        factual = self.factual_change_surface(scan)
        feedback_useful, feedback_not_useful, feedback_history, feedback_timing_count, feedback_delay_average = self.feedback_snapshot(
            str((scan or {}).get("repo") or "")
        )
        if work_items: first_action = work_items[0]["primary"]["summary"]
        elif results: first_action = factual[0].removeprefix("- ") if factual else "No evidence-backed item survived. Review the deterministic repo scan before another model run."
        elif scan and scan.get("status") == "ok":
            first_action = (
                "I checked the repo, but nothing was strong enough to ask an AI to work on safely yet. "
                "That is okay - I will try again after new repo or GitHub activity."
            )
        else:
            first_action = "Fix the startup gate or run with reachable local/Windows lanes."
        try: task_skips = json.loads((ledger / "task-skips.json").read_text(encoding="utf-8"))
        except (OSError, ValueError): task_skips = []
        lines = [
            "# Morning Brief", "", f"Status: {status}", "",
            "Good morning - here is the short version:", "",
            "Start here:", f"- {first_action}", "", "Three useful choices:",
        ]
        if work_items:
            for index, item in enumerate(work_items, 1):
                row = item["primary"]
                lines.append(f"{index}. {row['summary']} [{row['score']}]")
                if row.get("evidence"): lines.append(f"   Evidence: {row['evidence']}")
                if row.get("files"): lines.append(f"   Files: {', '.join(row['files'][:5])}")
                if row.get("tests"): lines.append(f"   Verify: `{row['tests']}`")
                lines.append(f"   Proof: {row['artifact']}")
        elif factual:
            lines.append("1. I did not keep a model draft because it did not meet the proof bar. Here is what I verified:")
            lines.extend(f"   {line}" for line in factual)
        else:
            lines.append("1. I did not keep a draft this time. Check the startup gate before another run.")
        all_items = self.deduped_work_items(results)
        lines.extend(["", "Run totals:", f"- Mode: {mode}", f"- Startup gate: {overall}", f"- Local loops: {len(local)}", f"- Windows loops: {len(windows)}", f"- Estimated local+Windows tokens: {total_tokens}", f"- Token target: {target_tokens}", f"- Token target reached: {'yes' if total_tokens >= target_tokens else 'no'}", f"- Artifacts: KEEP={keep}, MAYBE={maybe}, REJECT={reject}", f"- Weak signals skipped before model calls: {sum(row.get('category') == 'pre-model' for row in task_skips)}", f"- User-rejected task families skipped: {sum(row.get('category') == 'feedback' for row in task_skips)}", f"- Evidence-backed candidates awaiting proof: {sum(item['primary']['score'] == 'MAYBE' for item in work_items)}", f"- Unique work queue items: {len(all_items)}", f"- Learning signals for this repo: useful={feedback_useful} not useful={feedback_not_useful} history events={feedback_history}"])
        if feedback_timing_count:
            lines.append(
                f"- Review timing signals: {feedback_timing_count} vote(s), average {feedback_delay_average:g} seconds from brief view to vote"
            )
        lines.extend(["", "Token totals by lane:"])
        totals = self.token_totals_by_lane(results)
        for lane in sorted(totals):
            row = totals[lane]
            lines.append(f"- {lane}: calls={row['calls']} input~{row['input']} output~{row['output']} total~{row['total']}")
        if not totals: lines.append("- none")
        ready = [item for item in all_items if item["primary"]["score"] == "KEEP"]
        lines.extend(["", "Deterministically proven worker findings:"])
        lines.extend(f"- {item['action_type']}: {item['primary']['summary']} ({len(item['supporting'])} supporting artifact(s))" for item in ready[:5])
        if not ready: lines.append("- None.")
        maybe_items = [item for item in all_items if item["primary"]["score"] == "MAYBE"]
        lines.extend(["", "Evidence-backed candidates that still need deterministic proof:"])
        lines.extend(f"- {item['action_type']}: {item['primary']['summary']} ({len(item['supporting'])} supporting artifact(s))" for item in maybe_items[:5])
        if not maybe_items: lines.append("- None.")
        lines.extend(["", "REJECT summary:"])
        rejected = sorted((row for row in results if row["score"] == "REJECT"), key=lambda row: (-row["priority"], row["label"]))
        for row in rejected[:5]:
            reasons = [redact(str(reason)) for reason in row.get("quality_reasons", []) if str(reason).strip()]
            explanation = "; ".join(reasons[:2]) or "the response did not meet the evidence or safety checks"
            lines.append(f"- {row['label']}: {row['summary']} (dropped because: {explanation})")
        if reject == 0: lines.append("- None.")
        lines.extend([
            "", "Needs user review:",
            "- You do not need to read everything. Start with choice 1; worker output is a draft, not the final truth.",
        ])
        if work_items:
            ledger_arg = shlex.quote(str(ledger))
            lines.append(
                "- One-action independent review (read-only cloud; this command is explicit consent): "
                f"`night-shift handoff --ledger {ledger_arg} --item 1 --agent codex --run --allow-cloud`"
            )
            lines.extend([
                "",
                "Teach Night Shift (one quick vote):",
                f"- If choice 1 would save you time: `night-shift feedback --ledger {ledger_arg} --item 1 --useful`",
                f"- If it missed the mark: `night-shift feedback --ledger {ledger_arg} --item 1 --not-useful --note \"one short reason\"`",
                "- This stays on this computer and changes future rankings for this repo.",
            ])
        lines.extend(["- Treat manual hardware/audio proof as UNKNOWN unless a human verified it.", "", "Safety:", "- No merges, releases, tags, notarization, deploys, appcast/cask updates, billing, credentials, or user-file cleanup were performed by this command.", "- Local and Windows outputs are drafts, not truth.", "", "Proof files:", f"- Repo scan: {ledger / 'repo-scan.md'}", f"- Work queue: {ledger / 'work-queue.md'}", f"- Harvest: {ledger / 'harvest.md'}", f"- Token report: {ledger / 'token-report.txt'}"])
        (ledger / "morning.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
