#!/usr/bin/env bash
# Render.com deployment script

set -o errexit  # exit on error

# Install Poetry
pip install --upgrade pip
pip install poetry

# Configure Poetry to not create virtual environments (Render manages this)
poetry config virtualenvs.create false

# Install dependencies using Poetry (production only, no dev dependencies)
poetry install --only=main

# Collect static files
poetry run python manage.py collectstatic --no-input

# Run database migrations
poetry run python manage.py migrate