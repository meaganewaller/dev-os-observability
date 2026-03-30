"""Deterministic surrogate keys for MERGE (same line → same id)."""

from __future__ import annotations

import hashlib


def line_hash_id(prefix: str, source_path: str, line_no: int, raw_line: str) -> str:
    payload = f"{source_path}\n{line_no}\n{raw_line}"
    h = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"{prefix}_{h[:40]}"


def json_hash_id(prefix: str, *parts: str) -> str:
    h = hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()
    return f"{prefix}_{h[:40]}"
