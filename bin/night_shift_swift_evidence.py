"""Conservative Swift evidence for existing XCTest test strengthening."""
from __future__ import annotations

import re


SWIFT_EXTENSIONS = {".swift"}


def swift_declares_symbol(text: str, symbol: str) -> bool:
    return bool(re.search(
        rf"(?m)^\s*(?:(?:public|internal|private|fileprivate|open|final|static)\s+)*"
        rf"(?:class|struct|enum|actor|func)\s+{re.escape(symbol)}\b",
        text,
    ))


def swift_symbol_call_count_text(text: str, symbol: str) -> int:
    """Count direct calls while ignoring declarations and comments."""
    calls = 0
    for raw_line in text.splitlines():
        line = raw_line.split("//", 1)[0]
        if re.search(rf"\bfunc\s+{re.escape(symbol)}\s*\(", line):
            continue
        if re.search(rf"\b(?:class|struct|enum|actor)\s+{re.escape(symbol)}\b", line):
            continue
        calls += len(re.findall(rf"\b{re.escape(symbol)}\s*\(", line))
    return calls
