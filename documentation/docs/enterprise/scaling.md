# Enterprise Scaling

Native Colab Enterprise is designed to scale horizontally and vertically to support organizations from 100 to 100,000+ users.

## Horizontal Scaling

### Application Servers

**Add More Instances:**
```yaml
# docker-compose.prod.yml
services:
  app:
    image: nativecolab/backend:latest
    deploy:
      replicas: 10  # Scale from 3 to 10
```

### Auto-Scaling with Kubernetes

```yaml
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
  maxReplicas: 50
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

## Database Scaling

### Read Replicas

```sql
-- Create read replica
CREATE SUBSCRIPTION replica_subscription
CONNECTION 'host=primary port=5432 dbname=nativecolab'
PUBLICATION replica_publication;

-- Route read queries to replicas
SELECT * FROM projects WHERE workspace_id = 100;  -- Read from replica
INSERT INTO projects (...) VALUES (...);  -- Write to primary
```

### Connection Pooling

```python
# PgBouncer configuration
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_async_engine(
    DATABASE_URL,
    pool_size=50,  # Increase from 20
    max_overflow=100,  # Increase from 10
    pool_pre_ping=True,
    poolclass=QueuePool
)
```

### Partitioning

```sql
-- Partition large tables by workspace
CREATE TABLE messages (
    id BIGSERIAL,
    workspace_id INTEGER NOT NULL,
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
) PARTITION BY HASH (workspace_id);

CREATE TABLE messages_0 PARTITION OF messages
    FOR VALUES WITH (MODULUS 10, REMAINDER 0);

CREATE TABLE messages_1 PARTITION OF messages
    FOR VALUES WITH (MODULUS 10, REMAINDER 1);
-- ... create 10 partitions
```

## Redis Scaling

### Redis Cluster

```bash
# 6-node cluster (3 masters, 3 replicas)
redis-cli --cluster create \
  10.0.1.30:6379 \
  10.0.1.31:6379 \
  10.0.1.32:6379 \
  10.0.1.33:6379 \
  10.0.1.34:6379 \
  10.0.1.35:6379 \
  --cluster-replicas 1
```

## File Storage Scaling

### Distributed MinIO

```yaml
# docker-compose.minio-distributed.yml
version: '3.8'
services:
  minio1:
    image: minio/minio
    command: server http://minio{1...4}/data{1...2}
    environment:
      MINIO_ROOT_USER: admin
      MINIO_ROOT_PASSWORD: password

  minio2:
    image: minio/minio
    command: server http://minio{1...4}/data{1...2}

  minio3:
    image: minio/minio
    command: server http://minio{1...4}/data{1...2}

  minio4:
    image: minio/minio
    command: server http://minio{1...4}/data{1...2}
```

## Caching Strategy

### Multi-Layer Caching

```python
# Layer 1: In-memory cache (fast)
from cachetools import TTLCache
memory_cache = TTLCache(maxsize=1000, ttl=60)

# Layer 2: Redis (shared)
import redis
redis_client = redis.Redis(host='redis', port=6379)

# Layer 3: Database (source of truth)
async def get_project(project_id: int):
    # Check memory cache
    if project_id in memory_cache:
        return memory_cache[project_id]

    # Check Redis
    cached = await redis_client.get(f"project:{project_id}")
    if cached:
        project = json.loads(cached)
        memory_cache[project_id] = project
        return project

    # Query database
    project = await db.query(Project).filter(Project.id == project_id).first()

    # Update caches
    await redis_client.setex(f"project:{project_id}", 3600, json.dumps(project))
    memory_cache[project_id] = project

    return project
```

## Content Delivery Network (CDN)

### CloudFlare Integration

```nginx
# nginx.conf
location /static/ {
    alias /app/static/;
    expires 1y;
    add_header Cache-Control "public, immutable";

    # CDN will cache based on these headers
}

location /api/ {
    # Do not cache API responses
    add_header Cache-Control "no-cache, no-store, must-revalidate";
}
```

## Performance Optimization

### Database Optimization

```sql
-- Add indexes for common queries
CREATE INDEX CONCURRENTLY idx_messages_channel_created ON messages(channel_id, created_at DESC);
CREATE INDEX CONCURRENTLY idx_tasks_project_status ON tasks(project_id, status);

-- Analyze and vacuum
ANALYZE;
VACUUM ANALYZE;

-- Materialized views for expensive queries
CREATE MATERIALIZED VIEW project_statistics AS
SELECT
    project_id,
    COUNT(*) as total_tasks,
    COUNT(*) FILTER (WHERE status = 'completed') as completed_tasks,
    AVG(completion_time) as avg_completion_time
FROM tasks
GROUP BY project_id;

CREATE UNIQUE INDEX ON project_statistics (project_id);

-- Refresh periodically
REFRESH MATERIALIZED VIEW CONCURRENTLY project_statistics;
```

### Query Optimization

```python
# Bad: N+1 query problem
projects = await db.query(Project).all()
for project in projects:
    tasks = await db.query(Task).filter(Task.project_id == project.id).all()

# Good: Eager loading
from sqlalchemy.orm import selectinload

projects = await db.query(Project).options(
    selectinload(Project.tasks)
).all()
```

## Capacity Planning

### Sizing Guidelines

| Users | App Servers | CPU/Server | RAM/Server | Database | Redis |
|-------|-------------|------------|------------|----------|-------|
| 100 | 2 | 2 cores | 4 GB | 1 (50 GB) | 1 (2 GB) |
| 1,000 | 3 | 4 cores | 8 GB | 1 (200 GB) + 1 replica | 2 (4 GB each) |
| 10,000 | 10 | 8 cores | 16 GB | 1 (1 TB) + 2 replicas | Cluster (6 nodes, 8 GB each) |
| 100,000 | 50 | 16 cores | 32 GB | Partitioned (10 TB) + 3 replicas | Cluster (12 nodes, 16 GB each) |

## Best Practices

1. **Stateless Applications**: No server-side session state
2. **Database Connection Pooling**: Reuse connections
3. **Caching**: Cache frequently accessed data
4. **Asynchronous Processing**: Use Celery for background tasks
5. **CDN**: Offload static assets
6. **Monitoring**: Track performance metrics
7. **Load Testing**: Regular load tests
8. **Gradual Rollouts**: Blue-green or canary deployments

## Next Steps

- [High Availability →](./high-availability)
- [Monitoring →](./monitoring)
- [Enterprise Overview →](./overview)
