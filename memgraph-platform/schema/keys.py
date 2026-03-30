"""
Stable natural keys for Memgraph nodes (LPG).

Used by ETL MERGE and by index/unique definitions in indexes.py.
"""

# --- Property names (single source of truth) ---

KEY_PROJECT_ROOT = "project_root"
KEY_SESSION_ID = "session_id"
KEY_AGENT_ID = "agent_id"
KEY_MESSAGE_UUID = "uuid"
KEY_TOOL_USE_ID = "tool_use_id"
KEY_TOOL_NAME = "name"
KEY_FILE_PATH = "path"
KEY_HOOK_NAME = "name"
KEY_EVENT_ID = "event_id"
KEY_EXECUTION_ID = "execution_id"
KEY_ENTRY_ID = "entry_id"
KEY_RECORD_ID = "record_id"
KEY_MODEL_ID = "model_id"
KEY_DECISION_ID = "decision_id"
KEY_KIND = "kind"

# --- Labels ---

L_WORKSPACE_PROJECT = "WorkspaceProject"
L_SESSION = "Session"
L_SUBAGENT_RUN = "SubagentRun"
L_MESSAGE = "Message"
L_TOOL = "Tool"
L_TOOL_CALL = "ToolCall"
L_FILE = "File"
L_HOOK = "Hook"
L_HOOK_EXECUTION = "HookExecution"
L_DEV_OS_EVENT = "DevOsEvent"
L_DECISION = "Decision"
L_MODEL = "Model"
L_PROMPT_HISTORY_ENTRY = "PromptHistoryEntry"
L_FRICTION_EVENT = "FrictionEvent"
L_IMPACT_RECORD = "ImpactRecord"
