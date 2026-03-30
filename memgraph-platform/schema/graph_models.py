"""
Documentation-oriented typings for graph nodes (ETL aligns with these fields).

Indexes and uniques are enforced in Memgraph via init_schema.py + indexes.py, not via GQLAlchemy
class-level constraints (avoids requiring a live DB at import time).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class WorkspaceProject:
    project_root: str
    display_name: Optional[str] = None
    first_seen: Optional[str] = None
    last_seen: Optional[str] = None


@dataclass
class Session:
    session_id: str
    started_at: Optional[str] = None
    ended_at: Optional[str] = None
    cli_version: Optional[str] = None
    git_branch: Optional[str] = None
    entrypoint: Optional[str] = None
    slug: Optional[str] = None
    source_file: Optional[str] = None


@dataclass
class SubagentRun:
    session_id: str
    agent_id: str
    is_sidechain: bool = True
    transcript_path: Optional[str] = None


@dataclass
class Message:
    uuid: str
    type: str
    timestamp: Optional[str] = None
    role: Optional[str] = None
    is_sidechain: bool = False
    text_preview: Optional[str] = None
    prompt_id: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class Tool:
    name: str


@dataclass
class ToolCall:
    tool_use_id: str
    session_id: str
    timestamp: Optional[str] = None
    duration_ms: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None


@dataclass
class File:
    path: str
    extension: Optional[str] = None


@dataclass
class Hook:
    name: str


@dataclass
class HookExecution:
    execution_id: str
    timestamp: Optional[str] = None
    status: Optional[str] = None
    duration_ms: Optional[int] = None
    hook_event: Optional[str] = None
    error: Optional[str] = None
    source: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class DevOsEvent:
    event_id: str
    kind: str
    timestamp: Optional[str] = None
    session_id: Optional[str] = None
    payload_json: Optional[str] = None
    project_root: Optional[str] = None


@dataclass
class Decision:
    decision_id: str
    summary: Optional[str] = None
    captured_at: Optional[str] = None
    source: Optional[str] = None


@dataclass
class Model:
    model_id: str


@dataclass
class PromptHistoryEntry:
    entry_id: str
    timestamp: Optional[str] = None
    display: Optional[str] = None


@dataclass
class FrictionEvent:
    event_id: str
    timestamp: Optional[str] = None
    tool_name: Optional[str] = None
    domain: Optional[str] = None
    error_excerpt: Optional[str] = None
    session_id: Optional[str] = None


@dataclass
class ImpactRecord:
    record_id: str
    timestamp: Optional[str] = None
    change_type: Optional[str] = None
    risk_level: Optional[str] = None
    impact_guess: Optional[str] = None
    skill_domains: list[str] = field(default_factory=list)
