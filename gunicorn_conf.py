import multiprocessing
import os

# Gunicorn configuration file
bind = "0.0.0.0:8000"

# Worker Options
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120  # Longer timeout for AI operations
keepalive = 5

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process Name
proc_name = "chatterfix_cmms"

# Daemon mode
daemon = False
