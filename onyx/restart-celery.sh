echo "Killing pre-existing celery processes..."
killall celery;
echo "Starting celery beat..."
celery -A onyx beat -l INFO &> celery-beat.log &
echo "Starting celery worker..."
celery -A onyx worker -Q create_mpx_tables --concurrency=1 -l INFO &> celery-worker.log &
