"""Phase B: ingest Claude Code transcript JSONL under ~/.claude/projects/."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from gqlalchemy import Memgraph

from graph_loader.progress import log_info, maybe_tick

def _iter_transcript_lines(path: Path) -> Iterator[tuple[int, str, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line_no, raw in enumerate(f, start=1):
            raw = raw.strip()
            if not raw:
                continue
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(obj, dict):
                continue
            yield line_no, raw, obj


def _text_preview(msg: Dict[str, Any], max_len: int = 500) -> Optional[str]:
    content = msg.get("content")
    if isinstance(content, str):
        s = content.strip()
        return s[:max_len] if s else None
    if isinstance(content, list):
        parts: List[str] = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and isinstance(block.get("text"), str):
                parts.append(block["text"])
        s = " ".join(parts).strip()
        return s[:max_len] if s else None
    return None


def _tool_use_blocks(msg: Dict[str, Any]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    content = msg.get("content")
    if not isinstance(content, list):
        return out
    for block in content:
        if isinstance(block, dict) and block.get("type") == "tool_use":
            out.append(block)
    return out


def ingest_transcript_file(
    db: Memgraph,
    path: Path,
    ingest_run_id: str,
    *,
    progress_every: int = 0,
    progress_label: Optional[str] = None,
) -> int:
    """Load messages, tool calls, models, and session/project nodes from one transcript file."""
    tick_label = progress_label or path.name
    if path.parent.name == "subagents":
        session_from_path = path.parent.parent.name
    else:
        session_from_path = path.stem if path.suffix == ".jsonl" else None
    count = 0
    for line_no, raw, row in _iter_transcript_lines(path):
        if row.get("type") == "file-history-snapshot":
            continue

        uid = row.get("uuid")
        if not uid:
            continue

        sid = row.get("sessionId") or session_from_path
        cwd = row.get("cwd")
        ts = row.get("timestamp")
        typ = row.get("type")
        parent = row.get("parentUuid")
        is_side = bool(row.get("isSidechain", False))
        agent_id = row.get("agentId")
        slug = row.get("slug")
        branch = row.get("gitBranch")
        ver = row.get("version")

        role = None
        msg = row.get("message")
        if isinstance(msg, dict):
            role = msg.get("role")

        preview = None
        model_id = None
        usage = None
        if isinstance(msg, dict):
            preview = _text_preview(msg)
            model_id = msg.get("model")
            usage = msg.get("usage")

        db.execute(
            """
            MERGE (m:Message {uuid: $uuid})
            SET m.type = $typ,
                m.timestamp = $ts,
                m.role = $role,
                m.is_sidechain = $is_side,
                m.text_preview = $preview,
                m.prompt_id = $prompt_id,
                m.session_id = $sid,
                m.ingest_run_id = $ingest_run_id
            """,
            {
                "uuid": uid,
                "typ": typ,
                "ts": ts,
                "role": role,
                "is_side": is_side,
                "preview": preview,
                "prompt_id": row.get("promptId"),
                "sid": sid,
                "ingest_run_id": ingest_run_id,
            },
        )

        if sid:
            db.execute(
                """
                MERGE (s:Session {session_id: $sid})
                SET s.cli_version = coalesce($ver, s.cli_version),
                    s.git_branch = coalesce($branch, s.git_branch),
                    s.slug = coalesce($slug, s.slug),
                    s.source_file = $src,
                    s.last_seen = coalesce($ts, s.last_seen)
                """,
                {
                    "sid": sid,
                    "ver": ver,
                    "branch": branch,
                    "slug": slug,
                    "src": str(path),
                    "ts": ts,
                },
            )
            db.execute(
                """
                MATCH (m:Message {uuid: $uid}), (s:Session {session_id: $sid})
                MERGE (m)-[:IN_SESSION {ingest_run_id: $ingest_run_id}]->(s)
                """,
                {"uid": uid, "sid": sid, "ingest_run_id": ingest_run_id},
            )

        if isinstance(cwd, str) and cwd:
            db.execute(
                """
                MERGE (p:WorkspaceProject {project_root: $root})
                SET p.last_seen = coalesce($ts, p.last_seen)
                """,
                {"root": cwd, "ts": ts},
            )
            db.execute(
                """
                MATCH (s:Session {session_id: $sid}), (p:WorkspaceProject {project_root: $root})
                MERGE (s)-[:IN_PROJECT {ingest_run_id: $ingest_run_id}]->(p)
                """,
                {"sid": sid, "root": cwd, "ingest_run_id": ingest_run_id},
            )

        if parent:
            db.execute(
                """
                MATCH (child:Message {uuid: $cuid}), (parent:Message {uuid: $puid})
                MERGE (child)-[:CHILD_OF {ingest_run_id: $ingest_run_id}]->(parent)
                """,
                {"cuid": uid, "puid": parent, "ingest_run_id": ingest_run_id},
            )

        if is_side and agent_id and sid:
            db.execute(
                """
                MERGE (sr:SubagentRun {session_id: $sid, agent_id: $aid})
                SET sr.is_sidechain = true,
                    sr.transcript_path = $tpath,
                    sr.ingest_run_id = $ingest_run_id
                WITH sr
                MATCH (m:Message {uuid: $uid})
                MERGE (m)-[:PART_OF_SUBAGENT {ingest_run_id: $ingest_run_id}]->(sr)
                """,
                {
                    "sid": sid,
                    "aid": agent_id,
                    "tpath": str(path),
                    "uid": uid,
                    "ingest_run_id": ingest_run_id,
                },
            )

        if typ == "assistant" and isinstance(msg, dict) and model_id:
            db.execute(
                """
                MERGE (mod:Model {model_id: $mid})
                """,
                {"mid": model_id},
            )
            db.execute(
                """
                MATCH (m:Message {uuid: $uid}), (mod:Model {model_id: $mid})
                MERGE (m)-[:USED_MODEL {ingest_run_id: $ingest_run_id}]->(mod)
                """,
                {"uid": uid, "mid": model_id, "ingest_run_id": ingest_run_id},
            )

        if typ == "assistant" and isinstance(msg, dict):
            for block in _tool_use_blocks(msg):
                tname = block.get("name")
                tid = block.get("id")
                if not tname or not tid or not sid:
                    continue
                in_tokens = usage.get("input_tokens") if isinstance(usage, dict) else None
                out_tokens = usage.get("output_tokens") if isinstance(usage, dict) else None
                db.execute(
                    """
                    MERGE (tc:ToolCall {session_id: $sid, tool_use_id: $tid})
                    SET tc.timestamp = $ts,
                        tc.input_tokens = $in_t,
                        tc.output_tokens = $out_t,
                        tc.ingest_run_id = $ingest_run_id
                    WITH tc
                    MERGE (t:Tool {name: $tname})
                    MERGE (tc)-[:INVOKED {ingest_run_id: $ingest_run_id}]->(t)
                    WITH tc
                    MATCH (m:Message {uuid: $uid})
                    MERGE (m)-[:EMITS {ingest_run_id: $ingest_run_id}]->(tc)
                    """,
                    {
                        "sid": sid,
                        "tid": tid,
                        "ts": ts,
                        "in_t": in_tokens,
                        "out_t": out_tokens,
                        "tname": tname,
                        "uid": uid,
                        "ingest_run_id": ingest_run_id,
                    },
                )

                inp = block.get("input") or {}
                if isinstance(inp, dict):
                    fp = inp.get("file_path") or inp.get("path") or inp.get("file")
                    if isinstance(fp, str):
                        db.execute(
                            """
                            MERGE (f:File {path: $path})
                            SET f.extension = $ext
                            WITH f
                            MATCH (tc:ToolCall {session_id: $sid, tool_use_id: $tid})
                            MERGE (tc)-[:TARGETS {mode: $mode, ingest_run_id: $ingest_run_id}]->(f)
                            """,
                            {
                                "path": fp,
                                "ext": Path(fp).suffix.lower() or None,
                                "sid": sid,
                                "tid": tid,
                                "mode": "read" if tname in ("Read", "Grep", "Glob") else "write",
                                "ingest_run_id": ingest_run_id,
                            },
                        )

        count += 1
        maybe_tick(count, tick_label, every=progress_every)
    return count


def run_phase_b(
    db: Memgraph,
    projects_dir: Path,
    ingest_run_id: str,
    *,
    progress_every: int = 0,
) -> Dict[str, int]:
    stats: Dict[str, int] = {}
    if not projects_dir.is_dir():
        return stats
    files = sorted(projects_dir.rglob("*.jsonl"))
    total = len(files)
    if progress_every > 0 and total:
        log_info(f"[phase-b] Transcript ingest: {total} file(s)")

    for i, jsonl in enumerate(files, start=1):
        key = str(jsonl.relative_to(projects_dir))
        if progress_every > 0:
            log_info(f"[phase-b] → {i}/{total} {key}")
        n = ingest_transcript_file(
            db,
            jsonl,
            ingest_run_id,
            progress_every=progress_every,
            progress_label=key,
        )
        if progress_every > 0:
            log_info(f"[phase-b] ✓ {key}: {n} messages")
        stats[key] = n
    return stats
