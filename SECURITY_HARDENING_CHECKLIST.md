# Security Hardening Checklist

Comprehensive security checklist for Barcode Central production deployment.

## Table of Contents

1. [Application Security](#application-security)
2. [Server Security](#server-security)
3. [Network Security](#network-security)
4. [Container Security](#container-security)
5. [Mesh Network Security](#mesh-network-security)
6. [Raspberry Pi Security](#raspberry-pi-security)
7. [Data Security](#data-security)
8. [Monitoring & Logging](#monitoring--logging)
9. [Compliance & Best Practices](#compliance--best-practices)

---

## Application Security

### Authentication & Authorization

- [ ] **Change Default Credentials**
  - [ ] Set strong `LOGIN_USER` (not "admin")
  - [ ] Set complex `LOGIN_PASSWORD` (min 16 chars, mixed case, numbers, symbols)
  - [ ] Document credentials in secure password manager

- [ ] **Secret Key Management**
  - [ ] Generate cryptographically secure `SECRET_KEY`
  - [ ] Use: `python3 -c "import secrets; print(secrets.token_hex(32))"`
  - [ ] Never commit secrets to version control
  - [ ] Rotate secrets periodically (quarterly)

- [ ] **Session Security**
  - [ ] Set `SESSION_COOKIE_SECURE=true` (HTTPS only)
  - [ ] Set `SESSION_COOKIE_HTTPONLY=true`
  - [ ] Set `SESSION_COOKIE_SAMESITE=Lax`
  - [ ] Configure reasonable session timeout (24 hours default)

### Application Configuration

- [ ] **Production Mode**
  - [ ] Set `FLASK_ENV=production`
  - [ ] Set `FLASK_DEBUG=0`
  - [ ] Disable debug toolbar
  - [ ] Remove development endpoints

- [ ] **Logging**
  - [ ] Set `LOG_LEVEL=INFO` (not DEBUG in production)
  - [ ] Ensure logs don't contain sensitive data
  - [ ] Configure log rotation
  - [ ] Secure log file permissions (640)

- [ ] **Error Handling**
  - [ ] Custom error pages (no stack traces)
  - [ ] Generic error messages to users
  - [ ] Detailed errors only in logs
  - [ ] 404/500 pages configured

### Input Validation

- [ ] **Template Variables**
  - [ ] Validate all user inputs
  - [ ] Sanitize template data
  - [ ] Prevent ZPL injection
  - [ ] Limit variable lengths

- [ ] **File Uploads**
  - [ ] Validate file types (if applicable)
  - [ ] Limit file sizes
  - [ ] Scan for malware
  - [ ] Store outside web root

- [ ] **API Endpoints**
  - [ ] Rate limiting configured
  - [ ] Input validation on all endpoints
  - [ ] Proper HTTP methods enforced
  - [ ] CORS configured correctly

---

## Server Security

### Operating System

- [ ] **System Updates**
  - [ ] Enable automatic security updates
  - [ ] Configure unattended-upgrades
  - [ ] Regular manual updates (monthly)
  - [ ] Subscribe to security mailing lists

- [ ] **User Management**
  - [ ] Disable root login
  - [ ] Use sudo for privileged operations
  - [ ] Remove unnecessary user accounts
  - [ ] Strong password policy enforced

- [ ] **SSH Hardening**
  - [ ] Disable password authentication
  - [ ] Use SSH keys only (ED25519 or RSA 4096)
  - [ ] Change default SSH port (optional)
  - [ ] Configure fail2ban
  - [ ] Limit SSH access by IP (if possible)

### Firewall Configuration

- [ ] **UFW/iptables Rules**
  ```bash
  sudo ufw default deny incoming
  sudo ufw default allow outgoing
  sudo ufw allow 22/tcp      # SSH
  sudo ufw allow 80/tcp      # HTTP
  sudo ufw allow 443/tcp     # HTTPS
  sudo ufw allow 41641/udp   # Headscale
  sudo ufw enable
  ```

- [ ] **Port Exposure**
  - [ ] Only necessary ports open
  - [ ] No database ports exposed (if using)
  - [ ] No internal services exposed
  - [ ] Regular port scan audits

- [ ] **DDoS Protection**
  - [ ] Rate limiting at firewall level
  - [ ] Connection limits configured
  - [ ] SYN flood protection
  - [ ] Consider Cloudflare (optional)

### File System Security

- [ ] **Permissions**
  - [ ] Environment files: 600 (owner read/write only)
  - [ ] Configuration files: 640
  - [ ] Log files: 640
  - [ ] Application files: 644
  - [ ] Directories: 755

- [ ] **Ownership**
  - [ ] Application owned by non-root user
  - [ ] Logs owned by application user
  - [ ] No world-writable files
  - [ ] Regular permission audits

---

## Network Security

### HTTPS/TLS

- [ ] **Certificate Management**
  - [ ] Valid SSL certificate (Let's Encrypt)
  - [ ] Auto-renewal configured
  - [ ] Certificate expiry monitoring
  - [ ] Strong cipher suites only
  - [ ] TLS 1.2+ only (disable TLS 1.0/1.1)

- [ ] **Traefik Configuration**
  - [ ] HSTS enabled (Strict-Transport-Security)
  - [ ] Force HTTPS redirect
  - [ ] Security headers configured
  - [ ] Certificate resolver working

- [ ] **Security Headers**
  ```
  Strict-Transport-Security: max-age=31536000; includeSubDomains
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  X-XSS-Protection: 1; mode=block
  Referrer-Policy: strict-origin-when-cross-origin
  ```

### DNS Security

- [ ] **DNS Configuration**
  - [ ] DNSSEC enabled (if supported)
  - [ ] CAA records configured
  - [ ] SPF/DKIM/DMARC (if sending email)
  - [ ] Regular DNS audit

### Network Segmentation

- [ ] **Docker Networks**
  - [ ] Separate networks for services
  - [ ] No unnecessary network exposure
  - [ ] Internal networks for backend services
  - [ ] Network policies configured

---

## Container Security

### Docker Configuration

- [ ] **Container Hardening**
  - [ ] Run as non-root user
  - [ ] Read-only root filesystem (where possible)
  - [ ] No privileged containers
  - [ ] Resource limits configured
  - [ ] Health checks enabled

- [ ] **Image Security**
  - [ ] Use official base images
  - [ ] Pin image versions (no :latest)
  - [ ] Regular image updates
  - [ ] Scan images for vulnerabilities
  - [ ] Minimal image size

- [ ] **Docker Daemon**
  - [ ] TLS enabled for remote access
  - [ ] User namespace remapping
  - [ ] Audit logging enabled
  - [ ] Regular Docker updates

### Volume Security

- [ ] **Volume Mounts**
  - [ ] Minimal volume mounts
  - [ ] Read-only mounts where possible
  - [ ] No sensitive host paths mounted
  - [ ] Proper permissions on volumes

- [ ] **Data Persistence**
  - [ ] Encrypted volumes (if required)
  - [ ] Regular backups
  - [ ] Backup encryption
  - [ ] Offsite backup storage

---

## Mesh Network Security

### Headscale Security

- [ ] **Server Configuration**
  - [ ] Strong authentication required
  - [ ] API access restricted
  - [ ] Regular updates
  - [ ] Audit logging enabled

- [ ] **ACL Policies**
  - [ ] Principle of least privilege
  - [ ] Explicit allow rules only
  - [ ] No wildcard permissions
  - [ ] Regular ACL review
  - [ ] Document ACL changes

- [ ] **Key Management**
  - [ ] Pre-auth keys with expiration
  - [ ] Regular key rotation
  - [ ] Revoke unused keys
  - [ ] Secure key storage

### Tailscale/WireGuard

- [ ] **Encryption**
  - [ ] WireGuard encryption enabled
  - [ ] Strong key exchange
  - [ ] Perfect forward secrecy
  - [ ] Regular security audits

- [ ] **Network Isolation**
  - [ ] Subnet routing limited
  - [ ] No full network access
  - [ ] Firewall rules on nodes
  - [ ] Monitor unusual traffic

---

## Raspberry Pi Security

### System Hardening

- [ ] **Initial Setup**
  - [ ] Change default password
  - [ ] Disable default user (if possible)
  - [ ] SSH keys only
  - [ ] Disable unnecessary services

- [ ] **Updates**
  - [ ] Automatic security updates
  - [ ] Regular manual updates
  - [ ] Firmware updates
  - [ ] Monitor security advisories

- [ ] **Firewall**
  - [ ] UFW configured
  - [ ] Only necessary ports open
  - [ ] Tailscale port allowed
  - [ ] Local network restrictions

### Physical Security

- [ ] **Device Protection**
  - [ ] Secure physical location
  - [ ] Locked enclosure (if possible)
  - [ ] Tamper detection (optional)
  - [ ] Power surge protection

- [ ] **Access Control**
  - [ ] Limited physical access
  - [ ] Access logging
  - [ ] Visitor policies
  - [ ] Device inventory

### Monitoring

- [ ] **Health Checks**
  - [ ] Automated health monitoring
  - [ ] Temperature monitoring
  - [ ] Disk space monitoring
  - [ ] Network connectivity checks

- [ ] **Alerting**
  - [ ] Alert on failures
  - [ ] Alert on high temperature
  - [ ] Alert on connectivity loss
  - [ ] Alert on unauthorized access

---

## Data Security

### Data at Rest

- [ ] **Encryption**
  - [ ] Encrypt sensitive data files
  - [ ] Encrypted backups
  - [ ] Secure key storage
  - [ ] Regular encryption audits

- [ ] **File Permissions**
  - [ ] Restrict access to data files
  - [ ] No world-readable sensitive files
  - [ ] Regular permission audits
  - [ ] Secure temporary files

### Data in Transit

- [ ] **Network Encryption**
  - [ ] HTTPS for web traffic
  - [ ] WireGuard for mesh network
  - [ ] TLS for API calls
  - [ ] No plaintext credentials

- [ ] **Printer Communication**
  - [ ] Secure printer networks
  - [ ] VPN/mesh for remote printers
  - [ ] No sensitive data in ZPL (if possible)
  - [ ] Printer access logging

### Backup Security

- [ ] **Backup Strategy**
  - [ ] Automated daily backups
  - [ ] Encrypted backups
  - [ ] Offsite backup storage
  - [ ] Regular backup testing

- [ ] **Backup Access**
  - [ ] Restricted backup access
  - [ ] Backup integrity checks
  - [ ] Backup retention policy
  - [ ] Secure backup deletion

---

## Monitoring & Logging

### Application Logging

- [ ] **Log Configuration**
  - [ ] Comprehensive logging enabled
  - [ ] Log rotation configured
  - [ ] Centralized logging (optional)
  - [ ] Log retention policy

- [ ] **Log Security**
  - [ ] Secure log storage
  - [ ] No sensitive data in logs
  - [ ] Log integrity protection
  - [ ] Regular log review

### Security Monitoring

- [ ] **Intrusion Detection**
  - [ ] fail2ban configured
  - [ ] Unusual activity monitoring
  - [ ] Failed login tracking
  - [ ] Port scan detection

- [ ] **Alerting**
  - [ ] Critical error alerts
  - [ ] Security event alerts
  - [ ] System health alerts
  - [ ] Alert escalation procedures

### Audit Logging

- [ ] **Audit Trail**
  - [ ] User actions logged
  - [ ] Configuration changes logged
  - [ ] Access attempts logged
  - [ ] Audit log retention

- [ ] **Compliance**
  - [ ] Meet regulatory requirements
  - [ ] Regular compliance audits
  - [ ] Documentation maintained
  - [ ] Incident response plan

---

## Compliance & Best Practices

### Security Policies

- [ ] **Documentation**
  - [ ] Security policy documented
  - [ ] Incident response plan
  - [ ] Disaster recovery plan
  - [ ] Regular policy review

- [ ] **Training**
  - [ ] Team security training
  - [ ] Security awareness
  - [ ] Incident response drills
  - [ ] Regular updates

### Regular Audits

- [ ] **Security Audits**
  - [ ] Quarterly security reviews
  - [ ] Penetration testing (annual)
  - [ ] Vulnerability scanning
  - [ ] Third-party audits (if required)

- [ ] **Access Reviews**
  - [ ] Regular access audits
  - [ ] Remove unused accounts
  - [ ] Review permissions
  - [ ] Update documentation

### Incident Response

- [ ] **Preparation**
  - [ ] Incident response plan
  - [ ] Contact list maintained
  - [ ] Backup communication channels
  - [ ] Regular drills

- [ ] **Detection & Response**
  - [ ] Monitoring in place
  - [ ] Alert procedures defined
  - [ ] Escalation paths clear
  - [ ] Post-incident review process

---

## Security Checklist Summary

### Critical (Must Have)

- [x] Strong passwords and secret keys
- [x] HTTPS enabled with valid certificate
- [x] SSH keys only (no password auth)
- [x] Firewall configured
- [x] Automatic security updates
- [x] Regular backups
- [x] Non-root containers
- [x] Headscale ACLs configured

### Important (Should Have)

- [ ] Monitoring and alerting
- [ ] Log aggregation
- [ ] Intrusion detection
- [ ] Regular security audits
- [ ] Incident response plan
- [ ] Security training
- [ ] Backup testing
- [ ] Vulnerability scanning

### Recommended (Nice to Have)

- [ ] WAF (Web Application Firewall)
- [ ] DDoS protection
- [ ] Penetration testing
- [ ] Security information and event management (SIEM)
- [ ] Compliance certifications
- [ ] Bug bounty program
- [ ] Security insurance
- [ ] Third-party security audits

---

## Security Maintenance Schedule

### Daily
- Automated backups
- Health checks
- Log monitoring

### Weekly
- Review security logs
- Check for failed login attempts
- Verify backup integrity
- Update documentation

### Monthly
- System updates
- Security patch review
- Access audit
- Certificate expiry check

### Quarterly
- Comprehensive security audit
- Policy review
- Team training
- Vulnerability assessment

### Annually
- Penetration testing
- Third-party audit
- Disaster recovery drill
- Security strategy review

---

## Security Resources

### Tools

- **Vulnerability Scanning**: Trivy, Clair, Anchore
- **Intrusion Detection**: fail2ban, OSSEC, Snort
- **Log Management**: ELK Stack, Graylog, Splunk
- **Monitoring**: Prometheus, Grafana, Nagios
- **Security Testing**: OWASP ZAP, Burp Suite, Nmap

### References

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CIS Benchmarks: https://www.cisecurity.org/cis-benchmarks/
- Docker Security: https://docs.docker.com/engine/security/
- NIST Cybersecurity Framework: https://www.nist.gov/cyberframework

---

## Emergency Contacts

**Document your emergency contacts:**

- Security Team Lead: _______________
- System Administrator: _______________
- Hosting Provider Support: _______________
- Security Incident Response: _______________
- Legal/Compliance: _______________

---

## Incident Response Quick Reference

### If Compromised

1. **Isolate**: Disconnect affected systems
2. **Assess**: Determine scope of breach
3. **Contain**: Prevent further damage
4. **Eradicate**: Remove threat
5. **Recover**: Restore from clean backups
6. **Review**: Post-incident analysis

### Emergency Commands

```bash
# Stop all services immediately
docker compose down

# Block all incoming traffic
sudo ufw default deny incoming

# Check for unauthorized access
sudo last
sudo lastb

# Review logs
sudo journalctl -xe
docker compose logs

# Restore from backup
./scripts/restore.sh backups/latest.tar.gz
```

---

**Remember**: Security is an ongoing process, not a one-time task. Regular reviews and updates are essential.

---

**Version**: 1.0.0  
**Last Updated**: 2024-11-24  
**Review Frequency**: Quarterly