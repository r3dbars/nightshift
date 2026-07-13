from __future__ import annotations


REASONING_MODEL_MARKERS = (
    "deepseek-r1",
    "distilled",
    "qwen3",
    "qwq",
    "reasoning",
)


def output_token_budget(model: str, standard: int) -> int:
    normalized = model.lower()
    if any(marker in normalized for marker in REASONING_MODEL_MARKERS):
        return max(8192, standard)
    return standard
