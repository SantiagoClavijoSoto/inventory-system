# Security Documentation - Inventory System

## Overview

This document describes the security measures implemented in the Inventory System
and provides guidelines for maintaining security in production deployments.

---

## 1. Database Security

### 1.1 Least Privilege Users

The system uses three separate MySQL users with different privilege levels:

| User | Privileges | Purpose |
|------|------------|---------|
| `inventory_app` | SELECT, INSERT, UPDATE, DELETE | Runtime application operations |
| `inventory_migrate` | ALL PRIVILEGES | Database migrations only |
| `inventory_readonly` | SELECT | Reports and analytics |

**Configuration:** `backend/scripts/init.sql`

### 1.2 MySQL Hardening

Security configurations in `docker/mysql/conf.d/security.cnf`:

- `local_infile = 0` - Prevents file read attacks
- `skip-show-database` - Hides database list
- `sql_mode = STRICT_*` - Enforces strict SQL validation
- SSL/TLS encryption for connections

### 1.3 SSL/TLS for Database Connections

Generate certificates:
```bash
cd docker/mysql
./generate-ssl-certs.sh
```

Enable in `security.cnf`:
```ini
require_secure_transport = ON
ssl_ca = /etc/mysql/ssl/ca.pem
ssl_cert = /etc/mysql/ssl/server-cert.pem
ssl_key = /etc/mysql/ssl/server-key.pem
```

---

## 2. Application Security

### 2.1 Django Security Settings

**Production settings** (`config/settings/production.py`):

```python
# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Security headers
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### 2.2 Authentication Security

- **JWT tokens** with short expiration (30 min access, 7 day refresh)
- **Rate limiting** on login endpoints (5 requests/minute)
- **Password validation** using Django's built-in validators
- **Failed login tracking** with account lockout

### 2.3 Input Validation

All API inputs are validated using:

1. **Django REST Framework serializers** - Schema validation
2. **StrictTypeValidator** - Type coercion with strict checking
3. **SecureIDField** - Integer IDs with bounds checking

**Usage:**
```python
from core.validators import StrictTypeValidator

validator = StrictTypeValidator(request.data)
product_id = validator.get_positive_int('product_id', required=True)
quantity = validator.get_positive_int('quantity', required=True, max_value=10000)
validator.raise_if_invalid()
```

### 2.4 Multi-Tenant Security

- All data is isolated by `company_id`
- `TenantQuerySetMixin` automatically filters queries
- Cross-tenant access is blocked at the ORM level

---

## 3. Audit Logging

### 3.1 Security Events

The `SecurityAuditMiddleware` logs:

- Authentication attempts (success/failure)
- Password changes
- Administrative actions
- Access to sensitive endpoints
- All 4xx/5xx responses
- Suspicious request patterns

### 3.2 Log Location

- **Console:** Real-time monitoring
- **File:** `backend/logs/security.log` (rotated, 10MB max, 10 backups)

### 3.3 Log Format

```json
{
  "event_type": "AUTH_LOGIN_FAILED",
  "timestamp": "2025-12-18T10:30:00-0500",
  "request": {
    "method": "POST",
    "path": "/api/v1/users/login/"
  },
  "response": {
    "status_code": 401,
    "duration_ms": 45.2
  },
  "user": {
    "id": null,
    "email": "attempted@email.com"
  },
  "client": {
    "ip": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  }
}
```

---

## 4. Web Application Firewall (WAF)

### 4.1 Nginx-based Protection

The nginx configuration (`docker/nginx/nginx.conf`) provides:

**Rate Limiting:**
- General: 10 req/s
- API: 30 req/s
- Auth: 5 req/min

**Request Filtering:**
- Block bad bots (sqlmap, nikto, nmap)
- Block suspicious HTTP methods (TRACE, TRACK)
- Block SQL injection patterns in query strings

**Security Headers:**
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- Content-Security-Policy
- Strict-Transport-Security

### 4.2 Cloud WAF Options

For additional protection, consider:

| Provider | Features | Cost |
|----------|----------|------|
| **Cloudflare** | DDoS, Bot protection, WAF rules | Free tier available |
| **AWS WAF** | Integration with ALB/CloudFront | Pay per rule/request |
| **ModSecurity** | Self-hosted, OWASP Core Rule Set | Free (self-managed) |

**Recommended:** Cloudflare (free tier) for:
- DDoS protection
- SSL termination
- Geographic blocking
- Rate limiting at edge

---

## 5. CI/CD Security

### 5.1 SAST Tools

Security scanning runs on every push:

**Bandit** - Python security linter
```bash
bandit -r backend/ --severity-level medium
```

**Safety** - Dependency vulnerability check
```bash
safety check
```

**pip-audit** - Additional dependency scanning
```bash
pip-audit
```

### 5.2 Django Security Check

```bash
python manage.py check --deploy --fail-level WARNING
```

### 5.3 Workflow Location

`.forgejo/workflows/security.yml`

---

## 6. Production Deployment Checklist

### Pre-Deployment

- [ ] Change all default passwords in `.env.prod`
- [ ] Generate new `SECRET_KEY`
- [ ] Generate MySQL SSL certificates
- [ ] Configure firewall rules
- [ ] Set up SSL certificates for nginx
- [ ] Review and customize rate limits

### Database

- [ ] Remove root remote access
- [ ] Create least-privilege users
- [ ] Enable SSL/TLS connections
- [ ] Enable audit logging
- [ ] Configure automated backups

### Application

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set secure cookie settings
- [ ] Enable HSTS
- [ ] Test CSP headers

### Monitoring

- [ ] Set up log aggregation
- [ ] Configure alerting for security events
- [ ] Enable uptime monitoring
- [ ] Set up error tracking (Sentry)

---

## 7. Incident Response

### 7.1 Suspected Breach

1. **Isolate:** Disconnect affected systems
2. **Preserve:** Capture logs and evidence
3. **Analyze:** Review security.log for indicators
4. **Contain:** Rotate all credentials
5. **Recover:** Restore from known-good backup
6. **Report:** Notify stakeholders per compliance requirements

### 7.2 Security Contacts

- Security Lead: [Configure in deployment]
- On-call: [Configure in deployment]

---

## 8. Compliance Notes

### OWASP Top 10 Coverage

| Risk | Status | Implementation |
|------|--------|----------------|
| A01: Broken Access Control | ✅ | RBAC, tenant isolation |
| A02: Cryptographic Failures | ✅ | bcrypt passwords, JWT |
| A03: Injection | ✅ | ORM, parameterized queries |
| A04: Insecure Design | ✅ | Security by design |
| A05: Security Misconfiguration | ✅ | Hardened defaults |
| A06: Vulnerable Components | ✅ | Dependency scanning |
| A07: Auth Failures | ✅ | Rate limiting, lockout |
| A08: Data Integrity | ✅ | Input validation |
| A09: Logging Failures | ✅ | Comprehensive audit log |
| A10: SSRF | ✅ | No external requests |

---

## 9. Regular Maintenance

### Weekly
- Review security.log for anomalies
- Check for new dependency vulnerabilities

### Monthly
- Rotate service account passwords
- Review user access rights
- Update dependencies

### Quarterly
- Security assessment
- Penetration testing
- Backup restoration test

---

## References

- [OWASP Top 10](https://owasp.org/Top10/)
- [Django Security Documentation](https://docs.djangoproject.com/en/5.0/topics/security/)
- [MySQL Security Guide](https://dev.mysql.com/doc/refman/8.0/en/security.html)
- [Nginx Security](https://nginx.org/en/docs/http/configuring_https_servers.html)
