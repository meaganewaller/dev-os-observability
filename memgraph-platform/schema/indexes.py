"""
Index and unique-constraint maps for CALL schema.assert.

See: https://memgraph.com/docs/querying/schema
"""

from __future__ import annotations

# Label -> list of indexed fields. "" denotes label-only index.
INDICES_MAP: dict[str, list[str]] = {
    "WorkspaceProject": ["", "project_root"],
    "Session": ["", "session_id", "started_at"],
    "SubagentRun": ["", "session_id", "agent_id"],
    "Message": ["", "uuid", "timestamp", "session_id"],
    "Tool": ["", "name"],
    "ToolCall": ["", "tool_use_id", "session_id", "timestamp"],
    "File": ["", "path"],
    "Hook": ["", "name"],
    "HookExecution": ["", "execution_id", "timestamp"],
    "DevOsEvent": ["", "event_id", "kind", "timestamp", "session_id"],
    "Decision": ["", "decision_id", "captured_at"],
    "Model": ["", "model_id"],
    "PromptHistoryEntry": ["", "entry_id", "timestamp"],
    "FrictionEvent": ["", "event_id", "timestamp", "tool_name"],
    "ImpactRecord": ["", "record_id", "timestamp"],
}

# Label -> list of property groups; each inner list is one unique constraint.
UNIQUE_CONSTRAINTS_MAP: dict[str, list[list[str]]] = {
    "WorkspaceProject": [["project_root"]],
    "Session": [["session_id"]],
    "SubagentRun": [["session_id", "agent_id"]],
    "Message": [["uuid"]],
    "Tool": [["name"]],
    "ToolCall": [["session_id", "tool_use_id"]],
    "File": [["path"]],
    "Hook": [["name"]],
    "HookExecution": [["execution_id"]],
    "DevOsEvent": [["event_id"]],
    "Decision": [["decision_id"]],
    "Model": [["model_id"]],
    "PromptHistoryEntry": [["entry_id"]],
    "FrictionEvent": [["event_id"]],
    "ImpactRecord": [["record_id"]],
}


def indices_to_cypher_literal() -> str:
    parts: list[str] = []
    for label, props in INDICES_MAP.items():
        plist = ", ".join('""' if p == "" else f'"{p}"' for p in props)
        parts.append(f"`{label}`: [{plist}]")
    return "{" + ", ".join(parts) + "}"


def uniques_to_cypher_literal() -> str:
    parts: list[str] = []
    for label, groups in UNIQUE_CONSTRAINTS_MAP.items():
        group_strs = []
        for group in groups:
            inner = ", ".join(f'"{p}"' for p in group)
            group_strs.append(f"[{inner}]")
        parts.append(f"`{label}`: [{', '.join(group_strs)}]")
    return "{" + ", ".join(parts) + "}"
