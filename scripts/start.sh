#!/usr/bin/env bash
cd "${0%/*}"
./stop.sh
cd ..
echo "Starting Gunicorn server..."
poetry run gunicorn -c onyx/onyx.gunicorn.py
echo "Onyx started."