# Changelog

All notable changes to Barcode Central will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-15

### Added
- Initial release of Barcode Central
- ZPL template management system with Jinja2 variable substitution
- Template CRUD operations (create, read, update, delete)
- Template validation and variable extraction
- Printer configuration and management
- Network printer support via TCP/IP (port 9100)
- Printer compatibility validation
- Label preview generation using Labelary API
- Print job execution with variable substitution
- Print history tracking and logging
- History search and filtering capabilities
- History statistics and analytics
- Reprint functionality from history
- Web-based user interface
- Ace Editor integration for template editing
- Session-based authentication
- RESTful API with JSON responses
- Docker deployment support
- Docker Compose configuration
- Nginx reverse proxy setup
- Systemd service configuration
- Comprehensive test suite (unit, API, integration tests)
- API documentation
- User guide
- Developer guide
- Deployment guide

### Features

#### Template Management
- Create and edit ZPL templates with Jinja2 syntax
- Template metadata (name, description, label size)
- Automatic variable extraction from templates
- Template validation (ZPL and Jinja2 syntax)
- Template preview before printing

#### Printer Management
- Add and configure network printers
- Test printer connectivity
- Validate label size compatibility
- Enable/disable printers
- Support for multiple label sizes per printer

#### Print Operations
- Render templates with custom variables
- Generate label previews
- Print to network printers
- Preview-only mode
- Multiple copy support
- Print job validation

#### History & Logging
- Automatic logging of all print jobs
- Search and filter history
- View detailed job information
- Reprint from history
- Export history data
- Usage statistics
- Automatic cleanup of old entries

#### User Interface
- Clean, responsive web interface
- Dashboard with quick stats
- Template editor with syntax highlighting
- Print form with variable inputs
- History viewer with search
- Printer management interface

#### Security
- Session-based authentication
- Secure password handling
- CSRF protection
- HTTP-only cookies
- Secure cookies in production

#### Deployment
- Docker containerization
- Docker Compose orchestration
- Nginx reverse proxy
- Systemd service support
- Production-ready configuration
- Backup and restore scripts

### Technical Details
- Python 3.9+ support
- Flask web framework
- Jinja2 templating engine
- JSON file-based storage
- Labelary API integration for previews
- TCP socket communication with printers
- Comprehensive error handling
- Logging and debugging support

### Documentation
- Complete API reference
- User guide with screenshots
- Developer guide
- Deployment guide
- Troubleshooting guide
- Contributing guidelines

### Testing
- Unit tests for all core modules
- API endpoint tests
- Integration tests for workflows
- Test coverage >70%
- Automated test runner

## [Unreleased]

### Planned Features
- Database backend option (PostgreSQL/MySQL)
- Multi-user support with roles
- Template versioning
- Batch printing
- Print queue management
- Email notifications
- Webhook support
- Advanced analytics dashboard
- Template marketplace/sharing
- Mobile-responsive improvements
- Dark mode theme
- Internationalization (i18n)
- API rate limiting
- OAuth2 authentication option

---

## Version History

- **1.0.0** (2024-01-15) - Initial release

---

## Migration Guide

### From Pre-release to 1.0.0

This is the first stable release. No migration needed.

---

## Support

For issues, questions, or feature requests:
- GitHub Issues: [Create an issue](https://github.com/yourusername/barcode-central/issues)
- Documentation: See [README.md](README.md)
- Email: support@example.com