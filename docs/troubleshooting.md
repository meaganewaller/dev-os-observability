# Troubleshooting

## Common Issues

### No data in dashboards

**Symptoms:**
- Dashboards show "No data"
- Panels are empty

**Possible causes:**

1. **Collector not running**
   ```bash
   docker compose ps
   # Should show devos-collector as running
   ```

2. **Wrong time range**
   - Check dashboard time picker (top right)
   - Try "Last 1 hour" or "Last 7 days"

3. **Log files don't exist**
   ```bash
   ls -la ~/.claude/dev-os-events.jsonl
   ls -la ~/.claude/skill-friction-log.jsonl
   ```

4. **Collector started with `start_at: end` and no new events**
   - Either wait for new events, or backfill (see below)

5. **Query syntax issue**
   - Labels use `{label="value"}`
   - Structured metadata uses `| field="value"`

**Backfill historical data:**
```bash
# Edit otel-collector-config.yaml
# Change: start_at: end → start_at: beginning

docker compose restart devos-collector

# Wait for ingestion, then change back
# start_at: beginning → start_at: end
```

---

### Dashboards not appearing

**Symptoms:**
- DevOS folder empty in Grafana
- Dashboards existed but disappeared

**Solutions:**

1. **Check provisioning mount**
   ```bash
   docker exec devos-lgtm ls -la /devos-dashboards/
   # Should list JSON files
   ```

2. **Check provisioning config**
   ```bash
   docker exec devos-lgtm cat /otel-lgtm/grafana/conf/provisioning/dashboards/devos.yaml
   ```

3. **Restart Grafana**
   ```bash
   docker compose restart lgtm
   ```

4. **Check for JSON errors**
   ```bash
   # Validate JSON syntax
   cat grafana/dashboards/mission-control.json | jq '.' > /dev/null && echo "Valid"
   ```

---

### Alerts not firing

**Symptoms:**
- Alert rules show "OK" but condition should trigger
- No alerts in webhook logs

**Solutions:**

1. **Check alert state**
   - Go to http://localhost:3000/alerting/list
   - Click on the alert to see evaluation history

2. **Test query manually**
   ```bash
   curl -s -u admin:admin -G 'http://localhost:3000/api/datasources/proxy/uid/loki/loki/api/v1/query' \
     --data-urlencode 'query=sum(count_over_time({service_name="devos"} | log_source="friction" [1h]))' | jq '.data.result'
   ```

3. **Check contact point**
   ```bash
   # Verify webhook is reachable
   curl -s http://localhost:8085/health
   ```

4. **Check provisioning loaded**
   ```bash
   curl -s -u admin:admin 'http://localhost:3000/api/v1/provisioning/alert-rules' | jq '.[].title'
   ```

---

### Webhook not receiving alerts

**Symptoms:**
- Alerts fire in Grafana but no webhook logs
- `docker logs devos-webhook` shows nothing

**Solutions:**

1. **Check container is running**
   ```bash
   docker compose ps devos-webhook
   ```

2. **Test webhook directly**
   ```bash
   curl -X POST http://localhost:8085 \
     -H "Content-Type: application/json" \
     -d '{"title":"test"}'
   ```

3. **Check Grafana can reach webhook**
   ```bash
   docker exec devos-lgtm curl -s http://devos-webhook:8080/health
   ```

4. **Check contact point URL**
   ```bash
   curl -s -u admin:admin 'http://localhost:3000/api/v1/provisioning/contact-points' | jq '.'
   # Should show url: "http://devos-webhook:8080"
   ```

---

### Container won't start

**Symptoms:**
- `docker compose up` fails
- Container exits immediately

**Solutions:**

1. **Check logs**
   ```bash
   docker compose logs devos-lgtm
   docker compose logs devos-collector
   docker compose logs devos-webhook
   ```

2. **Port conflicts**
   ```bash
   lsof -i :3000
   lsof -i :8085
   # Kill conflicting processes or change ports in docker-compose.yaml
   ```

3. **Rebuild images**
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

4. **Clean slate**
   ```bash
   docker compose down -v
   rm -rf data/loki data/prometheus data/tempo data/grafana
   docker compose up -d
   ```

---

### Query returns empty results

**Symptoms:**
- LogQL query returns `[]`
- Data exists but query doesn't match

**Common issues:**

1. **Label vs structured metadata**
   ```logql
   # WRONG - log_source is not an indexed label
   {service_name="devos", log_source="friction"}

   # RIGHT - filter on structured metadata
   {service_name="devos"} | log_source="friction"
   ```

2. **Field name mismatch**
   ```bash
   # Check actual field names
   curl -s -u admin:admin -G 'http://localhost:3000/api/datasources/proxy/uid/loki/loki/api/v1/query' \
     --data-urlencode 'query={service_name="devos"}' \
     --data-urlencode 'limit=1' | jq '.data.result[0].stream | keys'
   ```

3. **Time range too narrow**
   - Extend the time range in query or dashboard

---

### High memory usage

**Symptoms:**
- Docker using too much memory
- System slowdown

**Solutions:**

1. **Check container stats**
   ```bash
   docker stats
   ```

2. **Reduce retention** (advanced)
   - Mount custom Loki config with shorter retention

3. **Limit container resources**
   ```yaml
   # In docker-compose.yaml
   services:
     lgtm:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

---

## Useful Commands

### Service management
```bash
docker compose up -d          # Start all
docker compose down           # Stop all
docker compose restart lgtm   # Restart specific service
docker compose logs -f        # Follow all logs
```

### Query Loki directly
```bash
# Raw query
curl -s -u admin:admin -G 'http://localhost:3000/api/datasources/proxy/uid/loki/loki/api/v1/query' \
  --data-urlencode 'query={service_name="devos"}' \
  --data-urlencode 'limit=10'

# With time range
curl -s -u admin:admin -G 'http://localhost:3000/api/datasources/proxy/uid/loki/loki/api/v1/query_range' \
  --data-urlencode 'query={service_name="devos"} | log_source="friction"' \
  --data-urlencode 'start='$(date -v-1H +%s)'000000000' \
  --data-urlencode 'end='$(date +%s)'000000000'
```

### Check labels
```bash
# Available labels
curl -s -u admin:admin 'http://localhost:3000/api/datasources/proxy/uid/loki/loki/api/v1/labels'

# Values for a label
curl -s -u admin:admin 'http://localhost:3000/api/datasources/proxy/uid/loki/loki/api/v1/label/service_name/values'
```

### Grafana API
```bash
# List dashboards
curl -s -u admin:admin 'http://localhost:3000/api/search?type=dash-db' | jq '.[].title'

# List alert rules
curl -s -u admin:admin 'http://localhost:3000/api/v1/provisioning/alert-rules' | jq '.[].title'

# List contact points
curl -s -u admin:admin 'http://localhost:3000/api/v1/provisioning/contact-points' | jq '.[].name'
```

---

## Getting Help

1. Check container logs: `docker compose logs <service>`
2. Verify connectivity between services
3. Test queries in Grafana Explore (http://localhost:3000/explore)
4. Check Grafana documentation: https://grafana.com/docs/
