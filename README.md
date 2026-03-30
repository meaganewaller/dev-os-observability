# DevOS Observability

Observability stack for the DevOS system (Claude Code configuration and automation). Provides dashboards, alerts, and metrics for monitoring Claude Code sessions, friction events, and quality signals.

## Quick Start

```bash
# Start the stack
docker compose up -d

# View Grafana
open http://localhost:3000
# Login: admin / admin
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Data Sources                            │
├─────────────────────────────────────────────────────────────────┤
│  ~/.claude/dev-os-events.jsonl    ~/.claude/skill-friction-log  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OpenTelemetry Collector                      │
│                      (devos-collector)                          │
│  - Tails log files                                              │
│  - Parses JSON                                                  │
│  - Adds log_source labels                                       │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Grafana LGTM Stack                         │
│                        (devos-lgtm)                             │
├─────────────────────────────────────────────────────────────────┤
│  Loki        │  Log aggregation and querying                    │
│  Grafana     │  Dashboards and alerting                         │
│  Tempo       │  Distributed tracing (future)                    │
│  Mimir       │  Metrics storage (future)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Alert Webhook                              │
│                     (devos-webhook)                             │
│  - Receives Grafana alerts                                      │
│  - Logs to data/alerts/alerts.jsonl                             │
└─────────────────────────────────────────────────────────────────┘
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| devos-lgtm | 3000 | Grafana UI |
| devos-lgtm | 4317 | OTLP gRPC endpoint |
| devos-lgtm | 4318 | OTLP HTTP endpoint |
| devos-collector | - | Log file collector |
| devos-webhook | 8085 | Alert receiver |

## Memgraph (optional graph analytics)

Relationship analytics over the same `~/.claude` JSONL files:

```bash
cd memgraph-platform && docker compose up -d --build
pip install -r graph_loader/requirements.txt
PYTHONPATH=. python -m graph_loader.cli --phase all
```

See [memgraph-platform/README.md](memgraph-platform/README.md), [docs/graph-etl-inventory.md](docs/graph-etl-inventory.md), [queries/dashboard_queries.cypher](queries/dashboard_queries.cypher) (aggregates), and [queries/lab_playbook.cypher](queries/lab_playbook.cypher) (Lab-friendly graph exploration).

## Dashboards

All dashboards are in the **DevOS** folder in Grafana.

| Dashboard | Purpose |
|-----------|---------|
| [Mission Control](docs/dashboards.md#mission-control) | High-level system health with tool failure breakdown |
| [Friction Overview](docs/dashboards.md#friction-overview) | Friction events and ADR-0008 tracking |
| [Session Activity](docs/dashboards.md#session-activity) | Session and tool usage patterns |
| [Cue Effectiveness](docs/dashboards.md#cue-effectiveness) | Cue system performance |
| [Hook Performance](docs/dashboards.md#hook-performance) | Tool success rates and errors |
| [Quality Signals](docs/dashboards.md#quality-signals) | Reversals, large changes, decisions |
| [Weekly Trends](docs/dashboards.md#weekly-trends) | Week-over-week comparisons |
| [Collaboration Insights](docs/dashboards.md#collaboration-insights) | Human/AI collaboration patterns |
| [Time & Effort](docs/dashboards.md#time--effort) | Session duration and productivity |
| [Project Focus](docs/dashboards.md#project-focus) | Work categories and risk profiles |

## Alerts

| Alert | Condition | Severity |
|-------|-----------|----------|
| Friction Spike | >20 friction events/hour | Warning |
| ADR-0008 Breach | >50 resource-limit errors/week | Critical |

See [docs/alerting.md](docs/alerting.md) for configuration details.

## Configuration

- `docker-compose.yaml` - Service definitions
- `otel-collector-config.yaml` - Log collection config
- `grafana/dashboards/` - Dashboard JSON files
- `grafana/provisioning/` - Grafana auto-provisioning

See [docs/configuration.md](docs/configuration.md) for details.

## Common Tasks

### View live alerts
```bash
docker logs -f devos-webhook
```

### Check alert history
```bash
tail -20 data/alerts/alerts.jsonl | jq '.'
```

### Query logs manually
```bash
# Recent friction events
curl -s -u admin:admin -G 'http://localhost:3000/api/datasources/proxy/uid/loki/loki/api/v1/query' \
  --data-urlencode 'query={service_name="devos"} | log_source="friction"' \
  --data-urlencode 'limit=10' | jq '.data.result'
```

### Restart services
```bash
docker compose restart        # All services
docker compose restart lgtm   # Just Grafana
```

### Backfill historical data
```bash
# Edit otel-collector-config.yaml, change start_at: end -> start_at: beginning
docker compose restart devos-collector
# Wait for ingestion, then change back to start_at: end
```

## Data Sources

### dev-os-events.jsonl

Main event log from DevOS hooks. Event types include:

| Event Type | Description |
|------------|-------------|
| `session_start` | Claude Code session began |
| `session_end` | Session ended |
| `tool_write` | File written/edited |
| `tool_failure` | Tool operation failed |
| `test_run` | Tests executed |
| `cue_fired` | Cue was triggered |
| `cue_matched` | Cue matched a prompt |
| `reversal` | Work was undone |
| `large_change` | Large file modification |
| `tradeoff_auto_capture` | Decision tradeoff recorded |

### skill-friction-log.jsonl

Friction/error events with subdomains:

| Subdomain | Description |
|-----------|-------------|
| `resource-limit` | File too large, token limit exceeded |
| `file-not-found` | Path doesn't exist |
| `command-failed` | Shell command failed |
| `parse` | JSON/YAML parse error |

## Troubleshooting

See [docs/troubleshooting.md](docs/troubleshooting.md) for common issues.

## License

MIT
