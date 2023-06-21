"""gunicorn WSGI server configuration."""

import os

chdir = os.path.join(os.environ["ONYX_WORKING_DIR"], "onyx")
wsgi_app = "onyx.wsgi"

bind = f"{os.environ['ONYX_HOST']}:{os.environ['ONYX_PORT']}"

workers = os.environ["ONYX_GUNICORN_WORKERS"]

accesslog = os.path.join(os.environ["ONYX_WORKING_DIR"], "logs", "access.log")
errorlog = os.path.join(os.environ["ONYX_WORKING_DIR"], "logs", "error.log")
capture_output = True  # Redirect stdout/stderr to errorlog

daemon = True  # Run process in the background
