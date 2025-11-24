"""
Gunicorn configuration file for Barcode Central
Production WSGI server configuration
"""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 2

# Restart workers after this many requests to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = "logs/gunicorn-access.log"
errorlog = "logs/gunicorn-error.log"
loglevel = os.getenv("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "barcode-central"

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Preload app for better performance
preload_app = True

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized."""
    server.log.info("Starting Barcode Central")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    server.log.info("Reloading Barcode Central")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("Barcode Central is ready. Listening on: %s", bind)

def on_exit(server):
    """Called just before exiting Gunicorn."""
    server.log.info("Shutting down Barcode Central")