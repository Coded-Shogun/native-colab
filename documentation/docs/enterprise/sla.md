# Service Level Agreement (SLA)

Native Colab Enterprise provides industry-leading SLA guarantees for uptime, performance, and support response times.

## Uptime SLA

### Service Availability

**Standard Edition:**
- Uptime: 99.5%
- Monthly downtime: < 3.6 hours
- No SLA credits

**Enterprise Edition:**
- Uptime: 99.9%
- Monthly downtime: < 43.8 minutes
- SLA credits for downtime

**Enterprise Premium:**
- Uptime: 99.95%
- Monthly downtime: < 21.9 minutes
- Enhanced SLA credits

### Uptime Calculation

```
Uptime % = (Total Minutes - Downtime Minutes) / Total Minutes × 100

Example (30-day month):
Total Minutes: 43,200
Downtime: 30 minutes
Uptime: (43,200 - 30) / 43,200 × 100 = 99.93%
```

### What Counts as Downtime

**Included:**
- Service completely unavailable
- Error rate > 5% for 5+ minutes
- Response time > 10 seconds for 10+ minutes
- Unable to login or authenticate

**Excluded:**
- Scheduled maintenance (with 7 days notice)
- Issues caused by customer configuration
- Third-party service failures (DNS, CDN)
- Force majeure events
- Customer's network issues
- Beta features

## Performance SLA

### Response Time Guarantees

**API Response Times:**
| Endpoint Type | p95 Latency | p99 Latency |
|---------------|-------------|-------------|
| Read operations | < 200ms | < 500ms |
| Write operations | < 500ms | < 1000ms |
| Search queries | < 1000ms | < 2000ms |
| File uploads | < 5000ms | < 10000ms |

**WebSocket Latency:**
- Message delivery: < 100ms (p95)
- Typing indicators: < 50ms (p95)
- Presence updates: < 200ms (p95)

### Database Performance

**Query Performance:**
- Simple queries: < 10ms (p95)
- Complex queries: < 100ms (p95)
- Aggregations: < 500ms (p95)
- Full-text search: < 1000ms (p95)

## Support Response SLA

### Response Times by Priority

| Priority | Description | Standard | Premium | Elite |
|----------|-------------|----------|---------|-------|
| P0 | Critical outage | 8 hours | 1 hour | 15 min |
| P1 | Major issue | 2 days | 4 hours | 2 hours |
| P2 | Minor issue | 5 days | 1 day | 4 hours |
| P3 | Question/Request | Best effort | 3 days | 1 day |

**Business Hours:**
- Standard: Monday-Friday, 9 AM - 5 PM local time
- Premium: 24/7 for P0, business hours for P1-P3
- Elite: 24/7 for all priorities

## SLA Credits

### Credit Calculation

**Enterprise Edition:**
| Monthly Uptime | Downtime | Service Credit |
|----------------|----------|----------------|
| < 99.9% | > 43.8 min | 10% |
| < 99.5% | > 3.6 hours | 25% |
| < 99.0% | > 7.2 hours | 50% |
| < 95.0% | > 36 hours | 100% |

**Enterprise Premium:**
| Monthly Uptime | Downtime | Service Credit |
|----------------|----------|----------------|
| < 99.95% | > 21.9 min | 10% |
| < 99.9% | > 43.8 min | 25% |
| < 99.5% | > 3.6 hours | 50% |
| < 99.0% | > 7.2 hours | 100% |

### Claiming Credits

**Process:**
1. Submit claim within 30 days of incident
2. Provide ticket number and downtime period
3. We verify with monitoring data
4. Credit applied to next invoice

**Example:**
```
Monthly License Cost: $1,000
Uptime Achieved: 99.7% (goal: 99.9%)
Credit Percentage: 10%
Credit Amount: $100
Next Invoice: $900
```

**Maximum Credit:** 100% of monthly fee for affected service

## Data Protection SLA

### Backup Guarantees

**Backup Frequency:**
- Database: Every hour
- Files: Every 4 hours
- Full backup: Daily
- Off-site replication: Real-time

**Backup Retention:**
- Hourly backups: 7 days
- Daily backups: 30 days
- Weekly backups: 90 days
- Monthly backups: 1 year

**Recovery Time Objective (RTO):** 4 hours
**Recovery Point Objective (RPO):** 1 hour

### Data Loss Prevention

**Guarantee:** Zero data loss under normal operations

**Protection:**
- Database replication with synchronous commit
- Transaction logs retained for 7 days
- Point-in-time recovery available
- Verified backups (tested monthly)

## Security SLA

### Security Incident Response

**Disclosure Timeline:**
- High severity: Within 24 hours
- Medium severity: Within 72 hours
- Low severity: Next security bulletin

**Patch Timeline:**
- Critical vulnerabilities: 24 hours
- High vulnerabilities: 7 days
- Medium vulnerabilities: 30 days

### Compliance Commitments

**Certifications:**
- SOC 2 Type II: Annual audit
- ISO 27001: Certified and maintained
- GDPR: Full compliance
- HIPAA: Available for BAA customers

## Monitoring and Reporting

### Status Page

**Real-Time Status:**
- https://status.nativecolab.com
- Current status of all services
- Incident history
- Scheduled maintenance

**Subscribe:**
- Email notifications
- SMS alerts (Premium/Elite)
- Slack integration
- RSS feed

### Monthly Reports

**Included:**
- Uptime percentage
- Performance metrics
- Incident summary
- Support ticket statistics
- Security events

**Available to:** All Enterprise customers via dashboard

### SLA Dashboard

```
https://app.nativecolab.com/admin/sla-dashboard

Current Month (January 2025):
┌─────────────────────────────────────┐
│ Uptime: 99.97% ✓                    │
│ Target: 99.9%                       │
│ Downtime: 12 minutes                │
│ Incidents: 1 (resolved)             │
│ SLA Credits: $0                     │
└─────────────────────────────────────┘

Performance Metrics:
┌─────────────────────────────────────┐
│ API p95 Latency: 145ms ✓            │
│ WebSocket Latency: 75ms ✓           │
│ Database Queries: 8ms ✓             │
└─────────────────────────────────────┘

Support Response Times:
┌─────────────────────────────────────┐
│ P0 Avg Response: 25 min ✓           │
│ P1 Avg Response: 2.5 hours ✓        │
│ Tickets Resolved: 45 / 48           │
└─────────────────────────────────────┘
```

## Maintenance Windows

### Scheduled Maintenance

**Notice Period:** 7 days minimum
**Frequency:** Maximum once per month
**Duration:** Maximum 4 hours
**Timing:** Off-peak hours (weekends, nights)
**Impact:** Planned downtime excluded from SLA

**Communication:**
1. Email notification (7 days prior)
2. In-app notification (3 days prior)
3. Status page update (1 day prior)
4. Pre/post-maintenance emails

### Emergency Maintenance

**When Required:**
- Critical security patch
- Data integrity risk
- Severe performance degradation

**Notice:** Best effort (minimum 1 hour when possible)
**Duration:** Minimized (typically < 30 minutes)
**Impact:** Counts toward SLA downtime

## Exceptions and Limitations

### Not Covered by SLA

**Customer Responsibility:**
- Custom code or integrations
- Third-party dependencies
- Network connectivity issues
- Browser compatibility
- User errors or misuse

**External Factors:**
- DNS provider outages
- Cloud provider (AWS/Azure) failures
- DDoS attacks
- Natural disasters
- Acts of terrorism
- Government actions

**Beta Features:**
- Features marked as "beta" or "preview"
- Experimental features
- Features in alpha testing

### Fair Usage Policy

**Rate Limits:**
- API: 60 requests/minute (authenticated)
- WebSocket: 100 messages/minute
- File uploads: 10 GB/hour
- Exports: 5 per hour

**Excessive Usage:**
- Will be contacted if usage exceeds 200% of plan
- May require upgrade to higher tier
- Intentional abuse may result in service suspension

## Legal Terms

### Service Credits

**Sole Remedy:** Service credits are the sole remedy for SLA breaches

**Limitations:**
- Maximum 100% of monthly fee
- Must be claimed within 30 days
- Cannot be exchanged for cash
- Do not roll over to next month

### Warranty Disclaimer

**As-Is Basis:** Service provided "as is" without warranties

**No Guarantee:**
- Uninterrupted service
- Error-free operation
- Meeting specific requirements
- Third-party compatibility

### Liability Limitation

**Maximum Liability:** Amount paid in last 12 months

**Excluded:**
- Indirect damages
- Loss of profits
- Loss of data (covered by backup SLA)
- Business interruption

## Changes to SLA

**Notification:** 30 days notice for material changes
**Acceptance:** Continued use constitutes acceptance
**Previous Terms:** Available in documentation archive

## Contact

**SLA Questions:**
- Email: sla@nativecolab.com
- Phone: +1-555-NATIVE-SLA

**Claim Service Credits:**
- Portal: https://support.nativecolab.com/credits
- Email: credits@nativecolab.com

**Status Updates:**
- Subscribe: https://status.nativecolab.com
- Twitter: @NativeColabStatus

## Next Steps

- [Support Plans →](./support-plans)
- [Enterprise Overview →](./overview)
- [High Availability →](./high-availability)
