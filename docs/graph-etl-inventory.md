# Graph ETL: source files and field mappings

This document locks **source-of-truth paths** (configurable via env) and **field mappings** for loading `.claude` JSONL telemetry into Memgraph.

## Default paths (host)


| Logical source       | Default path                                                    | Notes                                                    |
| -------------------- | --------------------------------------------------------------- | -------------------------------------------------------- |
| Dev OS events        | `~/.claude/dev-os-events.jsonl`                                 | Primary; merge with `dev-os-events-new.jsonl` if present |
| Dev OS events (alt)  | `~/.claude/dev-os-events-new.jsonl`                             | Same `event_type` + `payload` shape                      |
| Impact log           | `~/.claude/impact-log.jsonl`                                    | Denormalized file impact                                 |
| Skill friction       | `~/.claude/skill-friction-log.jsonl`                            | Tool failures                                            |
| Hook health          | `~/.claude/hook-health.jsonl`                                   | Hook execution metrics                                   |
| Prompt history       | `~/.claude/history.jsonl`                                       | Slash commands / prompts (epoch ms)                      |
| Transcripts          | `~/.claude/projects/<encoded-dir>/<sessionId>.jsonl`            | Claude Code session transcripts                          |
| Subagent transcripts | `~/.claude/projects/.../<sessionId>/subagents/agent-<id>.jsonl` | `isSidechain`, `agentId`                                 |


## Row shapes

### dev-os-events.jsonl

- `timestamp` (string ISO-8601)
- `session_id` (string UUID, optional)
- `event_type` (string) → graph `DevOsEvent.kind`
- `payload` (object, varies)

### impact-log.jsonl

- `timestamp`, `file_paths` (array), `change_type`, `skill_domains`, `impact_guess`, `risk_level`

### skill-friction-log.jsonl

- `timestamp`, `tool_name`, `file_paths`, `domain`, `error_excerpt`, `hints`, `signals`

### hook-health.jsonl

- `timestamp`, `hook`, `status`, `duration_ms`, `error` (nullable)

### history.jsonl

- `timestamp` (number, epoch ms)
- `sessionId`, `project`, `display`, `pastedContents`

### Transcript JSONL (project files)

- Top-level: `uuid`, `type`, `timestamp`, `sessionId`, `cwd`, `parentUuid`, `isSidechain`, `agentId` (subagents), `message`, `toolUseID`, etc.
- Assistant `message.usage`: token fields for aggregates
- `content[]` may include `tool_use` with `name`, `input`, `id`

## Graph node keys (ETL)


| Node label         | Natural key property | Source                                                |
| ------------------ | -------------------- | ----------------------------------------------------- |
| WorkspaceProject   | `project_root`       | `cwd`, `history.project`, or decoded projects path    |
| Session            | `session_id`         | UUID string                                           |
| DevOsEvent         | `event_id`           | `sha256(source_file + line_no)` or `sha256(jsonline)` |
| Hook               | `name`               | `hook` field                                          |
| HookExecution      | `execution_id`       | `sha256(source_file + line_no)`                       |
| Tool               | `name`               | Canonical tool name                                   |
| File               | `path`               | Absolute path from payloads                           |
| PromptHistoryEntry | `entry_id`           | `sha256(source_file + line_no)`                       |
| FrictionEvent      | `event_id`           | hash of line                                          |
| ImpactRecord       | `record_id`          | hash of line                                          |
| Message            | `uuid`               | Transcript line                                       |
| ToolCall           | `tool_use_id`        | From `tool_use` / `tool_result`                       |
| Model              | `model_id`           | Assistant `message.model`                             |


