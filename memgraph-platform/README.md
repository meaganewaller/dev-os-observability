# Memgraph platform

## Quick start

```bash
cd memgraph-platform
docker compose up -d --build
```

- **Memgraph Bolt** (drivers, loaders, `mgconsole`): `localhost:7687` — **not** an HTTP port; opening it in a browser will not show a UI.
- **Memgraph Lab** (web UI / Cypher): `http://localhost:3001` — host port **3001** → container `3000` (avoids clashing with Grafana on 3000). Preconfigured to connect to the `memgraph` service on the compose network.
- **memgraph-schema** runs once after Memgraph is healthy and applies `CALL schema.assert(...)` from `schema/indexes.py`.
- Data persists in Docker volume **`memgraph_data`** (mounts `/var/lib/memgraph`).

If `3001` is taken, change the Lab host mapping in `docker-compose.yml` (e.g. `"3010:3000"`).

### Using Memgraph Lab (beyond a blank canvas)

Lab is still “just” a Cypher shell plus graph/table views — it does not ship dashboards. You get more out of it if you:

1. **Use the right view** — `RETURN count(*)` or other scalars only populate **Table**. To see nodes and edges, **RETURN** actual nodes, relationships, or paths (see `queries/lab_playbook.cypher`).
2. **Save a playbook** — In Lab, open **Collections**, create something like “Dev OS”, and paste queries from [`queries/lab_playbook.cypher`](../queries/lab_playbook.cypher) (exploration + graph-friendly patterns) and [`queries/dashboard_queries.cypher`](../queries/dashboard_queries.cypher) (aggregates / “dashboard” style).
3. **Reuse Run history** — Past queries are in **Run history**; you can re-run or add them to a collection.
4. **Tune heavy queries** — Use **EXPLAIN** / **PROFILE** in the query editor for slow patterns; keep `LIMIT` on graph returns so the viz stays responsive.

If the graph view is empty, you often ran an aggregate-only query, or Phase B did not load (no `projects/**/*.jsonl` yet), so only telemetry nodes exist.

## Load data

From the repo root (with Memgraph running):

```bash
pip install -r graph_loader/requirements.txt
PYTHONPATH=. python -m graph_loader.cli --phase all --memgraph-host 127.0.0.1
```

Progress prints to **stderr** every 500 rows by default (`--progress-every N`; use `--quiet` or `--progress-every 0` to silence). Use it to confirm the loader is still working on long runs.

Large files (e.g. `hook-health.jsonl` with tens of thousands of lines) use one transaction per row today; expect long runtimes or use `--phase a` on a copy of `.claude` trimmed for testing. Batch `UNWIND` ingestion can be added later for speed.

## Read-only API (Grafana)

```bash
pip install -r graph_api/requirements.txt
cd graph_api && MG_HOST=127.0.0.1 uvicorn app:app --port 8090
```

`POST /cypher` with JSON `{"query": "MATCH (n) RETURN n LIMIT 5", "parameters": {}}`.

## Reset local data

```bash
docker compose down -v
```
