# Skill: Event Bus

## Skill Name
event_bus.publish / event_bus.subscribe

## Category
Integration / Event-Driven Architecture

## Purpose
Enable event-driven workflows by publishing task lifecycle events to a message broker (Kafka or Dapr). Allows external systems to react to vault state changes and enables decoupled, scalable agent orchestration.

## When This Skill Is Triggered

### Publishing (automatic)
Events are published on every state transition:
- `task.claimed` — file moved from `/Inbox` to `/Active`
- `task.completed` — file moved to `/Done`
- `task.escalated` — file moved to `/Review`
- `approval.requested` — file created in `/Pending_Approval`
- `approval.decided` — file moved from `/Pending_Approval` to `/Approved` or `/Done`
- `rollback.executed` — rollback completed
- `briefing.generated` — new briefing created
- `error.logged` — error recorded in `/Logs`

### Subscribing (on startup)
The agent subscribes to inbound events:
- `task.inbound` — external system drops a task into the pipeline
- `approval.external` — external approval decision received
- `command.execute` — remote command trigger

## Inputs

### Publish
- **event_type**: One of the event names above
- **payload**: JSON object with event details
- **source**: Agent name or system identifier

### Subscribe
- **topic**: Event topic to listen on
- **handler**: Skill to invoke when event received

## Outputs
- Event published to broker (Kafka topic or Dapr pub/sub)
- Subscription callback triggers the appropriate skill

## Event Schema

```json
{
  "event_id": "uuid",
  "event_type": "task.completed",
  "timestamp": "2026-01-27T14:30:00Z",
  "source": "claude-code",
  "vault": "ai-employee",
  "payload": {
    "task_file": "2026-01-27_setup_mcp_server.md",
    "from_folder": "/Active",
    "to_folder": "/Done",
    "metadata": {}
  }
}
```

## Broker Configuration

### Option A — Kafka

```yaml
# kafka-config.yaml
bootstrap_servers: "localhost:9092"
topics:
  outbound: "vault.events"
  inbound: "vault.commands"
consumer_group: "ai-employee-agent"
serialization: "json"
```

**Setup**:
1. Run Kafka locally or use a managed service
2. Create topics: `vault.events`, `vault.commands`
3. Agent publishes to `vault.events` on every state transition
4. External systems subscribe to `vault.events`
5. Agent consumes from `vault.commands` for inbound tasks

### Option B — Dapr

```yaml
# dapr-pubsub-component.yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: vault-pubsub
spec:
  type: pubsub.redis
  version: v1
  metadata:
    - name: redisHost
      value: "localhost:6379"
    - name: redisPassword
      value: ""
```

**Setup**:
1. Install Dapr CLI and initialize (`dapr init`)
2. Place component YAML in `~/.dapr/components/`
3. Agent uses Dapr HTTP API to publish:
   `POST http://localhost:3500/v1.0/publish/vault-pubsub/vault.events`
4. Subscribe via Dapr subscription config or programmatic endpoint

## Workflow

### Publishing Flow
1. A state transition occurs (file move, log entry, etc.)
2. The agent constructs an event object using the schema above
3. The event is published to the configured broker
4. A confirmation log is written to `/Logs/YYYY-MM-DD_event_published.md`

### Subscription Flow
1. On session start, the agent checks the inbound topic for pending messages
2. For each message:
   - Parse the event payload
   - Route to the appropriate skill (e.g., `task.inbound` -> create file in `/Inbox`)
   - Acknowledge the message
3. Log the processed event in `/Logs`

## File-Based Fallback

If no broker is available, the event bus falls back to file-based events:

- **Publish**: Write event JSON to `/Logs/events/YYYY-MM-DD_<event_type>_<uuid>.json`
- **Subscribe**: Scan `/Inbox/events/` for new `.json` files on each autonomy loop cycle
- **Acknowledge**: Move processed event files to `/Done/events/`

This ensures the event-driven pattern works even without infrastructure, making skills portable and demo-friendly.

## Integration Points

| External System | Subscribes To | Publishes |
|----------------|--------------|-----------|
| CI/CD Pipeline | `task.completed` | `task.inbound` (deploy tasks) |
| Monitoring/Alerting | `error.logged`, `task.escalated` | `command.execute` (remediation) |
| Approval UI | `approval.requested` | `approval.external` |
| Other Agents | `task.completed` | `task.inbound` (chained workflows) |

## Rules
- Every state transition MUST publish an event (no silent transitions)
- Events are fire-and-forget for publishing; failures are logged but do not block the task
- Inbound events are validated against the schema before processing
- Unknown event types are logged and ignored (no crashes)
- The file-based fallback is always available as a baseline
