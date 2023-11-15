#!/usr/bin/env bash
cd "${0%/*}"
cd ..

echo "Creating Python virtual environment..."
python3 -m venv .venv

echo "Activating Python virtual environment..."
source .venv/bin/activate

echo "Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Creating logs folder..."
mkdir -p logs

cd onyx/

echo "Making database migrations..."
python manage.py makemigrations data accounts internal
python manage.py migrate
