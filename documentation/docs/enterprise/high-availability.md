# High Availability Architecture

Native Colab Enterprise is designed for high availability with redundancy at every layer, ensuring 99.9%+ uptime for mission-critical collaboration workflows.

## Architecture Overview

### Multi-Tier Architecture

```
┌─────────────────────────────────────────┐
│           Load Balancer (HA)            │
│     (HAProxy/nginx + Keepalived)        │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼────┐           ┌───▼────┐
│  App   │           │  App   │
│ Server │◄─────────►│ Server │
│   #1   │   Sync    │   #2   │
└───┬────┘           └───┬────┘
    │                     │
    └──────────┬──────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───▼─────┐         ┌────▼────┐
│Database │◄───────►│ Database│
│ Primary │  Stream │ Replica │
└───┬─────┘         └────┬────┘
    │                    │
┌───▼────────────────────▼───┐
│    Redis Cluster (HA)      │
│  (Sentinel for failover)   │
└────────────────────────────┘
```

## Load Balancing

### HAProxy Configuration

**Active-Active Load Balancing:**
```haproxy
# /etc/haproxy/haproxy.cfg
global
    maxconn 4096
    log /dev/log local0
    user haproxy
    group haproxy
    daemon

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog
    option dontlognull

# Frontend (public facing)
frontend http_front
    bind *:80
    bind *:443 ssl crt /etc/ssl/certs/nativecolab.pem
    redirect scheme https if !{ ssl_fc }
    default_backend app_servers

# Backend (application servers)
backend app_servers
    balance roundrobin
    option httpchk GET /health
    http-check expect status 200

    server app1 10.0.1.10:8000 check inter 2000 rise 2 fall 3
    server app2 10.0.1.11:8000 check inter 2000 rise 2 fall 3
    server app3 10.0.1.12:8000 check inter 2000 rise 2 fall 3

# Statistics
listen stats
    bind *:8404
    stats enable
    stats uri /stats
    stats refresh 30s
```

### Nginx Load Balancing

**Alternative: Nginx as Load Balancer:**
```nginx
# /etc/nginx/nginx.conf
upstream backend {
    least_conn;  # Use least connections algorithm

    server 10.0.1.10:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.11:8000 max_fails=3 fail_timeout=30s;
    server 10.0.1.12:8000 max_fails=3 fail_timeout=30s;

    # Health check
    check interval=3000 rise=2 fall=3 timeout=1000 type=http;
    check_http_send "GET /health HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx http_3xx;
}

server {
    listen 443 ssl http2;
    server_name app.nativecolab.com;

    ssl_certificate /etc/ssl/certs/nativecolab.crt;
    ssl_certificate_key /etc/ssl/private/nativecolab.key;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Virtual IP with Keepalived

**Floating IP for Load Balancer HA:**
```conf
# /etc/keepalived/keepalived.conf
vrrp_script check_haproxy {
    script "/usr/bin/killall -0 haproxy"
    interval 2
    weight 2
}

vrrp_instance VI_1 {
    state MASTER
    interface eth0
    virtual_router_id 51
    priority 101
    advert_int 1

    authentication {
        auth_type PASS
        auth_pass secretpass123
    }

    virtual_ipaddress {
        192.168.1.100/24
    }

    track_script {
        check_haproxy
    }
}
```

## Database High Availability

### PostgreSQL Streaming Replication

**Primary Server Configuration:**
```conf
# /var/lib/postgresql/data/postgresql.conf
wal_level = replica
max_wal_senders = 3
wal_keep_size = 1GB
hot_standby = on
synchronous_commit = on
synchronous_standby_names = 'standby1'

# Connection settings
listen_addresses = '*'
max_connections = 200
```

**Replica Server Configuration:**
```conf
# /var/lib/postgresql/data/postgresql.conf
hot_standby = on
hot_standby_feedback = on
wal_receiver_status_interval = 10s
```

**Replication Monitoring:**
```sql
-- Check replication status
SELECT
    client_addr,
    state,
    sync_state,
    replay_lag,
    write_lag,
    flush_lag
FROM pg_stat_replication;

-- Check replication delay
SELECT
    now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

### Automatic Failover with Patroni

**Patroni Configuration:**
```yaml
# /etc/patroni/patroni.yml
scope: nativecolab
name: postgres1
namespace: /service/

etcd:
  hosts: 10.0.1.20:2379,10.0.1.21:2379,10.0.1.22:2379

bootstrap:
  dcs:
    ttl: 30
    loop_wait: 10
    retry_timeout: 10
    maximum_lag_on_failover: 1048576
    postgresql:
      use_pg_rewind: true
      parameters:
        max_connections: 200
        shared_buffers: 4GB
        effective_cache_size: 12GB

  initdb:
    - encoding: UTF8
    - data-checksums

postgresql:
  listen: 0.0.0.0:5432
  connect_address: 10.0.1.10:5432
  data_dir: /var/lib/postgresql/14/main
  bin_dir: /usr/lib/postgresql/14/bin
  authentication:
    replication:
      username: replicator
      password: repl_password
    superuser:
      username: postgres
      password: postgres_password

tags:
    nofailover: false
    noloadbalance: false
    clonefrom: false
```

**Automatic Failover Process:**
1. Primary node failure detected (< 30 seconds)
2. Patroni initiates leader election
3. Best replica promoted to primary
4. Other replicas reconfigured
5. Application connections redirected
6. Total downtime: < 60 seconds

## Redis High Availability

### Redis Sentinel

**Sentinel Configuration:**
```conf
# /etc/redis/sentinel.conf
port 26379
dir /var/lib/redis
sentinel monitor mymaster 10.0.1.30 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel parallel-syncs mymaster 1
sentinel failover-timeout mymaster 10000

# Notification script
sentinel notification-script mymaster /etc/redis/notify.sh
sentinel client-reconfig-script mymaster /etc/redis/reconfig.sh
```

**Redis Configuration:**
```conf
# /etc/redis/redis.conf
bind 0.0.0.0
port 6379
protected-mode yes
requirepass your_redis_password

# Persistence
save 900 1
save 300 10
save 60 10000

# Replication
replicaof 10.0.1.30 6379  # On replicas only
masterauth your_redis_password

# Memory
maxmemory 4gb
maxmemory-policy allkeys-lru
```

### Redis Cluster (Alternative)

**Cluster Mode for Horizontal Scaling:**
```bash
# Create Redis cluster with 3 masters and 3 replicas
redis-cli --cluster create \
  10.0.1.30:6379 \
  10.0.1.31:6379 \
  10.0.1.32:6379 \
  10.0.1.33:6379 \
  10.0.1.34:6379 \
  10.0.1.35:6379 \
  --cluster-replicas 1
```

## Application High Availability

### Multi-Instance Deployment

**Docker Compose with Replicas:**
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  app:
    image: nativecolab/backend:latest
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    environment:
      - DATABASE_URL=postgresql://user:pass@postgres-primary:5432/db
      - REDIS_URL=redis://redis-sentinel:26379
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Kubernetes Deployment

**HA Deployment on Kubernetes:**
```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nativecolab-backend
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0

  selector:
    matchLabels:
      app: nativecolab-backend

  template:
    metadata:
      labels:
        app: nativecolab-backend
    spec:
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - nativecolab-backend
              topologyKey: kubernetes.io/hostname

      containers:
      - name: backend
        image: nativecolab/backend:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            cpu: 500m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 4Gi

        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3

        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

---
apiVersion: v1
kind: Service
metadata:
  name: nativecolab-backend
spec:
  type: LoadBalancer
  selector:
    app: nativecolab-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: nativecolab-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: nativecolab-backend
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

## Health Checks

### Application Health Endpoint

```python
# app/api/v1/health.py
from fastapi import APIRouter, HTTPException
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
async def health_check():
    """Comprehensive health check for load balancer"""
    health_status = {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Check database
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        health_status["database"] = "healthy"
    except Exception as e:
        health_status["database"] = "unhealthy"
        health_status["database_error"] = str(e)
        health_status["status"] = "degraded"

    # Check Redis
    try:
        redis = get_redis_client()
        await redis.ping()
        health_status["redis"] = "healthy"
    except Exception as e:
        health_status["redis"] = "unhealthy"
        health_status["redis_error"] = str(e)
        health_status["status"] = "degraded"

    # Check file storage
    try:
        minio = get_minio_client()
        minio.bucket_exists("nativecolab")
        health_status["storage"] = "healthy"
    except Exception as e:
        health_status["storage"] = "unhealthy"
        health_status["storage_error"] = str(e)
        health_status["status"] = "degraded"

    # Return 503 if unhealthy (load balancer will remove from pool)
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)

    return health_status

@router.get("/health/live")
async def liveness_probe():
    """Simple liveness check (is app running?)"""
    return {"status": "alive"}

@router.get("/health/ready")
async def readiness_probe():
    """Readiness check (can app handle traffic?)"""
    # Check if dependencies are ready
    db_ready = await check_database_ready()
    redis_ready = await check_redis_ready()

    if not (db_ready and redis_ready):
        raise HTTPException(status_code=503, detail="Not ready")

    return {"status": "ready"}
```

## Session Management

### Sticky Sessions vs Stateless

**Stateless Architecture (Recommended):**
```python
# Store session in Redis, not memory
SESSION_CONFIG = {
    "type": "redis",
    "redis_url": "redis://redis-sentinel:26379",
    "key_prefix": "session:",
    "ttl": 3600
}

# All app servers can handle any request
@app.get("/api/v1/projects")
async def get_projects(
    session_id: str = Depends(get_session_id)
):
    # Fetch session from Redis
    session = await redis.get(f"session:{session_id}")
    # No server-side state required
    return projects
```

## Zero-Downtime Deployments

### Rolling Updates

**Deployment Strategy:**
```bash
#!/bin/bash
# Rolling deployment script

SERVERS=("10.0.1.10" "10.0.1.11" "10.0.1.12")

for SERVER in "${SERVERS[@]}"; do
    echo "Deploying to $SERVER"

    # Remove from load balancer
    curl -X POST "http://lb:8404/admin/disable/$SERVER"

    # Wait for connections to drain
    sleep 30

    # Deploy new version
    ssh $SERVER "docker pull nativecolab/backend:latest && docker-compose up -d"

    # Wait for health check
    sleep 20

    # Add back to load balancer
    curl -X POST "http://lb:8404/admin/enable/$SERVER"

    echo "Deployment to $SERVER complete"
done
```

## Monitoring and Alerting

### High Availability Monitoring

**Key Metrics:**
```yaml
Uptime_Metrics:
  - http_requests_total
  - http_request_duration_seconds
  - http_request_errors_total
  - active_connections
  - database_connections_active
  - redis_connections_active
  - health_check_status

Alerts:
  - name: ServiceDown
    expr: up == 0
    for: 1m
    severity: critical
    action: page_oncall

  - name: HighErrorRate
    expr: rate(http_request_errors_total[5m]) > 0.05
    for: 5m
    severity: high
    action: alert_team

  - name: DatabaseReplicationLag
    expr: pg_replication_lag_seconds > 30
    for: 5m
    severity: high
    action: alert_dba
```

## Best Practices

1. **Redundancy**: At least 2-3 instances of each component
2. **Health Checks**: Comprehensive health checks on all services
3. **Graceful Shutdown**: Drain connections before shutdown
4. **Monitoring**: Real-time monitoring of all components
5. **Automation**: Automate failover and recovery
6. **Testing**: Regular HA testing and drills
7. **Documentation**: Maintain runbooks for failures
8. **Capacity Planning**: Adequate resources for failover

## Testing High Availability

### Chaos Engineering

**Test Scenarios:**
```bash
# Test application server failure
docker stop nativecolab-app-1

# Test database failover
patronictl failover

# Test Redis failover
redis-cli -p 26379 sentinel failover mymaster

# Test load balancer failure
systemctl stop haproxy

# Test network partition
iptables -A INPUT -s 10.0.1.11 -j DROP
```

## Next Steps

- [Disaster Recovery →](./disaster-recovery)
- [Monitoring →](./monitoring)
- [Scaling →](./scaling)
- [Enterprise Overview →](./overview)
