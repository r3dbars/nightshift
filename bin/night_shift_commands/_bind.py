"""Bind command handlers to the CLI module so tests can monkeypatch globals."""
from __future__ import annotations

import sys
from functools import wraps


HOST = None


def bind_cli(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        cli = HOST or sys.modules.get("night_shift_cli")
        if cli is not None:
            fn.__globals__.update(
                {
                    key: value
                    for key, value in vars(cli).items()
                    if key != "__builtins__" and not key.startswith("__")
                }
            )
        return fn(*args, **kwargs)

    return wrapper
