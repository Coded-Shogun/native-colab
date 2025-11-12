# Enterprise Authentication

Native Colab Enterprise provides advanced authentication mechanisms designed for security-conscious organizations.

## Authentication Methods

### JWT Token-Based Authentication

**Features:**
- Access tokens (15-minute expiry)
- Refresh tokens (7-day expiry)
- Token rotation on refresh
- Secure token storage
- Token blacklisting for immediate revocation

**Token Structure:**
```json
{
  "sub": "user-uuid",
  "email": "user@company.com",
  "workspace_id": "workspace-uuid",
  "roles": ["admin", "manager"],
  "exp": 1705492800,
  "iat": 1705492000,
  "jti": "token-unique-id"
}
```

### Multi-Factor Authentication (MFA)

**Supported Methods:**
- **TOTP (Time-based One-Time Password)**: Google Authenticator, Authy, Microsoft Authenticator
- **SMS**: Text message verification codes
- **Email**: Email-based verification codes
- **Hardware Keys**: FIDO2/WebAuthn security keys (YubiKey, etc.)
- **Backup Codes**: Single-use recovery codes

**MFA Configuration:**
```python
# Enable MFA for user
POST /api/v1/auth/mfa/enable
{
  "method": "totp",
  "device_name": "iPhone 15"
}

# Verify MFA setup
POST /api/v1/auth/mfa/verify
{
  "code": "123456"
}

# Generate backup codes
POST /api/v1/auth/mfa/backup-codes
# Returns 10 single-use backup codes
```

### Single Sign-On (SSO)

**Coming Soon - Supported Protocols:**
- **SAML 2.0**: Enterprise identity providers
- **OAuth 2.0**: Google, Microsoft, GitHub
- **OpenID Connect**: Modern identity providers
- **LDAP/Active Directory**: On-premise directory services

**SSO Benefits:**
- Centralized user management
- Reduced password fatigue
- Automated provisioning/deprovisioning
- Enhanced security through IdP policies

### Certificate-Based Authentication

**Client Certificate Authentication:**
- X.509 certificate validation
- Certificate pinning
- Certificate revocation list (CRL) checking
- OCSP (Online Certificate Status Protocol) support

**Use Cases:**
- API client authentication
- Machine-to-machine communication
- High-security environments
- Regulatory compliance requirements

## Password Security

### Password Requirements

**Enforced Policies:**
- Minimum 12 characters (enterprise default)
- Uppercase and lowercase letters
- Numbers and special characters
- No common passwords (checked against breach databases)
- No personal information (name, email parts)
- Password history (prevent reusing last 10 passwords)

**Configurable Settings:**
```python
{
  "min_length": 12,
  "require_uppercase": true,
  "require_lowercase": true,
  "require_numbers": true,
  "require_special": true,
  "max_age_days": 90,
  "history_count": 10,
  "lockout_attempts": 5,
  "lockout_duration_minutes": 30
}
```

### Password Hashing

**Algorithm:** bcrypt with salt
- Work factor: 12 rounds (configurable)
- Unique salt per password
- Computationally expensive (prevents brute force)
- Industry-standard algorithm

**Implementation:**
```python
from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)

# Hash password
hashed = pwd_context.hash(plain_password)

# Verify password
is_valid = pwd_context.verify(plain_password, hashed)
```

## Session Management

### Session Security

**Features:**
- Secure session cookies (HttpOnly, Secure, SameSite)
- Session timeout after inactivity
- Concurrent session management
- Device tracking and management
- Suspicious activity detection

**Session Configuration:**
```python
SESSION_CONFIG = {
    "timeout_minutes": 60,
    "absolute_timeout_hours": 24,
    "max_concurrent_sessions": 5,
    "remember_me_days": 30,
    "secure_cookie": True,
    "http_only": True,
    "same_site": "strict"
}
```

### Token Blacklisting

**Immediate Token Revocation:**
```python
# Blacklist single token
POST /api/v1/auth/tokens/{token_id}/revoke
{
  "reason": "Security incident"
}

# Blacklist all user tokens (force logout)
POST /api/v1/auth/users/{user_id}/revoke-all
{
  "reason": "Account compromise"
}

# Check if token is blacklisted
GET /api/v1/auth/tokens/{token_id}/status
```

**Use Cases:**
- User logout
- Account compromise
- Employee termination
- Security incidents
- Suspicious activity

## Brute Force Protection

### Rate Limiting

**Authentication Endpoints:**
- Login: 5 attempts per minute
- Password reset: 3 attempts per hour
- MFA verification: 10 attempts per 5 minutes
- Token refresh: 10 attempts per minute

**IP-Based Blocking:**
```python
# Automatic blocking after failed attempts
{
  "failed_login_threshold": 5,
  "block_duration_minutes": 30,
  "progressive_delay": true,
  "captcha_after_attempts": 3
}
```

### Account Lockout

**Lockout Policy:**
- Temporary lockout after 5 failed attempts
- 30-minute lockout duration (configurable)
- Progressive delays between attempts
- Email notification to user
- Admin unlock capability

**Monitoring:**
```python
# Security events logged:
- Failed login attempts
- Account lockouts
- Brute force attempts
- Suspicious patterns
- Geographic anomalies
```

## API Authentication

### API Keys

**Long-Lived API Keys:**
```python
# Create API key
POST /api/v1/auth/api-keys
{
  "name": "Production Integration",
  "scopes": ["read:projects", "write:tasks"],
  "expires_at": "2025-12-31T23:59:59Z"
}

# Use API key
GET /api/v1/projects
Authorization: Bearer api_key_abc123xyz789
```

**API Key Features:**
- Scoped permissions
- Expiration dates
- Usage tracking
- Rate limiting per key
- Easy revocation

### Service Accounts

**Machine-to-Machine Authentication:**
```python
# Create service account
POST /api/v1/auth/service-accounts
{
  "name": "CI/CD Pipeline",
  "permissions": ["deploy", "test"],
  "ip_whitelist": ["192.168.1.0/24"]
}
```

**Benefits:**
- No user credentials required
- Automated workflows
- IP whitelisting
- Detailed audit logging
- Granular permissions

## Security Monitoring

### Authentication Events

**Logged Events:**
- Successful logins
- Failed login attempts
- MFA challenges
- Token refreshes
- Password changes
- Account lockouts
- SSO authentications
- API key usage

**Alerting:**
```python
# Automatic alerts for:
- Multiple failed logins
- Login from new location
- Login from new device
- Impossible travel (too fast between locations)
- After-hours access (configurable)
- Privilege escalation attempts
```

### Compliance Reporting

**Authentication Reports:**
- Login frequency by user
- Failed authentication attempts
- MFA adoption rates
- Password age distribution
- Session duration statistics
- Geographic access patterns

**Export Formats:**
- CSV for analysis
- PDF for auditing
- JSON for integration
- Real-time dashboard

## Best Practices

### For Administrators

1. **Enforce MFA**: Require MFA for all administrative accounts
2. **Strong Passwords**: Set minimum password requirements
3. **Regular Audits**: Review authentication logs weekly
4. **Token Rotation**: Rotate API keys quarterly
5. **Monitor Alerts**: Respond to security alerts promptly
6. **SSO Integration**: Use SSO when available
7. **Session Timeouts**: Configure appropriate timeouts
8. **IP Whitelisting**: Restrict access by IP when possible

### For Users

1. **Use MFA**: Enable two-factor authentication
2. **Strong Passwords**: Use unique, complex passwords
3. **Password Manager**: Store passwords securely
4. **Review Sessions**: Check active sessions regularly
5. **Report Suspicious**: Report unusual login attempts
6. **Secure Devices**: Keep devices physically secure
7. **Public Networks**: Avoid authentication on public WiFi
8. **Logout**: Logout when using shared devices

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
JWT_ALGORITHM=HS256

# Password Policy
PASSWORD_MIN_LENGTH=12
PASSWORD_MAX_AGE_DAYS=90
PASSWORD_HISTORY_COUNT=10

# Session Configuration
SESSION_TIMEOUT_MINUTES=60
MAX_CONCURRENT_SESSIONS=5

# Rate Limiting
AUTH_RATE_LIMIT_PER_MINUTE=5
PASSWORD_RESET_RATE_LIMIT_PER_HOUR=3
```

### Database Schema

```sql
-- User authentication table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    mfa_enabled BOOLEAN DEFAULT FALSE,
    mfa_secret VARCHAR(255),
    mfa_backup_codes TEXT[],
    password_changed_at TIMESTAMP,
    last_login TIMESTAMP,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User sessions table
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    refresh_token TEXT NOT NULL,
    device_name VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Token blacklist table (Redis)
-- Key: token_id
-- Value: {"reason": "logout", "timestamp": "..."}
-- TTL: token expiration time
```

## Troubleshooting

### Common Issues

**Issue:** User can't login with correct password
- Check if account is locked
- Verify password hasn't expired
- Check for IP-based blocking
- Review security event logs

**Issue:** MFA codes not working
- Verify time synchronization
- Check backup codes
- Confirm MFA secret is correct
- Reset MFA if necessary

**Issue:** Token expired too quickly
- Verify token expiration settings
- Check server time synchronization
- Review token refresh implementation
- Ensure proper token storage

**Issue:** API authentication failing
- Verify API key is active
- Check key expiration date
- Confirm correct Authorization header
- Review API key permissions

## Next Steps

- [Authorization & Permissions →](./authorization)
- [Data Protection →](./data-protection)
- [Security Overview →](./security)
- [Audit Logging →](./audit-logging)
