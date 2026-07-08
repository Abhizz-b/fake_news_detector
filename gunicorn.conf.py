#!/bin/bash
# Gunicorn configuration file

# Basic configuration
bind = "0.0.0.0:8080"
workers = 4  # Usually 2-4x the number of CPU cores
worker_class = "uvicorn.workers.UvicornWorker"
keepalive = 120
timeout = 120

# Logging configuration
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"

# Restart configuration
max_requests = 1000
max_requests_jitter = 50

# Process name
proc_name = "fact_checker_api"

# Preload the app to reduce startup time per worker
preload_app = True