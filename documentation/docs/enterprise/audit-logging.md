# Enterprise Audit Logging

Native Colab Enterprise provides comprehensive audit logging for compliance, security monitoring, and forensic analysis. All user actions, system events, and data modifications are logged immutably.

## Overview

### What is Audited?

**User Actions:**
- Authentication events (login, logout, MFA)
- Resource creation, modification, deletion
- Permission changes
- Data access and exports
- Configuration changes
- Administrative actions

**System Events:**
- Security events
- Failed access attempts
- Rate limit violations
- API errors
- System configuration changes

**Data Modifications:**
- Before/after values for all changes
- Who made the change
- When it was made
- Why it was made (if provided)
- From where (IP address, device)

## Audit Log Types

### 1. Universal Audit Log

**General Activity Tracking:**
```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    action = Column(String(100), nullable=False, index=True)  # create, read, update, delete
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=True, index=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_method = Column(String(10), nullable=True)  # GET, POST, PUT, DELETE
    request_path = Column(String(500), nullable=True)
    request_id = Column(String(100), unique=True, index=True)
    old_values = Column(JSON, nullable=True)  # Before change
    new_values = Column(JSON, nullable=True)  # After change
    success = Column(Boolean, default=True, nullable=False)
    failure_reason = Column(Text, nullable=True)
    risk_level = Column(String(20), default="low")  # low, medium, high, critical
    duration_ms = Column(Integer, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
```

**Example Log Entry:**
```json
{
  "id": 12345,
  "workspace_id": 100,
  "user_id": 42,
  "action": "update",
  "resource_type": "project",
  "resource_id": "proj_abc123",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  "request_method": "PUT",
  "request_path": "/api/v1/projects/proj_abc123",
  "request_id": "req_xyz789",
  "old_values": {
    "name": "Q4 Marketing Campaign",
    "status": "in_progress"
  },
  "new_values": {
    "name": "Q4 Marketing Campaign",
    "status": "completed"
  },
  "success": true,
  "risk_level": "low",
  "duration_ms": 45,
  "metadata": {
    "client_version": "2.1.0",
    "timestamp": "2025-01-15T10:30:00Z"
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

### 2. Security Event Log

**Security-Specific Tracking:**
```python
class SecurityEvent(Base):
    __tablename__ = "security_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    description = Column(Text, nullable=False)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    action_taken = Column(String(100), nullable=True)  # logged, blocked, alerted
    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
```

**Security Event Types:**
- `failed_login`: Failed login attempts
- `brute_force_attempt`: Multiple failed logins
- `unauthorized_access`: 403 Forbidden access
- `privilege_escalation`: Attempted privilege escalation
- `suspicious_activity`: Anomalous behavior detected
- `data_exfiltration`: Large data download
- `account_locked`: Account locked due to security
- `mfa_bypass_attempt`: MFA bypass attempt
- `token_theft_suspected`: Token reuse from different IP

**Example Security Event:**
```json
{
  "event_type": "brute_force_attempt",
  "user_id": null,
  "workspace_id": null,
  "severity": "high",
  "description": "Multiple failed login attempts from IP 203.0.113.42",
  "ip_address": "203.0.113.42",
  "action_taken": "blocked",
  "resolved": false,
  "metadata": {
    "failed_attempts": 15,
    "time_window_minutes": 5,
    "usernames_tried": ["admin", "root", "user"]
  },
  "created_at": "2025-01-15T10:30:00Z"
}
```

### 3. Data Access Log

**Sensitive Data Access Tracking:**
```python
class DataAccessLog(Base):
    __tablename__ = "data_access_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    resource_type = Column(String(100), nullable=False, index=True)
    resource_id = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=False, index=True)  # read, download, export, print
    data_classification = Column(String(50), nullable=True)  # public, internal, confidential, restricted
    ip_address = Column(String(45), nullable=True)
    justification = Column(Text, nullable=True)  # Why was data accessed
    granted_by_policy = Column(String(100), nullable=True)  # Which policy granted access
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
```

**Use Cases:**
- HIPAA compliance (PHI access tracking)
- Financial data access (SOX compliance)
- PII access tracking (GDPR compliance)
- Export control compliance
- Forensic investigations

### 4. Compliance Log

**Regulatory Compliance Tracking:**
```python
class ComplianceLog(Base):
    __tablename__ = "compliance_logs"

    id = Column(Integer, primary_key=True, index=True)
    compliance_type = Column(String(50), nullable=False, index=True)  # gdpr, hipaa, sox, pci
    action_type = Column(String(100), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"), nullable=True, index=True)
    description = Column(Text, nullable=False)
    legal_basis = Column(String(100), nullable=True)  # consent, contract, legal_obligation
    data_subject_id = Column(String(255), nullable=True, index=True)
    processing_purpose = Column(Text, nullable=True)
    data_categories = Column(JSON, nullable=True)
    retention_period = Column(Integer, nullable=True)  # Days
    expiry_date = Column(DateTime, nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
```

**Compliance Actions:**
- `data_export_requested`: GDPR Article 15
- `data_deletion_requested`: GDPR Article 17
- `consent_granted`: GDPR Article 7
- `consent_withdrawn`: GDPR Article 7
- `data_breach_detected`: GDPR Article 33
- `data_transfer`: GDPR Article 44-50
- `dpia_completed`: Data Protection Impact Assessment

## Automatic Audit Logging

### Middleware Implementation

**Audit Logging Middleware:**
```python
class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """Automatically logs all API requests"""

    AUDIT_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Determine if this should be audited
        should_audit = (
            request.method in self.AUDIT_METHODS or
            response.status_code >= 400 or
            "/auth/" in str(request.url)
        )

        if should_audit:
            await self._create_audit_log(
                request=request,
                response=response,
                duration_ms=duration_ms,
                request_id=request_id
            )

        return response
```

**What Gets Logged:**
- All POST, PUT, PATCH, DELETE requests
- All authentication endpoints
- All failed requests (4xx, 5xx errors)
- High-risk operations (deletions, permission changes)

## Query Audit Logs

### API Endpoints

**List Audit Logs:**
```http
GET /api/v1/audit/logs
?workspace_id=100
&user_id=42
&action=delete
&resource_type=project
&start_date=2025-01-01
&end_date=2025-01-31
&page=1
&limit=50

Response:
{
  "data": [
    {
      "id": 12345,
      "action": "delete",
      "resource_type": "project",
      "user": {
        "id": 42,
        "email": "user@company.com",
        "full_name": "John Doe"
      },
      "created_at": "2025-01-15T10:30:00Z",
      ...
    }
  ],
  "meta": {
    "page": 1,
    "limit": 50,
    "total": 1250,
    "pages": 25
  }
}
```

**Get Single Audit Log:**
```http
GET /api/v1/audit/logs/{log_id}

Response:
{
  "id": 12345,
  "action": "update",
  "resource_type": "project",
  "old_values": {...},
  "new_values": {...},
  "user": {...},
  "metadata": {...}
}
```

**Export Audit Logs:**
```http
POST /api/v1/audit/export
{
  "format": "csv",  # csv, json, pdf
  "filters": {
    "start_date": "2025-01-01",
    "end_date": "2025-01-31",
    "workspace_id": 100
  }
}

Response:
{
  "export_id": "exp_abc123",
  "status": "processing",
  "estimated_completion": "2025-01-15T10:35:00Z"
}
```

### Search and Filtering

**Advanced Filters:**
```python
# Complex query example
filters = {
    "workspace_id": 100,
    "actions": ["update", "delete"],
    "resource_types": ["project", "task"],
    "user_ids": [42, 43, 44],
    "risk_levels": ["high", "critical"],
    "success": False,  # Only failed attempts
    "date_range": {
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-31T23:59:59Z"
    },
    "ip_addresses": ["192.168.1.0/24"],  # CIDR notation
    "search_text": "sensitive data"
}
```

**Full-Text Search:**
```sql
-- Search audit logs
SELECT * FROM audit_logs
WHERE
    to_tsvector('english', description || ' ' || resource_type)
    @@ to_tsquery('english', 'project & delete');
```

## Retention and Archival

### Retention Policy

**Default Retention:**
```python
AUDIT_RETENTION = {
    "audit_logs": "7_years",  # Regulatory requirement
    "security_events": "10_years",
    "data_access_logs": "7_years",
    "compliance_logs": "10_years",
    "archived_logs": "permanent"  # Compressed, cold storage
}
```

### Archival Process

**Automated Archival:**
```python
@celery.task
async def archive_old_audit_logs():
    # Archive logs older than 1 year to cold storage
    cutoff_date = datetime.utcnow() - timedelta(days=365)

    # Export to compressed JSON
    old_logs = await db.query(AuditLog).filter(
        AuditLog.created_at < cutoff_date
    ).all()

    # Compress and upload to S3 Glacier
    archive_file = compress_logs(old_logs)
    await upload_to_glacier(archive_file)

    # Delete from primary database
    await db.query(AuditLog).filter(
        AuditLog.created_at < cutoff_date
    ).delete()

    # Keep index for reference
    await db.execute("""
        INSERT INTO archived_audit_log_index (
            date_range, archive_location, record_count
        ) VALUES (:start, :end, :location, :count)
    """, {
        "start": cutoff_date,
        "end": datetime.utcnow(),
        "location": "s3://glacier/archive_20250115.json.gz",
        "count": len(old_logs)
    })
```

## Alerting and Monitoring

### Real-Time Alerts

**Security Event Alerts:**
```python
# Alert on critical security events
@audit_event_listener("security_event")
async def on_security_event(event: SecurityEvent):
    if event.severity in ["high", "critical"]:
        # Send alert to security team
        await send_alert(
            channel="security",
            severity=event.severity,
            message=f"Security Event: {event.event_type}",
            details=event.description,
            actions=[
                {"label": "Review", "url": f"/audit/events/{event.id}"},
                {"label": "Block IP", "action": "block_ip", "ip": event.ip_address}
            ]
        )

        # Log to SIEM
        await forward_to_siem(event)
```

**Anomaly Detection:**
```python
# Detect unusual patterns
@celery.task
async def detect_audit_anomalies():
    # Detect unusual activity volume
    user_counts = await get_user_activity_last_hour()
    for user_id, count in user_counts.items():
        avg = await get_user_average_hourly_activity(user_id)
        if count > avg * 5:  # 5x normal activity
            await create_security_event(
                event_type="suspicious_activity",
                user_id=user_id,
                severity="medium",
                description=f"Unusual activity: {count} actions (avg: {avg})"
            )

    # Detect geographic anomalies
    users_with_geo_jump = await detect_impossible_travel()
    for user_id, locations in users_with_geo_jump:
        await create_security_event(
            event_type="suspicious_activity",
            user_id=user_id,
            severity="high",
            description=f"Impossible travel: {locations}"
        )
```

## Compliance Reporting

### GDPR Reports

**Article 30 - Records of Processing:**
```http
GET /api/v1/compliance/gdpr/article-30

Response:
{
  "controller_name": "Company Name",
  "controller_contact": "dpo@company.com",
  "purposes": [
    {
      "purpose": "User collaboration",
      "legal_basis": "contract",
      "data_categories": ["name", "email", "work_data"],
      "data_subjects": ["employees", "contractors"],
      "recipients": ["internal_staff"],
      "retention_period": "duration_of_employment + 7 years",
      "security_measures": ["encryption", "access_control", "audit_logging"]
    }
  ],
  "transfers": [],
  "generated_at": "2025-01-15T10:30:00Z"
}
```

### SOC 2 Reports

**Access Control Report:**
```http
GET /api/v1/compliance/soc2/access-controls
?start_date=2025-01-01
&end_date=2025-01-31

Response:
{
  "report_period": "2025-01-01 to 2025-01-31",
  "total_access_attempts": 125000,
  "successful_accesses": 124500,
  "failed_accesses": 500,
  "failed_access_reasons": {
    "invalid_credentials": 450,
    "insufficient_permissions": 40,
    "account_locked": 10
  },
  "privileged_access_changes": 12,
  "mfa_adoption_rate": 98.5,
  "findings": []
}
```

## Best Practices

### For Administrators

1. **Regular Reviews**: Review audit logs weekly
2. **Alert Configuration**: Set up alerts for critical events
3. **Retention Compliance**: Ensure logs retained per regulations
4. **Access Control**: Restrict audit log access to security team
5. **Immutability**: Ensure logs cannot be modified or deleted
6. **Backup Logs**: Backup logs separately from application data
7. **SIEM Integration**: Forward logs to SIEM for analysis
8. **Incident Response**: Use logs for forensic analysis

### For Security Teams

1. **Anomaly Detection**: Monitor for unusual patterns
2. **Threat Hunting**: Proactively search for IOCs
3. **Correlation**: Correlate events across different log types
4. **Baseline**: Establish normal behavior baselines
5. **Response Plans**: Have playbooks for common security events
6. **Chain of Custody**: Maintain proper log chain of custody
7. **Legal Hold**: Preserve logs for litigation when required

## API Reference

### Audit Log Endpoints

```http
# List audit logs
GET /api/v1/audit/logs

# Get specific log
GET /api/v1/audit/logs/{log_id}

# Export logs
POST /api/v1/audit/export

# List security events
GET /api/v1/audit/security-events

# List data access logs
GET /api/v1/audit/data-access

# Compliance report
GET /api/v1/audit/compliance-report
```

## Database Indexes

**Performance Optimization:**
```sql
-- Indexes for fast queries
CREATE INDEX idx_audit_logs_workspace_id ON audit_logs(workspace_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at DESC);
CREATE INDEX idx_audit_logs_risk_level ON audit_logs(risk_level);

-- Composite index for common queries
CREATE INDEX idx_audit_logs_workspace_date ON audit_logs(workspace_id, created_at DESC);
CREATE INDEX idx_audit_logs_user_date ON audit_logs(user_id, created_at DESC);

-- Partial index for failures
CREATE INDEX idx_audit_logs_failures ON audit_logs(created_at DESC)
WHERE success = false;
```

## Next Steps

- [Security Overview →](./security)
- [Compliance →](./compliance)
- [Data Protection →](./data-protection)
- [GDPR Features →](./gdpr)
