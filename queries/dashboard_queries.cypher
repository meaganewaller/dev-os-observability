// Dev OS graph — example Cypher for dashboards (run in Memgraph Lab or mgconsole)
// For graph visualization + exploration queries, see lab_playbook.cypher

// 1) Sessions per WorkspaceProject (top 15)
MATCH (s:Session)-[:IN_PROJECT]->(p:WorkspaceProject)
RETURN p.project_root AS project, count(s) AS sessions
ORDER BY sessions DESC
LIMIT 15;

// 2) Tool failure rate proxy: FrictionEvent count by tool
MATCH (f:FrictionEvent)-[:INVOKED_TOOL]->(t:Tool)
RETURN t.name AS tool, count(f) AS friction_events
ORDER BY friction_events DESC
LIMIT 20;

// 3) Dev OS event volume by kind (last N events — filter by time in app)
MATCH (e:DevOsEvent)
RETURN e.kind AS event_type, count(*) AS n
ORDER BY n DESC
LIMIT 30;

// 4) Decisions recorded per session (top sessions)
MATCH (d:Decision)-[:RECORDED_IN_SESSION]->(s:Session)
RETURN s.session_id AS session_id, count(d) AS decisions
ORDER BY decisions DESC
LIMIT 20;

// 5) Hook latency sample: average duration_ms by hook name
MATCH (x:HookExecution)-[:OF_HOOK]->(h:Hook)
WHERE x.duration_ms IS NOT NULL
RETURN h.name AS hook, avg(x.duration_ms) AS avg_ms, count(x) AS runs
ORDER BY runs DESC
LIMIT 25;

// 6) Model mix (transcript Phase B)
MATCH (m:Message)-[:USED_MODEL]->(mod:Model)
RETURN mod.model_id AS model, count(*) AS uses
ORDER BY uses DESC;

// 7) Most touched files (from impact + tool targets)
MATCH (f:File)
OPTIONAL MATCH (:ImpactRecord)-[r:AFFECTS_FILE]->(f)
OPTIONAL MATCH (:ToolCall)-[t:TARGETS]->(f)
WITH f, count(DISTINCT r) AS impact_hits, count(DISTINCT t) AS tool_hits
RETURN f.path AS path, impact_hits + tool_hits AS total
ORDER BY total DESC
LIMIT 30;

// 8) Messages per session (Phase B)
MATCH (m:Message)-[:IN_SESSION]->(s:Session)
RETURN s.session_id AS session_id, count(m) AS messages
ORDER BY messages DESC
LIMIT 20;

// 9) Subagent runs per session
MATCH (m:Message)-[:PART_OF_SUBAGENT]->(sr:SubagentRun)
RETURN sr.session_id AS session_id, sr.agent_id AS agent_id, count(m) AS msgs
ORDER BY msgs DESC
LIMIT 25;

// 10) Tool call counts by tool name (Phase B)
MATCH (tc:ToolCall)-[:INVOKED]->(t:Tool)
RETURN t.name AS tool, count(tc) AS calls
ORDER BY calls DESC
LIMIT 25;
