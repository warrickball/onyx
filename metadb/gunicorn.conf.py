"""gunicorn WSGI server configuration."""

import os

bind = f"{os.environ['METADB_HOST']}:{os.environ['METADB_PORT']}"
loglevel = os.environ["METADB_GUNICORN_LOG_LEVEL"]
workers = os.environ["METADB_GUNICORN_WORKER_COUNT"]
timeout = os.environ["METADB_GUNICORN_WORKER_TIMEOUT"]

# keyfile = os.environ["METADB_KEYFILE"]
# certfile = os.environ["METADB_CERTFILE"]
