"""gunicorn WSGI server configuration."""

import os

bind = f"{os.environ['ONYX_HOST']}:{os.environ['ONYX_PORT']}"
loglevel = os.environ["ONYX_GUNICORN_LOG_LEVEL"]
workers = os.environ["ONYX_GUNICORN_WORKER_COUNT"]
timeout = os.environ["ONYX_GUNICORN_WORKER_TIMEOUT"]

# keyfile = os.environ["ONYX_KEYFILE"]
# certfile = os.environ["ONYX_CERTFILE"]
