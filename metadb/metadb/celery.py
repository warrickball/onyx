import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "metadb.settings")

app = Celery("metadb", broker="pyamqp://guest@localhost//")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")


app.conf.beat_schedule = {
    "create-mpx-tables-task": {
        "task": "data.tasks.create_mpx_tables",
        "schedule": crontab(minute=f"*/{os.environ['METADB_CELERY_BEAT_TIME']}"),
    }
}
app.conf.task_routes = {"data.tasks.create_mpx_tables": {"queue": "create_mpx_tables"}}
