#!/usr/bin/env python3
"""Load ~/.claude JSONL into Memgraph (Phase A and/or B)."""

from __future__ import annotations

import argparse
import os
import uuid
from pathlib import Path

from gqlalchemy import Memgraph

from graph_loader.phase_a import run_phase_a
from graph_loader.progress import log_info
from graph_loader.transcripts import run_phase_b


def main() -> int:
    p = argparse.ArgumentParser(description="Dev OS graph loader")
    p.add_argument(
        "--claude-home",
        default=os.environ.get("CLAUDE_HOME", str(Path.home() / ".claude")),
        help="Path to .claude directory",
    )
    p.add_argument(
        "--memgraph-host",
        default=os.environ.get("MG_HOST", "127.0.0.1"),
    )
    p.add_argument(
        "--memgraph-port",
        type=int,
        default=int(os.environ.get("MG_PORT", "7687")),
    )
    p.add_argument(
        "--phase",
        choices=("a", "b", "all"),
        default="all",
        help="a=telemetry JSONL only, b=transcript projects only, all=both",
    )
    p.add_argument(
        "--ingest-run-id",
        default=None,
        help="Idempotency tag for this run (default: random UUID)",
    )
    p.add_argument(
        "--progress-every",
        type=int,
        default=500,
        metavar="N",
        help="Print progress every N rows to stderr (0 disables). Default: 500.",
    )
    p.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress progress output (same as --progress-every 0).",
    )
    args = p.parse_args()

    claude_home = Path(args.claude_home).expanduser().resolve()
    projects = claude_home / "projects"
    ingest_run_id = args.ingest_run_id or str(uuid.uuid4())
    progress_every = 0 if args.quiet else args.progress_every

    db = Memgraph(host=args.memgraph_host, port=args.memgraph_port)
    stats: dict = {}

    if progress_every > 0:
        log_info(
            f"[loader] Memgraph {args.memgraph_host}:{args.memgraph_port} "
            f"phase={args.phase} ingest_run_id={ingest_run_id}"
        )

    if args.phase in ("a", "all"):
        stats["phase_a"] = run_phase_a(
            db,
            claude_home,
            ingest_run_id,
            progress_every=progress_every,
        )
    if args.phase in ("b", "all"):
        stats["phase_b"] = run_phase_b(
            db,
            projects,
            ingest_run_id,
            progress_every=progress_every,
        )

    print(stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
