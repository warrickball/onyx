"""gunicorn WSGI server configuration."""

import multiprocessing

bind = "127.0.0.1:8000"
loglevel = "DEBUG"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 120
reload = False
