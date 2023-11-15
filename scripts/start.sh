#!/usr/bin/env bash
cd "${0%/*}"
./stop.sh
cd ..

echo "Activating Python virtual environment..."
source .venv/bin/activate

cd onyx/

echo "Starting Gunicorn server..."
gunicorn -c onyx.gunicorn.py

echo "Onyx started."
