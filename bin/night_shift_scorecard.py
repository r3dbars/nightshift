"""Parse and gate the source-backed Night Shift quality scorecard."""
from __future__ import annotations

import re
from pathlib import Path


SCORE_ROW = re.compile(r"^\|\s*(?P<dimension>[^|]+?)\s*\|\s*(?P<score>\d+)\s*\|")


def parse_scores(text: str) -> list[dict[str, int | str]]:
    rows: list[dict[str, int | str]] = []
    for line in text.splitlines():
        match = SCORE_ROW.match(line)
        if not match or match.group("dimension").strip().lower() == "dimension":
            continue
        rows.append({"dimension": match.group("dimension").strip(), "score": int(match.group("score"))})
    return rows


def below_target(rows: list[dict[str, int | str]], target: int = 95) -> list[dict[str, int | str]]:
    return [row for row in rows if int(row["score"]) < target]


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Check whether every Night Shift score meets the target.")
    parser.add_argument("--scorecard", type=Path, default=Path("docs/quality-scorecard.md"))
    parser.add_argument("--target", type=int, default=95)
    args = parser.parse_args(argv)
    try:
        rows = parse_scores(args.scorecard.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"NIGHTSHIFT_SCORECARD: RED | cannot read {args.scorecard}: {exc}")
        return 2
    if not rows:
        print(f"NIGHTSHIFT_SCORECARD: RED | no score rows found in {args.scorecard}")
        return 2
    below = below_target(rows, args.target)
    status = "GREEN" if not below else "YELLOW"
    print(
        f"NIGHTSHIFT_SCORECARD: {status} | target={args.target} "
        f"pass={len(rows) - len(below)} below={len(below)} total={len(rows)}"
    )
    for row in below:
        print(f"- {row['dimension']}: {row['score']}/{args.target}")
    return 0 if not below else 1


if __name__ == "__main__":
    raise SystemExit(main())
