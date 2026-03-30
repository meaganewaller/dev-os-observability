# Privacy and redaction (graph ETL)

## Principles

- **Transcript `thinking` blocks** and **encrypted reasoning** are **not** copied into Memgraph by the default loader. Only structured metadata (`usage`, `model`, `tool_use` ids, paths) and short **text previews** are stored on `:Message` nodes.
- **Full tool output** (large `tool_result` bodies) is **not** ingested; link files and paths only when present in `tool_use.input`.
- **Prompt history** (`history.jsonl`) stores user `display` text — treat `~/.claude` as **sensitive**. Restrict filesystem mounts in Docker to read-only and avoid shipping raw graph exports off-machine without review.

## Optional external blob store

For a future phase, store full message bodies in **object storage** or a **SQLite sidecar** keyed by `Message.uuid`, and keep the graph as an index of relationships and metrics only.

## Loader flags (future)

Consider adding `--redact-paths` or `--max-preview-chars` to `graph_loader/cli.py` for stricter local policy.
