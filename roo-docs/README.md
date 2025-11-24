# Barcode Central - Technical Documentation

## Overview

This directory contains comprehensive technical documentation for the Barcode Central ZPL label printing web application. These documents provide detailed specifications for architecture, API endpoints, data structures, and deployment strategies.

## Documentation Files

### 1. [architecture.md](architecture.md)
**System Architecture and Design**

Comprehensive overview of the application architecture including:
- System components and their interactions
- Authentication flow and security model
- Template management system
- Printer communication architecture
- Preview generation workflow
- History logging system
- Data flow diagrams for key operations
- Performance and scalability considerations
- Technology stack details

**Key Topics**:
- Core application layer (Flask, Flask-Login, Jinja2)
- Data storage layer (JSON files, file system)
- External integration layer (Labelary API, Zebra printers)
- Security considerations and best practices
- Error handling strategies
- Monitoring and maintenance

**Target Audience**: Architects, senior developers, technical leads

---

### 2. [endpoints.md](endpoints.md)
**Complete API Endpoint Specifications**

Detailed documentation of all HTTP endpoints including:
- Authentication endpoints (login, logout, session)
- Template endpoints (list, create, read, update, delete, render)
- Printer endpoints (list, get, validate)
- Preview endpoints (generate PNG/PDF previews)
- Print endpoints (print, test print)
- History endpoints (list, get, reprint, delete)
- Utility endpoints (health check, system info)

**Each endpoint includes**:
- HTTP method and path
- Authentication requirements
- Request parameters and body format
- Response format with examples
- Error responses and status codes
- cURL examples for testing

**Target Audience**: Backend developers, API consumers, testers

---

### 3. [data_structures.md](data_structures.md)
**JSON File Structures and Data Models**

Complete specification of all data structures including:
- Environment variables (.env format)
- Printer configuration (printers.json)
- Print history (history.json)
- Template metadata (embedded in ZPL files)
- In-memory data models (sessions, templates, printers, jobs)
- API request/response schemas
- File naming conventions
- Data validation rules

**Key Topics**:
- File-based storage formats
- JSON schema definitions
- Field definitions and validation rules
- Data rotation and cleanup strategies
- Backup and migration strategies

**Target Audience**: Backend developers, database administrators, DevOps

---

### 4. [deployment.md](deployment.md)
**Deployment Strategies and Configuration**

Comprehensive deployment guide covering:
- Development setup (WSL + Python venv)
- Docker containerization
- Production deployment strategies
- Environment configuration
- Volume mapping and persistence
- Port exposure and networking
- Security hardening
- Backup and recovery procedures
- Troubleshooting common issues
- Performance tuning

**Key Topics**:
- Step-by-step setup instructions
- Dockerfile and docker-compose.yml
- Requirements.txt specification
- Network configuration for printer access
- Monitoring and logging setup
- Maintenance schedules

**Target Audience**: DevOps engineers, system administrators, deployment teams

---

## Quick Start Guide

### For Developers

1. **Understand the Architecture**
   - Read [`architecture.md`](architecture.md) for system overview
   - Review component interactions and data flows

2. **Learn the API**
   - Study [`endpoints.md`](endpoints.md) for API specifications
   - Test endpoints using provided cURL examples

3. **Understand Data Structures**
   - Review [`data_structures.md`](data_structures.md) for data formats
   - Understand validation rules and constraints

4. **Set Up Development Environment**
   - Follow [`deployment.md`](deployment.md) for WSL setup
   - Configure environment variables and test data

### For DevOps/System Administrators

1. **Review Deployment Options**
   - Read [`deployment.md`](deployment.md) thoroughly
   - Choose between venv or Docker deployment

2. **Understand Security Requirements**
   - Review security sections in [`architecture.md`](architecture.md)
   - Implement security best practices from [`deployment.md`](deployment.md)

3. **Plan Network Configuration**
   - Ensure printer network accessibility
   - Configure firewall rules as needed

4. **Set Up Monitoring**
   - Implement health checks
   - Configure logging and alerting

### For Architects/Technical Leads

1. **Review System Design**
   - Study [`architecture.md`](architecture.md) for design decisions
   - Understand scalability limitations and future enhancements

2. **Evaluate API Design**
   - Review [`endpoints.md`](endpoints.md) for API patterns
   - Consider integration requirements

3. **Assess Data Management**
   - Review [`data_structures.md`](data_structures.md) for data strategy
   - Plan for data growth and retention

4. **Plan Deployment Strategy**
   - Review [`deployment.md`](deployment.md) for deployment options
   - Consider high availability and disaster recovery

---

## Project Structure

```
app.barcodecentral/
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── .env.example             # Example environment variables
├── .env                     # Actual environment variables (not in git)
├── printers.json            # Printer definitions
├── history.json             # Print history log
├── Dockerfile               # Docker container definition
├── docker-compose.yml       # Docker Compose configuration
│
├── templates_zpl/           # ZPL template files
│   ├── shipping_label.zpl.j2
│   └── product_label.zpl.j2
│
├── static/                  # Static assets
│   ├── ace/                 # Ace Editor files
│   ├── css/                 # Stylesheets
│   └── js/                  # JavaScript files
│
├── templates/               # Jinja2 HTML templates
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── edit_template.html
│   ├── print_form.html
│   └── history.html
│
├── previews/                # Generated preview images
│   └── (auto-generated PNG/PDF files)
│
└── roo-docs/                # Technical documentation
    ├── README.md            # This file
    ├── architecture.md      # System architecture
    ├── endpoints.md         # API endpoints
    ├── data_structures.md   # Data formats
    └── deployment.md        # Deployment guide
```

---

## Key Features

### Simple Authentication
- Environment variable-based credentials
- Session-based authentication with Flask-Login
- No external authentication providers required

### Template Management
- Jinja2-based ZPL templates
- Variable substitution for dynamic content
- Web-based template editor with syntax highlighting
- Template metadata embedded in files

### Printer Integration
- Raw TCP socket communication (port 9100)
- Multiple printer support
- Label size validation with warnings
- Printer status checking

### Preview Generation
- Labelary API integration
- PNG and PDF preview formats
- Automatic cleanup of old previews
- Preview caching

### History Tracking
- Complete print job logging
- Reprint functionality
- Automatic rotation (last 1000 entries)
- Audit trail for compliance

---

## Technology Stack

### Backend
- **Python 3.9+**: Core language
- **Flask 2.x**: Web framework
- **Flask-Login**: Session management
- **Jinja2**: Template engine (HTML and ZPL)
- **Requests**: HTTP client for Labelary API
- **Gunicorn**: Production WSGI server

### Frontend
- **HTML5/CSS3**: UI structure and styling
- **JavaScript**: Client-side logic
- **Ace Editor**: Code editor for templates
- **Bootstrap 5** (optional): UI framework

### Storage
- **JSON Files**: Configuration and history
- **File System**: Templates and previews

### External Services
- **Labelary API**: Preview generation
- **Zebra Printers**: Label printing via TCP/IP

### Deployment
- **WSL**: Development environment
- **Docker**: Production containerization
- **Python venv**: Dependency isolation

---

## Design Principles

1. **Simplicity First**
   - No database required
   - File-based storage
   - Minimal dependencies

2. **Self-Contained**
   - All dependencies bundled
   - Works offline (except preview generation)
   - Easy to deploy and maintain

3. **Security by Design**
   - Session-based authentication
   - Secure cookie handling
   - Input validation
   - Path traversal prevention

4. **Flexibility**
   - Easy to add new templates
   - Simple printer configuration
   - Extensible architecture

5. **Maintainability**
   - Clear separation of concerns
   - Comprehensive documentation
   - Standard Flask patterns

---

## Configuration Requirements

### Minimum Requirements
- Python 3.9 or higher
- 512 MB RAM
- 1 GB disk space
- Network access to printers
- Internet access for preview generation (optional)

### Recommended Requirements
- Python 3.11
- 1 GB RAM
- 5 GB disk space (for previews and history)
- Dedicated network for printers
- Reverse proxy (Nginx) for production

---

## Security Considerations

### Authentication
- Strong passwords (12+ characters)
- Secure session cookies
- Session timeout
- CSRF protection

### Network Security
- Internal network for printers
- HTTPS via reverse proxy
- Firewall rules
- No external printer access

### Data Protection
- No sensitive data in templates
- Regular backups
- Preview cleanup
- Access logging

### File Security
- Restricted file permissions
- Path traversal prevention
- Input validation
- No arbitrary file operations

---

## Limitations and Constraints

### Current Limitations
1. **Single-user authentication**: Only one set of credentials
2. **File-based storage**: Not suitable for high-volume operations
3. **Synchronous operations**: No async print queue
4. **History limit**: Maximum 1000 entries (configurable)
5. **Preview dependency**: Requires Labelary API for previews
6. **Single server**: No built-in clustering or load balancing

### Future Enhancements
1. Database backend (SQLite/PostgreSQL)
2. Multi-user authentication with roles
3. Async print queue (Celery/RQ)
4. Distributed caching (Redis)
5. API rate limiting
6. Webhook notifications
7. Advanced reporting and analytics

---

## Support and Maintenance

### Documentation Updates
- Update documentation when features change
- Keep examples current
- Document breaking changes
- Maintain version history

### Code Quality
- Follow PEP 8 style guide
- Write comprehensive tests
- Document complex logic
- Use type hints

### Monitoring
- Application health checks
- Printer connectivity monitoring
- Disk space monitoring
- Error rate tracking

### Backup Strategy
- Daily configuration backups
- Weekly full backups
- Monthly archive backups
- Test restore procedures

---

## Contributing Guidelines

### Documentation Standards
- Use clear, concise language
- Include code examples
- Provide diagrams where helpful
- Keep formatting consistent

### Code Standards
- Follow Flask best practices
- Write self-documenting code
- Add docstrings to functions
- Include error handling

### Testing Requirements
- Unit tests for core logic
- Integration tests for API endpoints
- Manual testing for UI
- Printer connectivity tests

---

## Version History

### Version 1.0 (Initial Release)
- Complete architecture documentation
- Full API endpoint specifications
- Comprehensive data structure definitions
- Detailed deployment guide

---

## Additional Resources

### External Documentation
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [ZPL Programming Guide](https://www.zebra.com/us/en/support-downloads/knowledge-articles/zpl-programming-guide.html)
- [Labelary API Documentation](http://labelary.com/service.html)
- [Docker Documentation](https://docs.docker.com/)

### Related Tools
- [Ace Editor](https://ace.c9.io/)
- [Gunicorn](https://gunicorn.org/)
- [Flask-Login](https://flask-login.readthedocs.io/)

---

## Contact and Support

For questions, issues, or contributions:
1. Review the relevant documentation file
2. Check troubleshooting section in [`deployment.md`](deployment.md)
3. Consult the architecture diagrams in [`architecture.md`](architecture.md)
4. Review API examples in [`endpoints.md`](endpoints.md)

---

## License

[Specify your license here]

---

## Acknowledgments

- Flask framework and community
- Labelary API for preview generation
- Zebra Technologies for ZPL specification
- Ace Editor for code editing capabilities

---

**Last Updated**: 2025-11-24

**Documentation Version**: 1.0

**Application Version**: 1.0.0