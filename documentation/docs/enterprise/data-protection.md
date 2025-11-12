# Data Protection & Encryption

Native Colab Enterprise implements comprehensive data protection measures including encryption at rest and in transit, data loss prevention, and secure data handling practices.

## Encryption

### Encryption at Rest

**Database Encryption:**
- **PostgreSQL**: Transparent Data Encryption (TDE) or full disk encryption
- **Algorithm**: AES-256-GCM
- **Key Management**: Separate encryption keys from data
- **Scope**: All database files, logs, backups

**Configuration:**
```bash
# PostgreSQL encryption setup
# Enable data-at-rest encryption
ssl = on
ssl_cert_file = '/path/to/server.crt'
ssl_key_file = '/path/to/server.key'
ssl_ca_file = '/path/to/ca.crt'

# Full disk encryption (OS level)
# LUKS encryption for Linux
cryptsetup luksFormat /dev/sdb
cryptsetup open /dev/sdb pgdata
```

**File Storage Encryption:**
- **MinIO/S3**: Server-side encryption (SSE-C)
- **Algorithm**: AES-256
- **Key Rotation**: Automatic quarterly rotation
- **Versioning**: Encrypted object versioning enabled

**MinIO Encryption:**
```yaml
# docker-compose.yml
minio:
  environment:
    - MINIO_SSE_MASTER_KEY=${ENCRYPTION_KEY}
    - MINIO_SSE_AUTO_ENCRYPTION=on
  volumes:
    - ./minio-data:/data  # Encrypted volume
```

### Encryption in Transit

**TLS/SSL Everywhere:**
- **Minimum Version**: TLS 1.3 (fallback to TLS 1.2)
- **Cipher Suites**: Strong ciphers only
- **Certificate**: Valid SSL certificate required
- **HSTS**: Strict Transport Security enabled

**Nginx TLS Configuration:**
```nginx
# SSL/TLS Configuration
ssl_protocols TLSv1.3 TLSv1.2;
ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384';
ssl_prefer_server_ciphers on;

# SSL Session
ssl_session_cache shared:SSL:10m;
ssl_session_timeout 10m;
ssl_session_tickets off;

# Certificate
ssl_certificate /etc/ssl/certs/nativecolab.crt;
ssl_certificate_key /etc/ssl/private/nativecolab.key;

# HSTS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;

# OCSP Stapling
ssl_stapling on;
ssl_stapling_verify on;
ssl_trusted_certificate /etc/ssl/certs/ca-chain.crt;
```

**WebSocket Encryption:**
- Socket.io over TLS (wss://)
- Certificate pinning
- Encrypted message payloads

### End-to-End Encryption (E2EE)

**Private Channels (Coming Soon):**
- Client-side encryption for sensitive channels
- Only participants can decrypt messages
- Zero-knowledge architecture
- Forward secrecy with key rotation

**Implementation:**
```typescript
// Client-side encryption
import { encrypt, decrypt } from '@/lib/crypto';

// Encrypt before sending
const encryptedMessage = await encrypt(
  plaintext,
  channelPublicKey
);

// Decrypt after receiving
const decryptedMessage = await decrypt(
  ciphertext,
  userPrivateKey
);
```

## Key Management

### Encryption Keys

**Key Hierarchy:**
```
Master Key (HSM or KMS)
└── Data Encryption Keys (DEK)
    ├── Database Encryption Key
    ├── File Storage Key
    ├── Backup Encryption Key
    └── Application Secret Keys
```

**Key Storage:**
- **Production**: Hardware Security Module (HSM) or Cloud KMS
- **Development**: Environment variables (never committed)
- **Backup Keys**: Offline storage in secure location

### Key Rotation

**Automatic Rotation:**
```python
# Key rotation schedule
{
  "master_key": "manual",  # Once per year
  "database_key": "quarterly",
  "storage_key": "quarterly",
  "jwt_secret": "monthly",
  "session_key": "weekly"
}
```

**Rotation Process:**
```python
# Automated key rotation
async def rotate_encryption_key():
    # Generate new key
    new_key = generate_encryption_key()

    # Re-encrypt data with new key
    await re_encrypt_database(new_key)
    await re_encrypt_files(new_key)

    # Update key reference
    await update_key_store(new_key)

    # Archive old key (for backup decryption)
    await archive_old_key(old_key, retention_days=90)

    # Audit log
    await log_key_rotation()
```

### Secrets Management

**HashiCorp Vault Integration:**
```python
# Fetch secrets from Vault
import hvac

client = hvac.Client(url='https://vault.company.com')
client.auth.approle.login(role_id, secret_id)

# Read database credentials
db_creds = client.secrets.kv.v2.read_secret_version(
    path='database/postgres'
)

DATABASE_URL = db_creds['data']['data']['connection_string']
```

**Environment-Specific Secrets:**
```bash
# .env.production (never committed)
DATABASE_URL=postgresql://...
JWT_SECRET_KEY=...
ENCRYPTION_KEY=...
AWS_SECRET_ACCESS_KEY=...

# Use secret management service
vault kv get -field=jwt_secret secret/nativecolab/production
```

## Data Loss Prevention (DLP)

### Content Scanning

**Sensitive Data Detection:**
- Credit card numbers (PAN)
- Social Security Numbers (SSN)
- API keys and secrets
- Personal Identifiable Information (PII)
- Health information (PHI)
- Financial data

**Scanning Implementation:**
```python
from app.core.dlp import scan_content

# Scan message before sending
async def send_message(content: str):
    # DLP scan
    scan_result = await scan_content(content)

    if scan_result.has_sensitive_data:
        # Block or redact
        if scan_result.severity == "high":
            raise DLPViolation("Message contains sensitive data")
        else:
            # Redact and warn
            content = scan_result.redacted_content
            await notify_admin(scan_result)

    # Send message
    return await create_message(content)
```

**Regex Patterns:**
```python
DLP_PATTERNS = {
    "credit_card": r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b",
    "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
    "api_key": r"(api[_-]?key|apikey)[\s:=]+['\"]?([a-zA-Z0-9]{32,})",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "private_key": r"-----BEGIN (RSA|DSA|EC|OPENSSH) PRIVATE KEY-----",
    "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
}
```

### Data Classification

**Automatic Classification:**
```python
# Classify data based on content
class DataClassifier:
    def classify(self, content: str) -> Classification:
        score = 0

        # Check for PII
        if contains_pii(content):
            score += 30

        # Check for financial data
        if contains_financial(content):
            score += 40

        # Check for health information
        if contains_phi(content):
            score += 50

        # Determine classification
        if score >= 70:
            return Classification.RESTRICTED
        elif score >= 40:
            return Classification.CONFIDENTIAL
        elif score >= 20:
            return Classification.INTERNAL
        else:
            return Classification.PUBLIC
```

### Access Controls

**Classification-Based Access:**
```python
# Enforce access based on classification
@require_clearance_level("confidential")
async def view_document(document_id: int):
    document = await get_document(document_id)

    # Check user clearance
    if document.classification > current_user.clearance_level:
        raise InsufficientClearance()

    # Log access for audit
    await log_data_access(
        user_id=current_user.id,
        resource_id=document_id,
        classification=document.classification
    )

    return document
```

## Data Retention & Deletion

### Retention Policies

**Configurable Retention:**
```python
RETENTION_POLICIES = {
    "messages": {
        "public_channels": "unlimited",
        "private_channels": "7_years",
        "direct_messages": "3_years"
    },
    "documents": {
        "active": "unlimited",
        "archived": "5_years",
        "deleted": "30_days"  # Soft delete period
    },
    "audit_logs": "7_years",  # Compliance requirement
    "time_tracking": "7_years",  # Financial records
    "backups": "90_days"
}
```

**Automated Cleanup:**
```python
# Celery task for data cleanup
@celery.task
async def cleanup_old_data():
    # Delete expired messages
    await delete_messages_older_than(days=365 * 7)

    # Delete expired documents
    await delete_archived_documents_older_than(days=365 * 5)

    # Delete expired backups
    await delete_backups_older_than(days=90)

    # Anonymize old audit logs (retain structure, remove PII)
    await anonymize_audit_logs_older_than(days=365 * 7)
```

### Secure Deletion

**Data Erasure:**
```python
async def secure_delete(file_path: str):
    # Overwrite file multiple times
    with open(file_path, 'wb') as f:
        size = os.path.getsize(file_path)

        # DoD 5220.22-M standard (3 passes)
        f.write(os.urandom(size))  # Pass 1: Random
        f.seek(0)
        f.write(b'\x00' * size)    # Pass 2: Zeros
        f.seek(0)
        f.write(os.urandom(size))  # Pass 3: Random

    # Delete file
    os.remove(file_path)

    # Delete database records
    await db.execute(
        "DELETE FROM files WHERE path = :path",
        {"path": file_path}
    )
```

### GDPR Right to Erasure

**User Data Deletion:**
```python
# GDPR Article 17: Right to erasure
POST /api/v1/gdpr/data-deletion
{
  "reason": "user_request",
  "delete_all": true,
  "anonymize_contributions": true  # Keep contributions but anonymize
}

# 30-day grace period
{
  "status": "scheduled",
  "deletion_date": "2025-02-14T00:00:00Z",
  "cancellable_until": "2025-02-13T23:59:59Z"
}
```

## Backup & Recovery

### Encrypted Backups

**Backup Strategy:**
- **Frequency**: Daily incremental, weekly full
- **Encryption**: AES-256 encryption
- **Location**: Off-site storage (separate region)
- **Retention**: 90 days
- **Testing**: Monthly restore tests

**Backup Configuration:**
```bash
#!/bin/bash
# Automated encrypted backup

# Dump database
pg_dump -U nativecolab nativecolab > /tmp/backup.sql

# Encrypt backup
openssl enc -aes-256-cbc -salt -pbkdf2 \
  -in /tmp/backup.sql \
  -out /backups/backup_$(date +%Y%m%d).sql.enc \
  -pass file:/etc/backup.key

# Upload to S3 with encryption
aws s3 cp /backups/backup_$(date +%Y%m%d).sql.enc \
  s3://backups/nativecolab/ \
  --sse AES256

# Clean up
rm /tmp/backup.sql
```

### Disaster Recovery

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 24 hours

**Recovery Process:**
```bash
# 1. Download encrypted backup
aws s3 cp s3://backups/nativecolab/backup_20250115.sql.enc /tmp/

# 2. Decrypt backup
openssl enc -aes-256-cbc -d -pbkdf2 \
  -in /tmp/backup_20250115.sql.enc \
  -out /tmp/backup.sql \
  -pass file:/etc/backup.key

# 3. Restore database
psql -U nativecolab nativecolab < /tmp/backup.sql

# 4. Verify integrity
psql -U nativecolab nativecolab -c "SELECT COUNT(*) FROM users;"

# 5. Restore files
aws s3 sync s3://nativecolab-files/ /data/files/
```

## Data Masking & Anonymization

### PII Masking

**Display Masking:**
```python
def mask_email(email: str) -> str:
    """Mask email for display: j***@e*****.com"""
    local, domain = email.split('@')
    return f"{local[0]}***@{domain[0]}*****.{domain.split('.')[-1]}"

def mask_phone(phone: str) -> str:
    """Mask phone: (555) ***-1234"""
    return f"({phone[:3]}) ***-{phone[-4:]}"

def mask_credit_card(cc: str) -> str:
    """Mask credit card: **** **** **** 1234"""
    return f"**** **** **** {cc[-4:]}"
```

**Database Anonymization:**
```python
# Anonymize data for testing/development
async def anonymize_user_data(user_id: int):
    await db.execute("""
        UPDATE users
        SET
            email = CONCAT('user_', id, '@example.com'),
            full_name = CONCAT('User ', id),
            phone = NULL,
            address = NULL,
            avatar_url = NULL
        WHERE id = :user_id
    """, {"user_id": user_id})
```

### Test Data Generation

**Synthetic Data:**
```python
from faker import Faker

fake = Faker()

# Generate fake users for testing
def generate_test_user():
    return {
        "email": fake.email(),
        "full_name": fake.name(),
        "phone": fake.phone_number(),
        "company": fake.company(),
        # Never use real PII in test environments
    }
```

## Monitoring & Alerting

### Security Events

**Data Access Monitoring:**
```python
# Log all data access
@log_data_access
async def get_sensitive_document(document_id: int):
    document = await fetch_document(document_id)

    # Create data access log
    await DataAccessLog.create(
        user_id=current_user.id,
        resource_type="document",
        resource_id=document_id,
        action="read",
        data_classification=document.classification,
        ip_address=request.client.host,
        justification=request.headers.get("X-Access-Reason")
    )

    return document
```

**Anomaly Detection:**
```python
# Detect unusual data access patterns
async def detect_data_access_anomaly():
    # Unusual volume
    if await get_user_access_count(user_id, hours=1) > 1000:
        await alert_admin("Unusual access volume", user_id)

    # Off-hours access to sensitive data
    if is_off_hours() and classification == "restricted":
        await alert_admin("Off-hours sensitive data access", user_id)

    # Bulk download
    if download_size > 1_000_000_000:  # 1GB
        await alert_admin("Large data download", user_id)
```

## Compliance

### Data Protection Regulations

**GDPR (EU):**
- Data minimization
- Purpose limitation
- Storage limitation
- Encryption and pseudonymization
- Data breach notification (72 hours)

**CCPA (California):**
- Right to know
- Right to delete
- Right to opt-out
- Non-discrimination

**HIPAA (Healthcare):**
- Administrative safeguards
- Physical safeguards
- Technical safeguards
- Breach notification

### Data Processing Agreements

**DPA Requirements:**
- Purpose and duration of processing
- Types of personal data
- Categories of data subjects
- Obligations and rights
- Sub-processors
- International transfers
- Data breach procedures

## Best Practices

1. **Encrypt Everything**: At rest and in transit
2. **Key Management**: Use HSM or KMS for production
3. **Regular Rotation**: Rotate encryption keys quarterly
4. **Access Logging**: Log all access to sensitive data
5. **DLP Scanning**: Scan content for sensitive information
6. **Data Classification**: Classify and label all data
7. **Secure Deletion**: Use secure deletion methods
8. **Backup Testing**: Test backups monthly
9. **Incident Response**: Have a data breach response plan
10. **Regular Audits**: Conduct security audits quarterly

## Next Steps

- [Audit Logging →](./audit-logging)
- [Security Overview →](./security)
- [Compliance →](./compliance)
- [GDPR Features →](./gdpr)
