# Disaster Recovery

Native Colab Enterprise includes comprehensive disaster recovery capabilities with automated backups, tested recovery procedures, and multi-region support.

## Recovery Objectives

**RTO (Recovery Time Objective):** 4 hours
**RPO (Recovery Point Objective):** 1 hour (incremental backups)

## Backup Strategy

### Automated Backups

```bash
#!/bin/bash
# /scripts/backup.sh

# Database backup
pg_dump -U nativecolab nativecolab | \
  gzip | \
  openssl enc -aes-256-cbc -salt -pbkdf2 -pass file:/etc/backup.key | \
  aws s3 cp - s3://backups/db/$(date +%Y%m%d-%H%M%S).sql.gz.enc

# Files backup
tar czf - /data/files | \
  openssl enc -aes-256-cbc -salt -pbkdf2 -pass file:/etc/backup.key | \
  aws s3 cp - s3://backups/files/$(date +%Y%m%d-%H%M%S).tar.gz.enc

# Redis backup
redis-cli --rdb /tmp/dump.rdb
aws s3 cp /tmp/dump.rdb s3://backups/redis/$(date +%Y%m%d-%H%M%S).rdb

# Retention: Keep 90 days
aws s3 ls s3://backups/ --recursive | \
  awk '{if ($1 < "'$(date -d '90 days ago' +%Y-%m-%d)'") print $4}' | \
  xargs -I {} aws s3 rm s3://backups/{}
```

**Schedule:**
- Every hour: Incremental backup
- Every day: Full backup
- Every week: Verified backup test
- Every month: Off-site backup

## Recovery Procedures

### Database Recovery

```bash
#!/bin/bash
# Restore database from backup

# Download latest backup
aws s3 cp s3://backups/db/latest.sql.gz.enc /tmp/backup.sql.gz.enc

# Decrypt
openssl enc -aes-256-cbc -d -pbkdf2 \
  -in /tmp/backup.sql.gz.enc \
  -out /tmp/backup.sql.gz \
  -pass file:/etc/backup.key

# Decompress and restore
gunzip /tmp/backup.sql.gz
psql -U nativecolab nativecolab < /tmp/backup.sql

# Verify
psql -U nativecolab nativecolab -c "SELECT COUNT(*) FROM users;"
```

### Complete System Recovery

```bash
#!/bin/bash
# Full disaster recovery procedure

echo "Starting disaster recovery..."

# 1. Deploy infrastructure
terraform apply -var-file=dr-site.tfvars

# 2. Restore database
./scripts/restore-database.sh

# 3. Restore files
aws s3 sync s3://backups/files/ /data/files/

# 4. Restore Redis
redis-cli --rdb /tmp/dump.rdb
redis-cli RESTORE ...

# 5. Start services
docker-compose -f docker-compose.prod.yml up -d

# 6. Verify health
curl -f http://localhost:8000/health || exit 1

# 7. Update DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123 \
  --change-batch file://dns-update.json

echo "Disaster recovery complete"
```

## Multi-Region Setup

### Active-Passive Configuration

```yaml
Primary_Region: us-east-1
  - All production traffic
  - Database primary
  - Real-time backups to DR site

DR_Region: eu-west-1
  - Standby mode
  - Database replica (async replication)
  - Can be activated in 4 hours
```

### Failover Process

```bash
# 1. Detect primary region failure
if ! curl -f https://app.nativecolab.com/health; then
    echo "Primary region down, initiating failover"

    # 2. Promote DR database to primary
    patronictl failover --candidate dr-db-1

    # 3. Update DNS to point to DR region
    aws route53 change-resource-record-sets \
      --hosted-zone-id Z123 \
      --change-batch file://failover-dns.json

    # 4. Notify team
    curl -X POST https://hooks.slack.com/services/xxx \
      -d '{"text":"Failover to DR region initiated"}'

    # 5. Monitor recovery
    watch -n 5 "curl -f https://app.nativecolab.com/health"
fi
```

## Testing and Validation

### Monthly DR Test

```bash
#!/bin/bash
# Monthly DR test (non-disruptive)

# 1. Take snapshot of production
aws rds create-db-snapshot --db-instance-identifier prod-db --db-snapshot-identifier dr-test-$(date +%Y%m%d)

# 2. Restore in test environment
aws rds restore-db-instance-from-db-snapshot \
  --db-instance-identifier dr-test \
  --db-snapshot-identifier dr-test-$(date +%Y%m%d)

# 3. Deploy application
docker-compose -f docker-compose.dr-test.yml up -d

# 4. Run smoke tests
pytest tests/smoke/ --dr-test

# 5. Document results
echo "DR Test $(date): SUCCESS" >> /var/log/dr-tests.log

# 6. Cleanup
docker-compose -f docker-compose.dr-test.yml down
aws rds delete-db-instance --db-instance-identifier dr-test --skip-final-snapshot
```

## Business Continuity

### Communication Plan

**Incident Communication:**
1. Internal: Slack #incidents channel
2. Customers: Status page (status.nativecolab.com)
3. Stakeholders: Email updates every 2 hours
4. Post-Mortem: Within 48 hours

### Roles and Responsibilities

```yaml
Incident_Commander:
  - Overall coordination
  - Communication to stakeholders
  - Decision making

Technical_Lead:
  - Technical recovery execution
  - Resource coordination
  - Progress updates

Database_Administrator:
  - Database recovery
  - Data verification
  - Replication setup

Operations_Lead:
  - Infrastructure provisioning
  - Network configuration
  - Service health monitoring

Security_Officer:
  - Security verification
  - Access control
  - Incident analysis
```

## Post-Incident Review

### Incident Report Template

```markdown
# Incident Report: [INCIDENT-ID]

## Summary
- **Date**: 2025-01-15
- **Duration**: 2 hours 15 minutes
- **Impact**: 500 users affected
- **RTO Achieved**: 1 hour 45 minutes (target: 4 hours)
- **RPO Achieved**: 30 minutes (target: 1 hour)

## Timeline
- 10:00 - Primary database failure detected
- 10:05 - Incident declared, team paged
- 10:15 - Failover to replica initiated
- 10:30 - Database recovered
- 11:00 - Application services restored
- 11:45 - Full service restored

## Root Cause
Database disk failure due to hardware issue

## Resolution
- Failed over to database replica
- Restored from latest backup
- Replaced failed hardware

## Action Items
1. [P0] Implement automated failover (Owner: DBA, Due: 2025-01-22)
2. [P1] Increase backup frequency (Owner: Ops, Due: 2025-01-29)
3. [P2] Improve monitoring alerts (Owner: SRE, Due: 2025-02-05)

## Lessons Learned
- Manual failover took longer than expected
- Backup verification process worked well
- Communication to customers could be faster
```

## Best Practices

1. **Regular Testing**: Monthly DR tests
2. **Documentation**: Keep runbooks updated
3. **Automation**: Automate recovery procedures
4. **Monitoring**: Real-time health monitoring
5. **Communication**: Clear incident communication plan
6. **Training**: Regular DR training for team
7. **Verification**: Verify backups regularly
8. **Off-Site**: Store backups in different region

## Next Steps

- [High Availability →](./high-availability)
- [Monitoring →](./monitoring)
- [Enterprise Overview →](./overview)
