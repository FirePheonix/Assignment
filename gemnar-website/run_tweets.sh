#!/bin/bash
# Wrapper script for cron job to run scheduled tweets

# Set PATH to include homebrew and other common locations
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:$PATH"

# Change to the project directory
cd /Users/ashish/Desktop/gemnar-website

# Run the management command
/opt/homebrew/bin/poetry run python manage.py run_every_minute 