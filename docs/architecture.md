# Architecture

## Overview

DevOS Observability is built on the Grafana LGTM stack (Loki, Grafana, Tempo, Mimir) with an OpenTelemetry Collector for log ingestion.

## Components

### OpenTelemetry Collector (devos-collector)

The collector tails DevOS log files and forwards them to Loki.

**Configuration:** `otel-collector-config.yaml`

```yaml
receivers:
  filelog/devos:
    include: [/claude-data/dev-os-events.jsonl]
    start_at: end
    operators:
      - type: json_parser
      - type: add
        field: attributes.log_source
        value: dev-os-events

  filelog/friction:
    include: [/claude-data/skill-friction-log.jsonl]
    start_at: end
    operators:
      - type: json_parser
      - type: add
        field: attributes.log_source
        value: friction
```

**Key behaviors:**
- `start_at: end` - Only reads new log entries (use `beginning` for backfill)
- JSON parsing extracts fields as structured metadata
- `log_source` attribute distinguishes event types from friction logs

### Grafana LGTM (devos-lgtm)

All-in-one observability stack using `grafana/otel-lgtm` image.

**Included services:**
- **Loki** - Log aggregation (queryable via LogQL)
- **Grafana** - Visualization and alerting
- **Tempo** - Distributed tracing (not currently used)
- **Mimir** - Metrics storage (not currently used)
- **Pyroscope** - Continuous profiling (not currently used)

**Provisioning:**
- Dashboards auto-loaded from `/devos-dashboards`
- Alert rules from `/otel-lgtm/grafana/conf/provisioning/alerting/`

### Alert Webhook (devos-webhook)

Simple Python HTTP server that receives Grafana alerts.

**Features:**
- Logs alerts to stdout (viewable via `docker logs`)
- Persists alerts to `data/alerts/alerts.jsonl`
- Health check endpoint at `/health`

## Data Flow

```
┌──────────────────┐     ┌──────────────────┐
│ dev-os-events    │     │ friction-log     │
│    .jsonl        │     │    .jsonl        │
└────────┬─────────┘     └────────┬─────────┘
         │                        │
         └──────────┬─────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │  OTel Collector  │
         │  (filelog recv)  │
         └────────┬─────────┘
                  │ OTLP
                  ▼
         ┌──────────────────┐
         │      Loki        │
         │  (log storage)   │
         └────────┬─────────┘
                  │ LogQL
                  ▼
         ┌──────────────────┐
         │     Grafana      │
         │  (dashboards)    │
         └────────┬─────────┘
                  │ Alert
                  ▼
         ┌──────────────────┐
         │     Webhook      │
         │  (notifications) │
         └──────────────────┘
```

## Log Schema

### Structured Metadata

The OTel collector extracts JSON fields as Loki structured metadata. These are queryable with `| field="value"` syntax (not label selectors).

**Common fields (dev-os-events):**
- `event_type` - Event classification
- `session_id` - Claude Code session UUID
- `timestamp` - Event timestamp
- `payload_*` - Nested payload fields (flattened)

**Common fields (friction):**
- `subdomain` - Error category
- `tool_name` - Which tool failed
- `domain` - High-level error domain
- `error_excerpt` - Error message snippet

### Querying

```logql
# All friction events
{service_name="devos"} | log_source="friction"

# Specific event type
{service_name="devos"} | log_source="dev-os-events" | event_type="tool_write"

# Count by subdomain
sum by (subdomain) (count_over_time({service_name="devos"} | log_source="friction" [1h]))
```

## Storage

All data is stored in `data/` subdirectories:

| Directory | Contents | Retention |
|-----------|----------|-----------|
| `data/loki/` | Log chunks and index | Default (31 days) |
| `data/grafana/` | Grafana state, plugins | Persistent |
| `data/alerts/` | Webhook alert log | Manual cleanup |
| `data/prometheus/` | Metrics (if used) | Default |
| `data/tempo/` | Traces (if used) | Default |

## Network

All services communicate via Docker network:

| Service | Internal Hostname | Ports |
|---------|-------------------|-------|
| Grafana/LGTM | `devos-lgtm` | 3000, 4317, 4318 |
| Collector | `devos-collector` | - |
| Webhook | `devos-webhook` | 8080 |

Grafana alerts reach the webhook via `http://devos-webhook:8080`.
