"""Phase A: ingest dev-os-events, impact, friction, hook-health, history JSONL."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, Optional

from gqlalchemy import Memgraph

from graph_loader.ids import line_hash_id
from graph_loader.progress import log_info, maybe_tick


def _iter_jsonl(path: Path) -> Iterator[tuple[int, str, Dict[str, Any]]]:
    if not path.exists():
        return
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


def _ensure_session(db: Memgraph, session_id: str, ts: Optional[str]) -> None:
    db.execute(
        """
        MERGE (s:Session {session_id: $sid})
        SET s.last_seen = coalesce($ts, s.last_seen)
        """,
        {"sid": session_id, "ts": ts},
    )


def _ensure_project(db: Memgraph, project_root: str, ts: Optional[str]) -> None:
    db.execute(
        """
        MERGE (p:WorkspaceProject {project_root: $root})
        SET p.last_seen = coalesce($ts, p.last_seen)
        """,
        {"root": project_root, "ts": ts},
    )


def load_dev_os_events(
    db: Memgraph,
    path: Path,
    ingest_run_id: str,
    *,
    progress_every: int = 0,
) -> int:
    count = 0
    for line_no, raw, row in _iter_jsonl(path):
        event_id = line_hash_id("devos", str(path), line_no, raw)
        ts = row.get("timestamp")
        kind = row.get("event_type", "")
        sid = row.get("session_id")
        payload = row.get("payload")
        payload_json = json.dumps(payload) if payload is not None else None

        db.execute(
            """
            MERGE (e:DevOsEvent {event_id: $eid})
            SET e.kind = $kind,
                e.timestamp = $ts,
                e.session_id = $sid,
                e.payload_json = $payload_json,
                e.ingest_run_id = $ingest_run_id
            """,
            {
                "eid": event_id,
                "kind": kind,
                "ts": ts,
                "sid": sid,
                "payload_json": payload_json,
                "ingest_run_id": ingest_run_id,
            },
        )
        if sid:
            _ensure_session(db, sid, ts)
            db.execute(
                """
                MATCH (e:DevOsEvent {event_id: $eid}), (s:Session {session_id: $sid})
                MERGE (e)-[:FOR_SESSION {ingest_run_id: $ingest_run_id}]->(s)
                """,
                {"eid": event_id, "sid": sid, "ingest_run_id": ingest_run_id},
            )
        if kind in ("decision_tradeoff", "tradeoff_auto_capture") and isinstance(payload, dict):
            summary = (payload.get("decision_summary") or payload.get("summary") or "")[:4000]
            if summary:
                did = line_hash_id("dec", str(path), line_no, raw)
                db.execute(
                    """
                    MERGE (d:Decision {decision_id: $did})
                    SET d.summary = $summary,
                        d.captured_at = $ts,
                        d.source = $source,
                        d.ingest_run_id = $ingest_run_id
                    """,
                    {
                        "did": did,
                        "summary": summary,
                        "ts": ts,
                        "source": "dev-os-events",
                        "ingest_run_id": ingest_run_id,
                    },
                )
                if sid:
                    _ensure_session(db, sid, ts)
                    db.execute(
                        """
                        MATCH (d:Decision {decision_id: $did}), (s:Session {session_id: $sid})
                        MERGE (d)-[:RECORDED_IN_SESSION {ingest_run_id: $ingest_run_id}]->(s)
                        """,
                        {"did": did, "sid": sid, "ingest_run_id": ingest_run_id},
                    )

        count += 1
        maybe_tick(count, path.name, every=progress_every)
    return count


def load_impact_log(
    db: Memgraph,
    path: Path,
    ingest_run_id: str,
    *,
    progress_every: int = 0,
) -> int:
    count = 0
    for line_no, raw, row in _iter_jsonl(path):
        rid = line_hash_id("impact", str(path), line_no, raw)
        ts = row.get("timestamp")
        paths = row.get("file_paths") or []
        change_type = row.get("change_type")
        risk = row.get("risk_level")
        guess = row.get("impact_guess")
        domains = row.get("skill_domains") or []

        db.execute(
            """
            MERGE (r:ImpactRecord {record_id: $rid})
            SET r.timestamp = $ts,
                r.change_type = $change_type,
                r.risk_level = $risk,
                r.impact_guess = $guess,
                r.skill_domains = $domains,
                r.ingest_run_id = $ingest_run_id
            """,
            {
                "rid": rid,
                "ts": ts,
                "change_type": change_type,
                "risk": risk,
                "guess": guess,
                "domains": domains,
                "ingest_run_id": ingest_run_id,
            },
        )
        for fp in paths:
            if not isinstance(fp, str):
                continue
            db.execute(
                """
                MERGE (f:File {path: $path})
                SET f.extension = $ext
                WITH f
                MATCH (r:ImpactRecord {record_id: $rid})
                MERGE (r)-[:AFFECTS_FILE {ingest_run_id: $ingest_run_id}]->(f)
                """,
                {
                    "path": fp,
                    "ext": Path(fp).suffix.lower() or None,
                    "rid": rid,
                    "ingest_run_id": ingest_run_id,
                },
            )
        count += 1
        maybe_tick(count, path.name, every=progress_every)
    return count


def load_friction_log(
    db: Memgraph,
    path: Path,
    ingest_run_id: str,
    *,
    progress_every: int = 0,
) -> int:
    count = 0
    for line_no, raw, row in _iter_jsonl(path):
        eid = line_hash_id("fric", str(path), line_no, raw)
        ts = row.get("timestamp")
        tool_name = row.get("tool_name")
        domain = row.get("domain")
        err = (row.get("error_excerpt") or "")[:4000]

        db.execute(
            """
            MERGE (f:FrictionEvent {event_id: $eid})
            SET f.timestamp = $ts,
                f.tool_name = $tool_name,
                f.domain = $domain,
                f.error_excerpt = $err,
                f.ingest_run_id = $ingest_run_id
            """,
            {
                "eid": eid,
                "ts": ts,
                "tool_name": tool_name,
                "domain": domain,
                "err": err,
                "ingest_run_id": ingest_run_id,
            },
        )
        if tool_name:
            db.execute(
                """
                MERGE (t:Tool {name: $name})
                WITH t
                MATCH (f:FrictionEvent {event_id: $eid})
                MERGE (f)-[:INVOKED_TOOL {ingest_run_id: $ingest_run_id}]->(t)
                """,
                {"name": tool_name, "eid": eid, "ingest_run_id": ingest_run_id},
            )
        count += 1
        maybe_tick(count, path.name, every=progress_every)
    return count


def load_hook_health(
    db: Memgraph,
    path: Path,
    ingest_run_id: str,
    *,
    progress_every: int = 0,
) -> int:
    count = 0
    for line_no, raw, row in _iter_jsonl(path):
        xid = line_hash_id("hook", str(path), line_no, raw)
        ts = row.get("timestamp")
        hook = row.get("hook")
        status = row.get("status")
        duration_ms = row.get("duration_ms")
        err = row.get("error")

        if not hook:
            continue

        db.execute(
            """
            MERGE (h:Hook {name: $name})
            """,
            {"name": hook},
        )
        db.execute(
            """
            MERGE (x:HookExecution {execution_id: $xid})
            SET x.timestamp = $ts,
                x.status = $status,
                x.duration_ms = $duration_ms,
                x.error = $err,
                x.source = $source,
                x.ingest_run_id = $ingest_run_id
            WITH x
            MATCH (h:Hook {name: $name})
            MERGE (x)-[:OF_HOOK {ingest_run_id: $ingest_run_id}]->(h)
            """,
            {
                "xid": xid,
                "ts": ts,
                "status": status,
                "duration_ms": duration_ms,
                "err": err,
                "name": hook,
                "source": "hook-health",
                "ingest_run_id": ingest_run_id,
            },
        )
        count += 1
        maybe_tick(count, path.name, every=progress_every)
    return count


def load_history(
    db: Memgraph,
    path: Path,
    ingest_run_id: str,
    *,
    progress_every: int = 0,
) -> int:
    count = 0
    for line_no, raw, row in _iter_jsonl(path):
        eid = line_hash_id("hist", str(path), line_no, raw)
        ts_ms = row.get("timestamp")
        ts = None
        if isinstance(ts_ms, (int, float)):
            from datetime import datetime, timezone

            ts = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc).isoformat()
        sid = row.get("sessionId")
        proj = row.get("project")
        display = (row.get("display") or "")[:8000]

        db.execute(
            """
            MERGE (e:PromptHistoryEntry {entry_id: $eid})
            SET e.timestamp = $ts,
                e.display = $display,
                e.ingest_run_id = $ingest_run_id
            """,
            {"eid": eid, "ts": ts, "display": display, "ingest_run_id": ingest_run_id},
        )
        if sid:
            _ensure_session(db, sid, ts)
            db.execute(
                """
                MATCH (e:PromptHistoryEntry {entry_id: $eid}), (s:Session {session_id: $sid})
                MERGE (e)-[:FOR_SESSION {ingest_run_id: $ingest_run_id}]->(s)
                """,
                {"eid": eid, "sid": sid, "ingest_run_id": ingest_run_id},
            )
        if project_root := proj if isinstance(proj, str) else None:
            _ensure_project(db, project_root, ts)
            db.execute(
                """
                MATCH (e:PromptHistoryEntry {entry_id: $eid}), (p:WorkspaceProject {project_root: $root})
                MERGE (e)-[:FOR_PROJECT {ingest_run_id: $ingest_run_id}]->(p)
                """,
                {"eid": eid, "root": project_root, "ingest_run_id": ingest_run_id},
            )

        count += 1
        maybe_tick(count, path.name, every=progress_every)
    return count


def run_phase_a(
    db: Memgraph,
    claude_home: Path,
    ingest_run_id: str,
    *,
    progress_every: int = 0,
) -> Dict[str, int]:
    stats: Dict[str, int] = {}
    if progress_every > 0:
        log_info("[phase-a] Telemetry JSONL ingest")

    def _run(name: str, loader, path: Path) -> int:
        if progress_every > 0:
            log_info(f"[phase-a] → {path.name} ({name})")
        n = loader(db, path, ingest_run_id, progress_every=progress_every)
        if progress_every > 0:
            log_info(f"[phase-a] ✓ {path.name}: {n} rows")
        return n

    stats["dev_os_events"] = _run(
        "dev-os-events",
        load_dev_os_events,
        claude_home / "dev-os-events.jsonl",
    )
    alt = claude_home / "dev-os-events-new.jsonl"
    if alt.exists():
        stats["dev_os_events_new"] = _run("dev-os-events-new", load_dev_os_events, alt)
    stats["impact_log"] = _run("impact-log", load_impact_log, claude_home / "impact-log.jsonl")
    stats["friction_log"] = _run(
        "skill-friction-log",
        load_friction_log,
        claude_home / "skill-friction-log.jsonl",
    )
    stats["hook_health"] = _run("hook-health", load_hook_health, claude_home / "hook-health.jsonl")
    stats["history"] = _run("history", load_history, claude_home / "history.jsonl")
    return stats
