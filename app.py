"""
Barcode Central - ZPL Label Printing Web Application
Main Flask application entry point
"""
import os
import logging
from datetime import timedelta
from flask import Flask, render_template
from flask_login import LoginManager
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure ProxyFix for reverse proxy support
# This allows Flask to trust X-Forwarded-* headers from nginx/Traefik
app.wsgi_app = ProxyFix(
    app.wsgi_app,
    x_for=1,  # Trust X-Forwarded-For
    x_proto=1,  # Trust X-Forwarded-Proto (HTTP vs HTTPS)
    x_host=1,  # Trust X-Forwarded-Host
    x_prefix=1  # Trust X-Forwarded-Prefix
)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
login_manager.login_message_category = 'warning'

# Import and register user_loader callback
from auth import load_user
login_manager.user_loader(load_user)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Session configuration for security
# In production, require HTTPS for session cookies (ProxyFix handles X-Forwarded-Proto)
# Set SESSION_COOKIE_SECURE=false in .env to disable if not using HTTPS
session_secure_env = os.getenv('SESSION_COOKIE_SECURE')
flask_env = os.getenv('FLASK_ENV')

# Debug logging
print(f"DEBUG: SESSION_COOKIE_SECURE env = {session_secure_env}")
print(f"DEBUG: FLASK_ENV = {flask_env}")

if session_secure_env is not None:
    app.config['SESSION_COOKIE_SECURE'] = session_secure_env.lower() == 'true'
    print(f"DEBUG: Setting SESSION_COOKIE_SECURE from env: {app.config['SESSION_COOKIE_SECURE']}")
else:
    # Default: secure in production, insecure in development
    app.config['SESSION_COOKIE_SECURE'] = flask_env == 'production'
    print(f"DEBUG: Setting SESSION_COOKIE_SECURE from FLASK_ENV: {app.config['SESSION_COOKIE_SECURE']}")

app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Configure logging
log_level = logging.DEBUG if os.getenv('FLASK_DEBUG') == '1' else logging.INFO
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/app.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Favicon handler to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    """Serve favicon or return 204 No Content"""
    from flask import send_from_directory
    favicon_path = os.path.join(app.root_path, 'static', 'favicon.ico')
    if os.path.exists(favicon_path):
        return send_from_directory(os.path.join(app.root_path, 'static'),
                                   'favicon.ico', mimetype='image/vnd.microsoft.icon')
    return '', 204  # No Content - prevents 404 in logs


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    # Don't log favicon 404s as they're expected
    if 'favicon.ico' not in str(error):
        logger.warning(f"404 error: {error}")
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    return render_template('500.html'), 500


# Blueprint registration
# Authentication and Web UI blueprints
from blueprints.auth_bp import auth_bp
from blueprints.web_bp import web_bp

# API blueprints
from blueprints.templates_bp import templates_bp
from blueprints.printers_bp import printers_bp
from blueprints.preview_bp import preview_bp
from blueprints.print_bp import print_bp
from blueprints.history_bp import history_bp

# Register authentication blueprint (no prefix - handles /, /login, /logout)
app.register_blueprint(auth_bp)

# Register web UI blueprint (no prefix - handles /dashboard, /templates, etc.)
app.register_blueprint(web_bp)

# Register API blueprints (with /api prefix)
app.register_blueprint(templates_bp, url_prefix='/api/templates')
app.register_blueprint(printers_bp, url_prefix='/api/printers')
app.register_blueprint(preview_bp, url_prefix='/api/preview')
app.register_blueprint(print_bp, url_prefix='/api/print')
app.register_blueprint(history_bp, url_prefix='/api/history')


# Health check endpoint for Docker
@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring and Docker health checks"""
    from datetime import datetime
    return {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'barcode-central'
    }, 200


if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs('previews', exist_ok=True)
    
    # Log startup
    logger.info("Starting Barcode Central application")
    logger.info(f"Environment: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"Debug mode: {os.getenv('FLASK_DEBUG', '0') == '1'}")
    
    # Run the application
    debug_mode = os.getenv('FLASK_DEBUG', '0') == '1'
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=debug_mode
    )