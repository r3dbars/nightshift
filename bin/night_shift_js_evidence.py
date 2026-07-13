"""Conservative JavaScript and TypeScript evidence for test-strengthening."""
from __future__ import annotations

import re
from pathlib import Path


JS_EXTENSIONS = {".js", ".jsx", ".ts", ".tsx"}


def top_level_symbol_call_count_text(text: str, symbol: str) -> int | None:
    """Count direct or member calls without pretending to parse arbitrary JS."""
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", symbol):
        return None
    if not text or text.count("`") % 2:
        return None
    scrubbed = re.sub(r"//[^\n]*|/\*[\s\S]*?\*/", "", text)
    scrubbed = re.sub(r"(['\"])(?:\\.|(?!\1)[^\\])*\1", "", scrubbed)
    pattern = rf"(?<![A-Za-z0-9_$])(?:{re.escape(symbol)}|\.{re.escape(symbol)})\s*\("
    return len(re.findall(pattern, scrubbed))


def simple_exported_function(text: str, symbol: str) -> bool:
    """Allow only small synchronous exported functions for automatic test drafts."""
    if not re.fullmatch(r"[A-Za-z_$][A-Za-z0-9_$]*", symbol):
        return False
    declaration = re.search(
        rf"(?m)^\s*export\s+function\s+{re.escape(symbol)}\s*\([^\n]*\)", text
    )
    if not declaration:
        return False
    start = declaration.start()
    next_export = re.search(r"(?m)^\s*export\s+(?:async\s+)?function\s+", text[declaration.end():])
    end = declaration.end() + (next_export.start() if next_export else 4000)
    excerpt = text[start:end]
    if re.search(
        r"\b(?:async|await|fetch|prisma|withUserContext|requireUserContext|process|child_process|fs)\b",
        excerpt,
    ):
        return False
    return len(excerpt) <= 4000


def is_javascript_test_path(path: str) -> bool:
    return Path(path).suffix.lower() in JS_EXTENSIONS
