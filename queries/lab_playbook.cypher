// =============================================================================
// Memgraph Lab playbook — Dev OS graph
// =============================================================================
// Lab is best for:
//   • Queries that RETURN nodes, relationships, or paths → Graph view
//   • Aggregates (counts, averages) → Table view (Graph is often empty)
// Copy sections into Lab, or save them as a Collection (Collections in the sidebar).
//
// See also: queries/dashboard_queries.cypher (tile-oriented aggregates)
// Schema reference: memgraph-platform/schema/graph_models.py
// =============================================================================

// --- 0) Is there data? (Table view) ------------------------------------------

MATCH (n) RETURN count(n) AS total_nodes;

MATCH ()-[r]->() RETURN count(r) AS total_relationships;


// --- 1) What labels exist? (Table view) --------------------------------------
// Handy right after a load to see what Phase A / B actually populated.

MATCH (n)
RETURN DISTINCT labels(n) AS label_set, count(*) AS n
ORDER BY n DESC;


// --- 2) Relationship types in use (Table view) -------------------------------

MATCH ()-[r]->()
RETURN DISTINCT type(r) AS rel_type, count(*) AS n
ORDER BY n DESC;


// --- 3) Graph: one “busiest” session → messages + project ---------------------
// Good default graph: Session, WorkspaceProject, and a cap on Messages.
// Tune LIMITs if the graph is too dense.

MATCH (s:Session)<-[:IN_SESSION]-(m:Message)
WITH s, count(m) AS msg_count
ORDER BY msg_count DESC
LIMIT 1
OPTIONAL MATCH (s)-[:IN_PROJECT]->(p:WorkspaceProject)
WITH s, p
OPTIONAL MATCH (s)<-[:IN_SESSION]-(m:Message)
WITH s, p, m
ORDER BY m.timestamp ASC
LIMIT 80
RETURN s, p, m;


// --- 4) Graph: message → tool calls → tools + files --------------------------
// Shows assistant tool usage and file targets (Phase B).

MATCH (m:Message {type: "assistant"})-[:EMITS]->(tc:ToolCall)-[:INVOKED]->(t:Tool)
OPTIONAL MATCH (tc)-[:TARGETS]->(f:File)
WITH m, tc, t, f
LIMIT 120
RETURN m, tc, t, f;


// --- 5) Graph: hook executions → hook nodes (Phase A) -------------------------

MATCH (x:HookExecution)-[:OF_HOOK]->(h:Hook)
RETURN x, h
LIMIT 100;


// --- 6) Graph: friction → tool (if friction data exists) ---------------------

MATCH (f:FrictionEvent)-[:INVOKED_TOOL]->(t:Tool)
RETURN f, t
LIMIT 80;


// --- 7) Graph: decisions tied to sessions (Phase A) ---------------------------

MATCH (d:Decision)-[:RECORDED_IN_SESSION]->(s:Session)
RETURN d, s
LIMIT 50;


// --- 8) Graph: Dev OS events linked to sessions -------------------------------

MATCH (e:DevOsEvent)-[:FOR_SESSION]->(s:Session)
RETURN e, s
LIMIT 80;


// --- 9) Narrow subgraph: pick session by id (replace SESSION_ID_HERE) ----------
// Paste a real session_id from a Table query first, e.g. from dashboard_queries #8.

MATCH (s:Session {session_id: "SESSION_ID_HERE"})<-[:IN_SESSION]-(m:Message)
OPTIONAL MATCH (m)-[:CHILD_OF]->(parent:Message)
OPTIONAL MATCH (m)-[:EMITS]->(tc:ToolCall)-[:INVOKED]->(t:Tool)
RETURN s, m, parent, tc, t
LIMIT 150;


// --- 10) Path: child messages up the tree (visual chain, keep LIMIT low) -----

MATCH p=(child:Message)-[:CHILD_OF*1..4]->(ancestor:Message)
RETURN p
LIMIT 40;
