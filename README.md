# Barcode Central

A modern web application for managing and printing ZPL (Zebra Programming Language) labels to network printers. Built with Flask and designed for easy deployment with Docker.

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Python](https://img.shields.io/badge/python-3.11-blue)
![Flask](https://img.shields.io/badge/flask-3.0.0-green)
![Docker](https://img.shields.io/badge/docker-ready-blue)

## Features

### 🏷️ Label Management
- **Template System**: Create and manage ZPL label templates with Jinja2 templating
- **Live Preview**: Generate PNG previews of labels before printing
- **Template Editor**: Built-in code editor with syntax highlighting
- **Variable Substitution**: Dynamic label generation with custom data

### 🖨️ Printer Management
- **Network Printers**: Support for Zebra network printers via TCP/IP
- **Multiple Printers**: Manage multiple printer configurations
- **Printer Testing**: Test connectivity and print test labels
- **Status Monitoring**: Check printer availability

### 📊 Print Job History
- **Job Tracking**: Complete history of all print jobs
- **Search & Filter**: Find jobs by template, printer, or date
- **Job Details**: View template data and parameters for each job
- **Export**: Download history data

### 🔐 Security
- **Authentication**: Secure login system
- **Session Management**: Secure session handling
- **Environment-based Config**: Sensitive data in environment variables
- **Non-root Container**: Docker container runs as non-privileged user

### 🚀 Modern Architecture
- **RESTful API**: Clean API design for all operations
- **Responsive UI**: Works on desktop and mobile devices
- **Docker Ready**: Production-ready containerization
- **Health Checks**: Built-in monitoring endpoints

## Quick Start

### Using Docker (Recommended)

```bash
# 1. Clone the repository
git clone <repository-url>
cd barcode-central

# 2. Create environment configuration
cp .env.production.example .env
nano .env  # Edit with your settings

# 3. Deploy
./scripts/deploy.sh --build
```

Access the application at `http://localhost:5000`

### Manual Installation

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
nano .env

# 3. Run development server
./run_dev.sh
```

## Documentation

- **[Deployment Guide](DEPLOYMENT.md)** - Complete deployment instructions
- **[Architecture](roo-docs/architecture.md)** - System architecture and design
- **[API Endpoints](roo-docs/endpoints.md)** - API documentation
- **[Data Structures](roo-docs/data_structures.md)** - Data models and schemas

## Requirements

### Production (Docker)
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 1GB disk space

### Development
- Python 3.11+
- pip
- Virtual environment (recommended)

## Configuration

### Environment Variables

Key configuration options in `.env`:

```env
# Security
SECRET_KEY=your-secret-key-here
LOGIN_USER=admin
LOGIN_PASSWORD=your-password

# Application
FLASK_ENV=production
FLASK_DEBUG=0
LOG_LEVEL=INFO
```

See [`.env.production.example`](.env.production.example) for all options.

### Printer Configuration

Add printers via the web interface or edit `printers.json`:

```json
[
  {
    "id": "printer-1",
    "name": "Warehouse Printer",
    "ip": "192.168.1.100",
    "port": 9100,
    "description": "Main warehouse label printer"
  }
]
```

### Template Configuration

Templates are stored in `templates_zpl/` directory as `.zpl.j2` files:

```zpl
^XA
^FO50,50^A0N,50,50^FD{{ product_name }}^FS
^FO50,120^BY3^BCN,100,Y,N,N^FD{{ barcode }}^FS
^XZ
```

## Project Structure

```
barcode-central/
├── app.py                      # Main application entry point
├── Dockerfile                  # Docker image definition
├── docker-compose.yml          # Container orchestration
├── gunicorn.conf.py           # Production server config
├── requirements.txt            # Python dependencies
├── .env.production.example    # Environment template
│
├── blueprints/                # Flask blueprints (routes)
│   ├── auth_bp.py            # Authentication
│   ├── web_bp.py             # Web UI routes
│   ├── templates_bp.py       # Template API
│   ├── printers_bp.py        # Printer API
│   ├── print_bp.py           # Print job API
│   ├── preview_bp.py         # Preview generation
│   └── history_bp.py         # History API
│
├── templates/                 # HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── edit_template.html
│   └── history.html
│
├── static/                    # Static assets
│   ├── css/
│   ├── js/
│   └── ace/                  # Code editor
│
├── templates_zpl/            # ZPL label templates
│   ├── example.zpl.j2
│   ├── product_label_4x2.zpl.j2
│   └── address_label_4x6.zpl.j2
│
├── scripts/                  # Deployment scripts
│   ├── build.sh
│   ├── deploy.sh
│   ├── backup.sh
│   └── restore.sh
│
├── utils/                    # Utility modules
│   ├── json_storage.py
│   └── validators.py
│
├── logs/                     # Application logs
├── previews/                 # Generated previews
├── history.json             # Print job history
└── printers.json            # Printer configurations
```

## API Overview

### Authentication
- `POST /login` - User login
- `GET /logout` - User logout

### Templates
- `GET /api/templates` - List all templates
- `GET /api/templates/<id>` - Get template details
- `POST /api/templates` - Create template
- `PUT /api/templates/<id>` - Update template
- `DELETE /api/templates/<id>` - Delete template

### Printers
- `GET /api/printers` - List all printers
- `POST /api/printers` - Add printer
- `PUT /api/printers/<id>` - Update printer
- `DELETE /api/printers/<id>` - Delete printer
- `POST /api/printers/<id>/test` - Test printer

### Printing
- `POST /api/print` - Print label
- `POST /api/preview` - Generate preview

### History
- `GET /api/history` - Get print history
- `GET /api/history/search` - Search history
- `DELETE /api/history/<id>` - Delete history entry

See [API Documentation](roo-docs/endpoints.md) for complete details.

## Development

### Running Development Server

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
./run_dev.sh
```

The development server runs on `http://localhost:5000` with auto-reload enabled.

### Development Tools

- **Flask Debug Mode**: Enabled in development
- **Hot Reload**: Automatic restart on code changes
- **Debug Logging**: Detailed logs in development
- **Error Pages**: Detailed error information

### Code Structure

The application follows a modular blueprint architecture:

- **Blueprints**: Separate modules for different features
- **Managers**: Business logic in manager classes
- **Utils**: Shared utility functions
- **Templates**: Jinja2 HTML templates
- **Static**: CSS, JavaScript, and assets

## Deployment

### Docker Deployment (Recommended)

```bash
# Build and deploy
./scripts/deploy.sh --build

# View logs
docker-compose logs -f

# Stop application
docker-compose down
```

### Manual Deployment

```bash
# Install dependencies
pip install -r requirements.txt

# Run with gunicorn
gunicorn --config gunicorn.conf.py app:app
```

### Systemd Service

For non-Docker deployments, use the provided systemd service:

```bash
sudo cp barcode-central.service /etc/systemd/system/
sudo systemctl enable barcode-central
sudo systemctl start barcode-central
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

## Backup and Restore

### Create Backup

```bash
./scripts/backup.sh
```

Backups are stored in `backups/backup_YYYYMMDD_HHMMSS.tar.gz`

### Restore from Backup

```bash
./scripts/restore.sh backups/backup_20240101_120000.tar.gz
```

### Automated Backups

Set up cron job for automated backups:

```bash
crontab -e
# Add: 0 2 * * * cd /path/to/barcode-central && ./scripts/backup.sh
```

## Monitoring

### Health Check

```bash
curl http://localhost:5000/api/health
```

### View Logs

```bash
# Docker logs
docker-compose logs -f

# Application logs
tail -f logs/app.log

# Gunicorn logs
tail -f logs/gunicorn-access.log
tail -f logs/gunicorn-error.log
```

### Container Status

```bash
docker-compose ps
docker stats barcode-central
```

## Troubleshooting

### Common Issues

**Container won't start:**
```bash
# Check logs
docker-compose logs app

# Verify .env file exists
ls -la .env

# Check port availability
sudo lsof -i :5000
```

**Can't connect to printer:**
- Verify printer IP and port
- Check network connectivity: `ping <printer-ip>`
- Test printer port: `telnet <printer-ip> 9100`
- Ensure printer is on same network

**Preview generation fails:**
- Check Pillow installation
- Verify preview directory permissions
- Check logs for specific errors

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed troubleshooting.

## Security

### Best Practices

1. **Change default credentials** in `.env`
2. **Generate strong secret key**: `python -c "import secrets; print(secrets.token_hex(32))"`
3. **Secure .env file**: `chmod 600 .env`
4. **Use HTTPS** in production with reverse proxy
5. **Keep Docker updated**
6. **Regular backups**
7. **Monitor logs** for suspicious activity

### Production Checklist

- [ ] Changed default LOGIN_USER and LOGIN_PASSWORD
- [ ] Generated secure SECRET_KEY
- [ ] Set FLASK_ENV=production
- [ ] Set FLASK_DEBUG=0
- [ ] Configured HTTPS (if applicable)
- [ ] Set up firewall rules
- [ ] Configured automated backups
- [ ] Tested restore procedure
- [ ] Set up monitoring/alerting
- [ ] Reviewed security logs

## Technology Stack

- **Backend**: Flask 3.0, Python 3.11
- **Frontend**: HTML5, CSS3, JavaScript
- **Code Editor**: Ace Editor
- **Server**: Gunicorn
- **Container**: Docker, Docker Compose
- **Templating**: Jinja2
- **Image Processing**: Pillow
- **Networking**: Requests library

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Code Style

- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions
- Comment complex logic
- Keep functions focused and small

## License

[Add your license information here]

## Support

For issues, questions, or contributions:

- Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- Review [API Documentation](roo-docs/endpoints.md)
- Check logs for error details
- Verify configuration files

## Acknowledgments

- Flask framework and community
- Zebra Technologies for ZPL documentation
- Docker for containerization platform
- All contributors and users

---

**Version**: 1.0.0  
**Last Updated**: 2024-01-01  
**Maintained by**: [Your Name/Organization]