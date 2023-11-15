#!/usr/bin/env bash
echo "Stopping Gunicorn server..."
pkill -f "onyx.gunicorn.py"

echo "Onyx stopped."
