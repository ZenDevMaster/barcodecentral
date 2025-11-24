# Barcode Central - Known Limitations

**Version:** 1.0.0  
**Last Updated:** 2024-11-24

This document outlines the known limitations of Barcode Central. Understanding these limitations will help you make informed decisions about deployment and usage.

---

## 1. Authentication & User Management

### Single User Only
**Limitation:** The application supports only one user account configured via environment variables.

**Impact:**
- No multi-user support
- No user registration or management
- All users share the same credentials
- No user-specific settings or preferences

**Workaround:**
- Use separate instances for different users/teams
- Implement external authentication proxy
- Plan upgrade to version 1.2+ for multi-user support

**Future Enhancement:** Version 1.2 will add multi-user support with user management UI.

### No Password Hashing
**Limitation:** Passwords are stored in plain text in the `.env` file.

**Impact:**
- Security risk if `.env` file is compromised
- No password complexity requirements
- No password expiration

**Workaround:**
- Restrict `.env` file permissions (chmod 600)
- Use strong, unique passwords
- Rotate passwords regularly
- Deploy behind VPN or firewall

**Future Enhancement:** Version 1.1 will add password hashing with bcrypt.

### No Password Reset
**Limitation:** No self-service password reset functionality.

**Impact:**
- Manual `.env` file editing required
- Application restart needed after password change
- No email-based reset

**Workaround:**
- Document password change procedure
- Maintain secure access to server
- Keep backup of `.env` file

**Future Enhancement:** Version 1.2 will add password reset functionality.

### No Role-Based Access Control
**Limitation:** No roles, permissions, or access control.

**Impact:**
- All authenticated users have full access
- Cannot restrict features by user
- No audit trail by user

**Workaround:**
- Use separate instances for different access levels
- Implement external authorization proxy
- Monitor logs for all activities

**Future Enhancement:** Version 1.2 will add RBAC with roles like Admin, Operator, Viewer.

---

## 2. Data Storage

### JSON File-Based Storage
**Limitation:** All data stored in JSON files, not a database.

**Impact:**
- Limited scalability (recommended max 1000 history entries)
- No ACID transactions
- No concurrent write protection
- File corruption risk
- No advanced querying

**Workaround:**
- Regular backups (use provided scripts)
- Monitor file sizes
- Implement file rotation
- Consider external backup solutions

**Future Enhancement:** Version 1.2 will add PostgreSQL/MySQL support.

### No Database Backend
**Limitation:** No SQL or NoSQL database support.

**Impact:**
- Cannot leverage database features (indexes, joins, etc.)
- Limited query capabilities
- No database-level backups
- No replication or clustering

**Workaround:**
- Use JSON storage for small to medium deployments
- Implement custom backup strategies
- Monitor storage usage

**Future Enhancement:**
- Version 1.1: SQLite support
- Version 1.2: PostgreSQL/MySQL support
- Version 2.0: MongoDB support

### Limited History Storage
**Limitation:** History automatically rotates at 1000 entries.

**Impact:**
- Older entries automatically deleted
- No long-term historical analysis
- Limited data retention

**Workaround:**
- Export history regularly
- Archive exported data
- Increase rotation limit in code (not recommended)
- Implement external logging

**Future Enhancement:** Version 1.2 will add configurable retention and archiving.

### No Data Encryption
**Limitation:** Data stored in plain text JSON files.

**Impact:**
- Sensitive data not encrypted at rest
- Template data visible in file system
- History data readable

**Workaround:**
- Use encrypted file system (LUKS, BitLocker)
- Restrict file permissions
- Deploy in secure environment
- Avoid storing sensitive data in templates

**Future Enhancement:** Version 2.0 will add optional data encryption.

---

## 3. Printing Capabilities

### Network Printers Only
**Limitation:** Only supports network-accessible Zebra printers via TCP/IP.

**Impact:**
- Cannot use USB-connected printers
- Cannot use Bluetooth printers
- Requires network configuration
- Firewall rules may be needed

**Workaround:**
- Use network print servers for USB printers
- Configure printer network settings
- Use printer sharing features
- Consider Zebra ZebraNet adapters

**Future Enhancement:** Version 2.0 may add USB printer support.

### No Printer Driver Support
**Limitation:** Direct TCP socket communication only, no printer drivers.

**Impact:**
- Limited to printers supporting raw TCP (port 9100)
- No Windows printer queue integration
- No CUPS integration on Linux
- Cannot use system print dialogs

**Workaround:**
- Use printers with TCP/IP support
- Configure printers for raw TCP printing
- Use network print servers

**Future Enhancement:** Version 1.2 may add CUPS integration.

### No Print Queue Management
**Limitation:** No print queue, jobs sent directly to printer.

**Impact:**
- Cannot pause or cancel print jobs
- Cannot prioritize jobs
- Cannot view pending jobs
- No job scheduling

**Workaround:**
- Print one job at a time
- Verify preview before printing
- Use printer's built-in queue (if available)

**Future Enhancement:** Version 1.2 will add print queue management.

### No Printer Status Monitoring
**Limitation:** Basic connectivity check only, no detailed status.

**Impact:**
- Cannot detect low paper
- Cannot detect printer errors
- Cannot detect offline printers (until print fails)
- No proactive alerts

**Workaround:**
- Manually check printer status
- Test connection before printing
- Monitor printer physically
- Use printer's web interface

**Future Enhancement:** Version 1.2 will add SNMP monitoring.

---

## 4. Preview Generation

### Requires Internet Connection
**Limitation:** Preview generation requires internet access to Labelary API.

**Impact:**
- Cannot generate previews offline
- Dependent on external service
- Network latency affects preview speed
- Service outages prevent previews

**Workaround:**
- Ensure reliable internet connection
- Cache previews for reuse
- Test ZPL on actual printer
- Use Labelary's local installation (enterprise)

**Future Enhancement:** Version 1.2 will add local preview generation.

### Limited Label Sizes
**Limitation:** Preview supports standard label sizes only.

**Impact:**
- Custom sizes may not preview correctly
- Some label dimensions not supported
- Preview may not match actual output

**Workaround:**
- Use standard label sizes (4x2, 4x6, etc.)
- Test custom sizes on actual printer
- Adjust template for standard sizes

**Future Enhancement:** Version 1.2 will add custom size support.

### No Offline Preview
**Limitation:** Cannot generate previews without internet.

**Impact:**
- Preview unavailable in air-gapped environments
- Cannot work offline
- Dependent on Labelary service availability

**Workaround:**
- Print test labels without preview
- Use Labelary's local installation
- Cache previews for common templates

**Future Enhancement:** Version 1.2 will add local rendering engine.

---

## 5. Scalability & Performance

### Single Instance Only
**Limitation:** Designed for single instance deployment.

**Impact:**
- No horizontal scaling
- No load balancing
- Single point of failure
- Limited concurrent users

**Workaround:**
- Deploy on adequately sized server
- Use reverse proxy for caching
- Monitor resource usage
- Plan for vertical scaling

**Future Enhancement:** Version 2.0 will support multi-instance deployment.

### No Load Balancing
**Limitation:** Cannot distribute load across multiple instances.

**Impact:**
- All traffic to single instance
- Limited scalability
- No redundancy

**Workaround:**
- Use single powerful server
- Implement caching
- Optimize performance
- Monitor resource usage

**Future Enhancement:** Version 2.0 will add load balancing support.

### File-Based Locking
**Limitation:** No distributed locking mechanism.

**Impact:**
- Concurrent writes may conflict
- Race conditions possible
- Data corruption risk with multiple instances

**Workaround:**
- Use single instance only
- Implement external locking if needed
- Monitor for conflicts

**Future Enhancement:** Version 1.2 will add proper locking with database.

### Limited Concurrent Users
**Limitation:** Not optimized for high concurrency.

**Impact:**
- Performance degrades with many simultaneous users
- Recommended max: 10-20 concurrent users
- No connection pooling

**Workaround:**
- Deploy on adequate hardware
- Use caching
- Stagger usage if possible
- Monitor performance

**Future Enhancement:** Version 1.2 will add performance optimizations.

---

## 6. Integration & API

### No API Versioning
**Limitation:** API endpoints not versioned.

**Impact:**
- Breaking changes may affect integrations
- No backward compatibility guarantee
- Difficult to maintain multiple API versions

**Workaround:**
- Document API changes in CHANGELOG
- Test integrations after updates
- Pin to specific version

**Future Enhancement:** Version 1.2 will add API versioning (/api/v1/).

### No Rate Limiting
**Limitation:** No API rate limiting or throttling.

**Impact:**
- Vulnerable to abuse
- No protection against DoS
- Resource exhaustion possible

**Workaround:**
- Deploy behind reverse proxy with rate limiting
- Use firewall rules
- Monitor API usage
- Implement external rate limiting

**Future Enhancement:** Version 1.2 will add rate limiting.

### No Webhooks
**Limitation:** No webhook support for events.

**Impact:**
- Cannot notify external systems
- No event-driven integrations
- Must poll for changes

**Workaround:**
- Poll API endpoints
- Monitor history for changes
- Use external monitoring tools

**Future Enhancement:** Version 1.2 will add webhook support.

### Session-Based Authentication Only
**Limitation:** No API key or token-based authentication.

**Impact:**
- Difficult for programmatic access
- Must maintain session cookies
- No service-to-service authentication

**Workaround:**
- Use session cookies in API clients
- Implement external authentication proxy
- Use reverse proxy for auth

**Future Enhancement:** Version 1.2 will add API key authentication.

---

## 7. Deployment & Operations

### No High Availability
**Limitation:** No built-in HA or failover.

**Impact:**
- Single point of failure
- Downtime during updates
- No automatic failover

**Workaround:**
- Use reliable infrastructure
- Schedule maintenance windows
- Implement external monitoring
- Keep backups current

**Future Enhancement:** Version 2.0 will add HA support.

### No Auto-Scaling
**Limitation:** Cannot automatically scale based on load.

**Impact:**
- Manual scaling required
- Cannot handle traffic spikes
- Over-provisioning needed

**Workaround:**
- Provision for peak load
- Monitor resource usage
- Scale vertically as needed

**Future Enhancement:** Version 2.0 will add auto-scaling support.

### Limited Monitoring
**Limitation:** Basic health check only, no advanced monitoring.

**Impact:**
- Limited visibility into application health
- No performance metrics
- No alerting
- Difficult to troubleshoot

**Workaround:**
- Use external monitoring tools (Prometheus, etc.)
- Monitor logs
- Implement custom health checks
- Use Docker health checks

**Future Enhancement:** Version 1.2 will add metrics and monitoring.

### No Built-in Backup Automation
**Limitation:** Backup scripts provided but not automated.

**Impact:**
- Manual backup execution required
- Risk of data loss if backups not performed
- No scheduled backups

**Workaround:**
- Set up cron jobs for backups
- Use external backup solutions
- Implement monitoring for backups
- Test restore procedures

**Future Enhancement:** Version 1.2 will add automated backup scheduling.

---

## 8. Security

### No Two-Factor Authentication
**Limitation:** No 2FA or MFA support.

**Impact:**
- Password-only authentication
- Vulnerable to credential theft
- No additional security layer

**Workaround:**
- Use strong passwords
- Deploy behind VPN
- Implement external 2FA proxy
- Restrict network access

**Future Enhancement:** Version 2.0 will add 2FA support.

### No Login Attempt Limiting
**Limitation:** No rate limiting on login attempts.

**Impact:**
- Vulnerable to brute force attacks
- No account lockout
- No failed login tracking

**Workaround:**
- Use strong passwords
- Deploy behind reverse proxy with rate limiting
- Monitor logs for failed attempts
- Use firewall rules

**Future Enhancement:** Version 1.2 will add login attempt limiting.

### No Audit Logging
**Limitation:** Basic logging only, no comprehensive audit trail.

**Impact:**
- Limited visibility into user actions
- Difficult to track changes
- No compliance support

**Workaround:**
- Monitor application logs
- Implement external logging
- Use reverse proxy logging
- Review history regularly

**Future Enhancement:** Version 1.2 will add comprehensive audit logging.

### No HTTPS Enforcement
**Limitation:** Application runs on HTTP by default.

**Impact:**
- Credentials sent in clear text
- Vulnerable to man-in-the-middle attacks
- No encryption in transit

**Workaround:**
- Deploy behind reverse proxy with HTTPS
- Use Nginx or Apache with SSL/TLS
- Obtain SSL certificates (Let's Encrypt)
- Configure secure cookies

**Future Enhancement:** Version 1.2 will add built-in HTTPS support.

---

## 9. User Experience

### No Dark Mode
**Limitation:** Light mode only, no dark theme.

**Impact:**
- Eye strain in low-light environments
- No user preference options
- Limited accessibility

**Workaround:**
- Use browser extensions for dark mode
- Adjust monitor brightness
- Use system-wide dark mode

**Future Enhancement:** Version 1.2 will add dark mode support.

### English Only
**Limitation:** No internationalization or localization.

**Impact:**
- English-only interface
- No multi-language support
- Limited global usability

**Workaround:**
- Use browser translation
- Create custom translations
- Fork and translate

**Future Enhancement:** Version 2.0 will add i18n support.

### Limited Accessibility
**Limitation:** Basic accessibility, not fully WCAG compliant.

**Impact:**
- May not work well with screen readers
- Limited keyboard navigation
- No accessibility settings

**Workaround:**
- Use browser accessibility features
- Provide alternative access methods
- Test with assistive technologies

**Future Enhancement:** Version 1.2 will improve accessibility.

### No Mobile App
**Limitation:** Web interface only, no native mobile app.

**Impact:**
- Mobile browser experience only
- No offline mobile access
- No mobile-specific features

**Workaround:**
- Use responsive web interface
- Add to home screen (PWA-like)
- Use mobile browser

**Future Enhancement:** Version 2.0 will add mobile app.

---

## 10. Feature Limitations

### No Template Versioning
**Limitation:** No version control for templates.

**Impact:**
- Cannot track template changes
- Cannot revert to previous versions
- No change history

**Workaround:**
- Manual version control (Git)
- Backup templates regularly
- Use descriptive names with versions
- Document changes manually

**Future Enhancement:** Version 1.2 will add template versioning.

### No Batch Operations
**Limitation:** Operations performed one at a time.

**Impact:**
- Cannot print multiple different labels at once
- Cannot bulk update templates
- Time-consuming for large operations

**Workaround:**
- Use API for automation
- Create scripts for batch operations
- Process items sequentially

**Future Enhancement:** Version 1.2 will add batch operations.

### No Scheduled Printing
**Limitation:** No job scheduling functionality.

**Impact:**
- Cannot schedule prints for later
- Cannot automate recurring prints
- Manual intervention required

**Workaround:**
- Use external scheduling (cron + API)
- Create custom scripts
- Print manually when needed

**Future Enhancement:** Version 1.2 will add job scheduling.

### No Template Marketplace
**Limitation:** No sharing or marketplace for templates.

**Impact:**
- Cannot share templates with community
- Cannot download pre-made templates
- Must create all templates manually

**Workaround:**
- Share templates via file system
- Create template repository
- Document templates

**Future Enhancement:** Version 2.0 will add template marketplace.

---

## Mitigation Strategies

### For Production Deployment

1. **Security:**
   - Deploy behind reverse proxy with HTTPS
   - Use strong passwords and rotate regularly
   - Restrict network access with firewall
   - Monitor logs for suspicious activity

2. **Reliability:**
   - Implement automated backups
   - Monitor application health
   - Use reliable infrastructure
   - Test disaster recovery procedures

3. **Performance:**
   - Deploy on adequate hardware
   - Implement caching where possible
   - Monitor resource usage
   - Optimize templates

4. **Scalability:**
   - Plan for growth
   - Monitor usage patterns
   - Consider upgrade path
   - Evaluate alternatives for high-scale needs

---

## When to Consider Alternatives

Consider alternative solutions if you need:

- **Multi-user support** with roles and permissions
- **High availability** and failover
- **Horizontal scaling** across multiple instances
- **Advanced security** features (2FA, SSO, etc.)
- **Database backend** with ACID transactions
- **Offline operation** without internet
- **Enterprise features** (LDAP, SAML, etc.)
- **High concurrency** (100+ simultaneous users)
- **Advanced monitoring** and alerting
- **Compliance** requirements (SOC 2, HIPAA, etc.)

---

## Reporting Issues

If you encounter a limitation not listed here:

1. Check if it's a bug or intended limitation
2. Review [FEATURES.md](FEATURES.md) for planned features
3. Check [ROADMAP.md](ROADMAP.md) for future plans
4. Submit issue with:
   - Clear description
   - Impact assessment
   - Suggested workaround
   - Use case details

---

## Summary

Barcode Central 1.0.0 is designed for:
- **Small to medium deployments** (1-20 users)
- **Single-site operations**
- **Trusted network environments**
- **Standard label printing workflows**
- **Organizations with technical staff**

It may not be suitable for:
- **Large enterprises** (100+ users)
- **Multi-site deployments**
- **High-security environments**
- **Complex workflows**
- **Mission-critical operations** (without HA)

**Future versions will address many of these limitations.** See [ROADMAP.md](ROADMAP.md) for details.

---

**Last Updated:** 2024-11-24  
**Document Version:** 1.0.0  
**For Questions:** See [CONTRIBUTING.md](CONTRIBUTING.md)