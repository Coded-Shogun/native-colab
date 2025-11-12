# Enterprise Monitoring & Observability

Native Colab Enterprise provides comprehensive monitoring and observability through Prometheus, Grafana, and integrated alerting systems.

## Metrics Collection

### Prometheus Configuration

```yaml
# /etc/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'nativecolab'
    static_configs:
      - targets: ['app1:8000', 'app2:8000', 'app3:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
```

### Application Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# HTTP metrics
http_requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
http_request_duration_seconds = Histogram('http_request_duration_seconds', 'HTTP request latency')

# Business metrics
active_users_total = Gauge('active_users_total', 'Total active users')
projects_created_total = Counter('projects_created_total', 'Total projects created')
tasks_completed_total = Counter('tasks_completed_total', 'Total tasks completed')

# Database metrics
database_connections_active = Gauge('database_connections_active', 'Active database connections')
database_query_duration_seconds = Histogram('database_query_duration_seconds', 'Database query duration')

# Security metrics
failed_login_attempts_total = Counter('failed_login_attempts_total', 'Failed login attempts')
security_events_total = Counter('security_events_total', 'Security events', ['event_type', 'severity'])
```

### Metrics Endpoint

```python
# backend/app/api/v1/metrics.py
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

## Grafana Dashboards

### System Overview Dashboard

```json
{
  "dashboard": {
    "title": "Native Colab - System Overview",
    "panels": [
      {
        "title": "HTTP Requests per Second",
        "targets": [{
          "expr": "rate(http_requests_total[5m])"
        }]
      },
      {
        "title": "Request Latency p95",
        "targets": [{
          "expr": "histogram_quantile(0.95, http_request_duration_seconds_bucket)"
        }]
      },
      {
        "title": "Error Rate",
        "targets": [{
          "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
        }]
      },
      {
        "title": "Active Users",
        "targets": [{
          "expr": "active_users_total"
        }]
      }
    ]
  }
}
```

## Log Aggregation

### Centralized Logging

```yaml
# docker-compose.logging.yml
services:
  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yml:/etc/loki/config.yml

  promtail:
    image: grafana/promtail:latest
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=false
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## Alerting

### Alert Rules

```yaml
# /etc/prometheus/alerts.yml
groups:
  - name: nativecolab
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} requests/sec"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"

      - alert: HighMemoryUsage
        expr: (node_memory_Active_bytes / node_memory_MemTotal_bytes) > 0.9
        for: 10m
        labels:
          severity: warning
```

### AlertManager Configuration

```yaml
# /etc/alertmanager/config.yml
global:
  slack_api_url: 'https://hooks.slack.com/services/xxx'

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'slack-critical'

  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'

    - match:
        severity: warning
      receiver: 'slack-warnings'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: 'YOUR_PAGERDUTY_KEY'

  - name: 'slack-critical'
    slack_configs:
      - channel: '#alerts-critical'
        title: 'Critical Alert'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'slack-warnings'
    slack_configs:
      - channel: '#alerts-warnings'
```

## Distributed Tracing

### OpenTelemetry Integration

```python
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

# Initialize tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Instrument FastAPI
FastAPIInstrumentor.instrument_app(app)

# Custom spans
tracer = trace.get_tracer(__name__)

@router.get("/projects/{project_id}")
async def get_project(project_id: int):
    with tracer.start_as_current_span("get_project"):
        with tracer.start_as_current_span("database_query"):
            project = await db.query(Project).filter(Project.id == project_id).first()
        return project
```

## Performance Monitoring

### Application Performance Monitoring (APM)

```python
# Integration with Sentry
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="https://your-dsn@sentry.io/project",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    environment="production"
)
```

## Best Practices

1. **Golden Signals**: Monitor latency, traffic, errors, and saturation
2. **SLOs**: Define Service Level Objectives
3. **Dashboards**: Create role-specific dashboards
4. **Alerts**: Alert on symptoms, not causes
5. **On-Call**: Maintain on-call rotation
6. **Runbooks**: Document incident response procedures

## Next Steps

- [High Availability →](./high-availability)
- [Scaling →](./scaling)
- [Security Overview →](./security)
