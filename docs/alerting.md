# Alerting

## Overview

Alerts are configured via Grafana's provisioning system and delivered to a local webhook service.

## Alert Rules

### Friction Spike

**File:** `grafana/provisioning/alerting/rules.yaml`

| Property | Value |
|----------|-------|
| UID | `friction-spike` |
| Condition | >20 friction events in 1 hour |
| Severity | Warning |
| Evaluation | Every 1 minute |
| Fires After | 5 minutes of sustained condition |

**Query:**
```logql
sum(count_over_time({service_name="devos"} | log_source="friction" [1h]))
```

**When it fires:**
- Sustained friction indicates systemic issues
- Check friction breakdown for patterns
- Common causes: attempting to read large files repeatedly

---

### ADR-0008: Resource Limit Breach

| Property | Value |
|----------|-------|
| UID | `adr0008-breach` |
| Condition | >50 resource-limit errors in 7 days |
| Severity | Critical |
| Evaluation | Every 1 minute |
| Fires After | Immediately |

**Query:**
```logql
sum(count_over_time({service_name="devos"} | log_source="friction" | subdomain="resource-limit" [7d]))
```

**When it fires:**
- Weekly target from ADR-0008 exceeded
- Review chunked operation patterns
- Check for repeated attempts on large files

---

## Contact Points

### Webhook (devos-webhook)

**File:** `grafana/provisioning/alerting/contactpoints.yaml`

```yaml
contactPoints:
  - orgId: 1
    name: devos-webhook
    receivers:
      - uid: webhook-alerts
        type: webhook
        settings:
          url: "http://devos-webhook:8080"
          httpMethod: POST
```

The webhook service logs alerts to:
- stdout (viewable via `docker logs devos-webhook`)
- `data/alerts/alerts.jsonl`

---

## Notification Policy

**File:** `grafana/provisioning/alerting/policies.yaml`

```yaml
policies:
  - orgId: 1
    receiver: devos-webhook
    group_by: [grafana_folder, alertname]
    group_wait: 30s
    group_interval: 5m
    repeat_interval: 4h
```

| Setting | Value | Description |
|---------|-------|-------------|
| group_wait | 30s | Wait before sending first notification |
| group_interval | 5m | Wait between notifications for same group |
| repeat_interval | 4h | Re-notify if alert still firing |

---

## Viewing Alerts

### In Grafana

- **Alert Rules:** http://localhost:3000/alerting/list
- **Alert State:** http://localhost:3000/alerting/alerts
- **Silence Alerts:** http://localhost:3000/alerting/silences

### Via Webhook

```bash
# Live alerts
docker logs -f devos-webhook

# Alert history
cat data/alerts/alerts.jsonl | jq '.'

# Recent alerts
tail -10 data/alerts/alerts.jsonl | jq '.'

# Filter by severity
cat data/alerts/alerts.jsonl | jq 'select(.severity == "critical")'
```

---

## Adding New Alerts

1. Add rule to `grafana/provisioning/alerting/rules.yaml`:

```yaml
- uid: my-new-alert
  title: My New Alert
  condition: threshold
  data:
    - refId: A
      relativeTimeRange:
        from: 3600
        to: 0
      datasourceUid: loki
      model:
        expr: <your LogQL query>
        instant: true
        refId: A
    - refId: threshold
      datasourceUid: __expr__
      model:
        type: threshold
        expression: A
        conditions:
          - evaluator:
              type: gt
              params: [<threshold_value>]
            operator:
              type: and
            reducer:
              type: last
        refId: threshold
  noDataState: OK
  execErrState: Error
  for: 5m
  annotations:
    summary: Alert summary
    description: Detailed description
  labels:
    severity: warning
  isPaused: false
```

2. Restart Grafana:
```bash
docker compose restart lgtm
```

3. Verify in Grafana UI: http://localhost:3000/alerting/list

---

## Alternative Contact Points

### Slack

```yaml
contactPoints:
  - orgId: 1
    name: slack
    receivers:
      - uid: slack-devos
        type: slack
        settings:
          url: "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
          username: "DevOS Alerts"
```

### Email (requires SMTP)

```yaml
# Add to docker-compose.yaml environment:
environment:
  GF_SMTP_ENABLED: "true"
  GF_SMTP_HOST: "smtp.gmail.com:587"
  GF_SMTP_USER: "your-email@gmail.com"
  GF_SMTP_PASSWORD: "app-password"

# Then in contactpoints.yaml:
contactPoints:
  - orgId: 1
    name: email
    receivers:
      - uid: email-devos
        type: email
        settings:
          addresses: "alerts@example.com"
```

### ntfy.sh (free push notifications)

```yaml
contactPoints:
  - orgId: 1
    name: ntfy
    receivers:
      - uid: ntfy-devos
        type: webhook
        settings:
          url: "https://ntfy.sh/your-topic-name"
          httpMethod: POST
```

Subscribe at: https://ntfy.sh/your-topic-name

---

## Silencing Alerts

To temporarily silence alerts:

1. Go to http://localhost:3000/alerting/silences
2. Click "Add Silence"
3. Add matchers (e.g., `alertname = friction-spike`)
4. Set duration
5. Save

Or via API:
```bash
curl -X POST -u admin:admin \
  -H "Content-Type: application/json" \
  -d '{
    "matchers": [{"name": "alertname", "value": "friction-spike", "isRegex": false}],
    "startsAt": "2024-01-01T00:00:00Z",
    "endsAt": "2024-01-02T00:00:00Z",
    "comment": "Silencing during maintenance"
  }' \
  http://localhost:3000/api/alertmanager/grafana/api/v2/silences
```
