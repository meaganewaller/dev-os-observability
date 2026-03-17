# Configuration

## File Overview

```
dev-os-observability/
├── docker-compose.yaml           # Service definitions
├── otel-collector-config.yaml    # Log collection
├── grafana/
│   ├── dashboards/               # Dashboard JSON files
│   │   ├── mission-control.json
│   │   ├── friction-overview.json
│   │   ├── session-activity.json
│   │   ├── cue-effectiveness.json
│   │   ├── hook-performance.json
│   │   ├── quality-signals.json
│   │   └── weekly-trends.json
│   └── provisioning/
│       ├── dashboards/
│       │   └── devos.yaml        # Dashboard provisioning
│       └── alerting/
│           ├── rules.yaml        # Alert rules
│           ├── contactpoints.yaml
│           └── policies.yaml
└── webhook/
    ├── Dockerfile
    └── server.py
```

---

## docker-compose.yaml

### devos-lgtm

```yaml
lgtm:
  image: grafana/otel-lgtm:latest
  container_name: devos-lgtm
  ports:
    - "3000:3000"   # Grafana UI
    - "4317:4317"   # OTLP gRPC
    - "4318:4318"   # OTLP HTTP
  environment:
    GF_SECURITY_ADMIN_PASSWORD: admin
  volumes:
    - ./grafana/dashboards:/devos-dashboards
    - ./grafana/provisioning/dashboards/devos.yaml:/otel-lgtm/grafana/conf/provisioning/dashboards/devos.yaml
    - ./grafana/provisioning/alerting:/otel-lgtm/grafana/conf/provisioning/alerting
```

**Environment variables:**
| Variable | Description | Default |
|----------|-------------|---------|
| `GF_SECURITY_ADMIN_PASSWORD` | Admin password | `admin` |
| `GF_AUTH_ANONYMOUS_ENABLED` | Allow anonymous access | `true` |
| `GF_AUTH_ANONYMOUS_ORG_ROLE` | Anonymous user role | `Admin` |

### devos-collector

```yaml
devos-collector:
  image: otel/opentelemetry-collector-contrib:latest
  container_name: devos-collector
  volumes:
    - ./otel-collector-config.yaml:/etc/otelcol/config.yaml
    - ~/.claude:/claude-data
  command: ["--config=/etc/otelcol/config.yaml"]
  depends_on:
    - lgtm
```

**Volume mounts:**
- `~/.claude` → `/claude-data` - Access to DevOS log files

### devos-webhook

```yaml
devos-webhook:
  build: ./webhook
  container_name: devos-webhook
  ports:
    - "8085:8080"
  volumes:
    - ./data/alerts:/data
  environment:
    ALERTS_FILE: /data/alerts.jsonl
```

**Environment variables:**
| Variable | Description | Default |
|----------|-------------|---------|
| `ALERTS_FILE` | Where to write alerts | `/data/alerts.jsonl` |
| `PORT` | HTTP port | `8080` |

---

## otel-collector-config.yaml

### Receivers

```yaml
receivers:
  filelog/devos:
    include:
      - /claude-data/dev-os-events.jsonl
    start_at: end
    operators:
      - type: json_parser
        parse_from: body
      - type: add
        field: attributes.log_source
        value: dev-os-events

  filelog/friction:
    include:
      - /claude-data/skill-friction-log.jsonl
    start_at: end
    operators:
      - type: json_parser
        parse_from: body
      - type: add
        field: attributes.log_source
        value: friction
```

**Key settings:**
| Setting | Description |
|---------|-------------|
| `start_at: end` | Only new entries (change to `beginning` for backfill) |
| `json_parser` | Extract JSON fields as attributes |
| `add log_source` | Label to distinguish log types |

### Processors

```yaml
processors:
  resource/devos:
    attributes:
      - key: service.name
        value: devos
        action: upsert
  batch:
```

### Exporters

```yaml
exporters:
  otlp:
    endpoint: devos-lgtm:4317
    tls:
      insecure: true
  debug:
    verbosity: detailed
```

### Pipeline

```yaml
service:
  pipelines:
    logs:
      receivers: [filelog/devos, filelog/friction]
      processors: [resource/devos, batch]
      exporters: [otlp, debug]
```

---

## Dashboard Provisioning

**File:** `grafana/provisioning/dashboards/devos.yaml`

```yaml
apiVersion: 1

providers:
  - name: DevOS
    type: file
    folder: DevOS
    folderUid: devos
    disableDeletion: false
    updateIntervalSeconds: 30
    allowUiUpdates: true
    options:
      path: /devos-dashboards
      foldersFromFilesStructure: false
```

**Settings:**
| Setting | Description |
|---------|-------------|
| `updateIntervalSeconds: 30` | Check for changes every 30s |
| `allowUiUpdates: true` | Save changes made in UI |
| `disableDeletion: false` | Allow removing dashboards |

---

## Alert Provisioning

### Rules

**File:** `grafana/provisioning/alerting/rules.yaml`

See [alerting.md](alerting.md) for rule format.

### Contact Points

**File:** `grafana/provisioning/alerting/contactpoints.yaml`

```yaml
apiVersion: 1

contactPoints:
  - orgId: 1
    name: devos-webhook
    receivers:
      - uid: webhook-alerts
        type: webhook
        settings:
          url: "http://devos-webhook:8080"
          httpMethod: POST
        disableResolveMessage: false
```

### Notification Policies

**File:** `grafana/provisioning/alerting/policies.yaml`

```yaml
apiVersion: 1

policies:
  - orgId: 1
    receiver: devos-webhook
    group_by:
      - grafana_folder
      - alertname
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
```

---

## Adding New Log Sources

To ingest additional log files:

1. Add receiver in `otel-collector-config.yaml`:
```yaml
receivers:
  filelog/newlog:
    include:
      - /claude-data/new-log.jsonl
    start_at: end
    operators:
      - type: json_parser
        parse_from: body
      - type: add
        field: attributes.log_source
        value: new-log
```

2. Add to pipeline:
```yaml
service:
  pipelines:
    logs:
      receivers: [filelog/devos, filelog/friction, filelog/newlog]
```

3. Restart collector:
```bash
docker compose restart devos-collector
```

4. Query in Grafana:
```logql
{service_name="devos"} | log_source="new-log"
```

---

## Customizing Retention

The LGTM image uses default retention (31 days for Loki). To customize, you'd need to mount custom config files for each service. For most use cases, the defaults are sufficient.

---

## Security Considerations

**Current setup is for local development:**
- Grafana uses `admin/admin` credentials
- Anonymous access is enabled
- No TLS encryption

**For production:**
1. Change `GF_SECURITY_ADMIN_PASSWORD`
2. Disable anonymous auth: `GF_AUTH_ANONYMOUS_ENABLED=false`
3. Add TLS to OTLP endpoints
4. Restrict network access
