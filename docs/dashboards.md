# Dashboards

All dashboards are provisioned automatically and appear in the **DevOS** folder in Grafana.

## Mission Control

**Purpose:** Single-pane-of-glass for system health.

**URL:** http://localhost:3000/d/devos-mission-control

### Panels

| Panel | Description | Thresholds |
|-------|-------------|------------|
| Write Success Rate | writes / (writes + Write/Edit failures) | <80% red, 80-90% yellow, >90% green |
| Read Failures | Read tool failures (usually resource-limit) | >100 red, 50-100 yellow, <50 green |
| Bash Failures | Bash commands with non-zero exit | >50 red, 20-50 yellow, <20 green |
| Friction Rate | friction per 100 writes | >30% red, 15-30% yellow, <15% green |
| Reversal Rate | reversals per 100 writes | >7% red, 3-7% yellow, <3% green |
| ADR-0008 Tracker | resource-limit errors (7d) | >50 red, 25-50 yellow, <25 green |
| Activity Stats | Sessions, Writes, Total Failures, Tests, Cues, Tradeoffs | - |
| Activity Timeline | Writes, Read failures, Bash failures, friction over time | - |
| Failure Breakdown by Tool | Pie chart: Read vs Bash vs Write/Edit | - |
| Friction Breakdown | Pie chart by subdomain | - |
| Quality Signals | Reversals, large changes, compactions | Threshold-based |

### When to Use

- Daily health check
- Quick status before/after sessions
- Identifying systemic issues

---

## Friction Overview

**Purpose:** Deep dive into friction events. Track ADR-0008 goals.

**URL:** http://localhost:3000/d/devos-friction

### Panels

| Panel | Description |
|-------|-------------|
| Friction Events Over Time | Stacked bar chart by subdomain |
| Friction by Subdomain | Pie chart of total distribution |
| Friction by Tool | Which tools cause most friction |
| ADR-0008 Goal Tracker | Resource-limit errors vs <50 target |
| Recent Friction Events | Log viewer |

### Key Metrics

- **resource-limit**: File too large, token limit exceeded
- **file-not-found**: Path doesn't exist
- **command-failed**: Shell command error
- **parse**: JSON/YAML syntax error

---

## Session Activity

**Purpose:** Understand session patterns and tool usage.

**URL:** http://localhost:3000/d/devos-sessions

### Panels

| Panel | Description |
|-------|-------------|
| Events Over Time by Type | All event types |
| Sessions/Writes/Failures/Tests | Quick stats |
| Event Type Distribution | Pie chart |
| Tasks Completed | Timeline |
| Recent Events | Log viewer |

### Use Cases

- How many sessions per day?
- What's the write-to-failure ratio?
- When are tests being run?

---

## Cue Effectiveness

**Purpose:** Monitor the cue system (contextual guidance injection).

**URL:** http://localhost:3000/d/devos-cues

### Panels

| Panel | Description |
|-------|-------------|
| Cue Activity Over Time | cue_fired vs cue_matched |
| Total Cues Fired/Matched | Stats |
| Cue Efficiency Ratio | Fired per match (lower = better targeting) |
| Cues by Trigger Type | prompt, bash, tool, etc. |
| Decisions & Reversals | Track decision quality |
| Recent Cue Events | Log viewer |

### Key Insights

- High fired:matched ratio = cues triggering too broadly
- Low cue activity = cues may not be matching relevant contexts

---

## Hook Performance

**Purpose:** Monitor hook reliability and tool success rates.

**URL:** http://localhost:3000/d/devos-hooks

### Panels

| Panel | Description |
|-------|-------------|
| Friction by Tool Over Time | Which tools have issues |
| Tool Write Success Rate | Gauge |
| Large Changes | Flagged large modifications |
| Reversals | Work undone |
| Context Compactions | Sessions hitting limits |
| Error Patterns by Domain | Bar chart |
| Recent Failures | Log viewer |

---

## Quality Signals

**Purpose:** Track decision quality and development practices.

**URL:** http://localhost:3000/d/devos-quality

### Panels

| Panel | Description | Target |
|-------|-------------|--------|
| Reversal Rate | % of writes that get undone | <5% |
| Large Change Rate | % of writes flagged large | <10% |
| Decision Tradeoffs | Documented tradeoffs | Higher is better |
| Principles Activated | Principle-guided decisions | Higher is better |
| Quality Events Timeline | All quality-related events | - |
| Individual Stats | Reversals, large changes, tradeoffs, opinions, compactions, domain modeling | - |

### Interpretation

- **High reversal rate**: May indicate rushing or insufficient planning
- **High large change rate**: Consider breaking work into smaller chunks
- **Low tradeoffs documented**: May be missing decision documentation

---

## Weekly Trends

**Purpose:** Week-over-week comparison and long-term trends.

**URL:** http://localhost:3000/d/devos-weekly

### Panels

| Panel | Description |
|-------|-------------|
| Friction Events - Weekly | Weekly totals |
| Productivity - Weekly | Writes and tasks completed |
| This Week vs Last Week | Friction comparison |
| Sessions/Tests This Week | Activity stats |
| Friction by Subdomain - 4 Week Trend | Trend lines |
| Success Rate Trend | Daily success rate |
| Daily Activity | Events per day |

### Use Cases

- Weekly review preparation
- Identifying long-term patterns
- Measuring improvement initiatives

---

## Collaboration Insights

**Purpose:** Understand how human and AI work together.

**URL:** http://localhost:3000/d/devos-collaboration

### Panels

| Panel | Description |
|-------|-------------|
| Session Archetypes | Distribution: sprint, flow, marathon |
| Session Duration Categories | Quick, short, medium, long, marathon |
| Task List Usage | Sessions using task lists for planning |
| Avg Writes/Session | Throughput indicator |
| Change Types | Architecture, bugfix, feature, test, docs |
| Risk Profile | Low, medium, high risk changes |
| Top Cues Fired | Most helpful guidance injections |
| Cue Triggers by Type | Prompt, bash, tool triggers |

### Key Insights

- **Session archetypes** reveal work style preferences
- **Change type distribution** shows strategic vs tactical work balance
- **Cue effectiveness** indicates how well guidance is targeted

---

## Time & Effort

**Purpose:** Track session duration, productivity, and work patterns.

**URL:** http://localhost:3000/d/devos-time-effort

### Panels

| Panel | Description |
|-------|-------------|
| Productivity (Writes/Session) | Average file modifications per session |
| Efficiency (Writes/Friction) | Smoother flow = higher ratio |
| Duration Distribution | How long sessions typically last |
| Activity Timeline | Writes, tests, friction over time |
| Daily Writes/Sessions | Averages per day |
| Test Coverage Rate | Tests per write (TDD indicator) |
| Failure Rate | Tool failures as % of writes |

### Use Cases

- How productive are our sessions?
- Are we spending time efficiently (low friction)?
- What's our typical session length?

---

## Project Focus

**Purpose:** Understand what we work on - categories, risk, and skills.

**URL:** http://localhost:3000/d/devos-project-focus

### Panels

| Panel | Description |
|-------|-------------|
| Change Categories | Architecture, bugfix, feature, test distribution |
| Risk Profile | Low/medium/high risk changes |
| Skills Applied | Engineering skills used |
| Architecture/Bugfix/Test Ratios | Balance of work types |
| High Risk Ratio | Safety indicator |
| Change Types Over Time | Trends in work categories |

### Key Metrics

- **Architecture Ratio**: Higher = more strategic work
- **Bugfix Ratio**: Lower = better initial quality
- **Test Ratio**: Higher = better coverage
- **High Risk Ratio**: Lower = safer changes

---

## Customizing Dashboards

Dashboards are stored in `grafana/dashboards/` as JSON files.

**To modify:**
1. Edit in Grafana UI (changes save to JSON)
2. Or edit JSON directly and restart: `docker compose restart lgtm`

**To add a new dashboard:**
1. Create JSON file in `grafana/dashboards/`
2. Use `devos-` prefix for UID
3. Provisioner will pick it up within 30 seconds

### Query Patterns

```logql
# Count events by type
sum by (event_type) (count_over_time({service_name="devos"} | log_source="dev-os-events" [$__interval]))

# Filter by specific event
{service_name="devos"} | log_source="dev-os-events" | event_type="tool_write"

# Friction by subdomain
sum by (subdomain) (count_over_time({service_name="devos"} | log_source="friction" [$__range]))

# Rate calculation
sum(count_over_time({...} | event_type="a" [...])) / sum(count_over_time({...} | event_type="b" [...])) * 100
```
