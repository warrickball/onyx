"""gunicorn WSGI server configuration."""

import os

bind = f"{os.environ['METADB_HOST']}:{os.environ['METADB_PORT']}"
workers = os.environ["METADB_WORKER_COUNT"]
loglevel = os.environ["METADB_LOG_LEVEL"]
timeout = os.environ["METADB_WORKER_TIMEOUT"]

# keyfile = os.environ["METADB_KEYFILE"]
# certfile = os.environ["METADB_CERTFILE"]
