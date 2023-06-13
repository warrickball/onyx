"""gunicorn WSGI server configuration."""

import os

bind = f"{os.environ['ONYX_HOST']}:{os.environ['ONYX_PORT']}"
workers = os.environ["ONYX_GUNICORN_WORKERS"]
loglevel = "DEBUG"
