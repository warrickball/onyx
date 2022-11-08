"""gunicorn WSGI server configuration."""

import multiprocessing
import os

bind = "127.0.0.1:8000"
loglevel = "DEBUG"
workers = os.getenv("METADB_WORKER_COUNT")
timeout = 120
reload = True
# keyfile = os.getenv("METADB_KEYFILE")
# certfile = os.getenv("METADB_CERTFILE")