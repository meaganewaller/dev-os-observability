"""Progress logging to stderr so stdout stays clean for JSON/piping."""

from __future__ import annotations

import sys


def log_info(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def maybe_tick(count: int, label: str, *, every: int) -> None:
    """Emit a line every `every` rows (starting at `every`, 2*every, …)."""
    if every <= 0:
        return
    if count > 0 and count % every == 0:
        log_info(f"  … {label}: {count} rows processed")
