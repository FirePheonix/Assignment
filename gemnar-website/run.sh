#!/bin/bash

# Run Django website with uvicorn

LOGDIR="$(dirname "$0")/logs"
mkdir -p "$LOGDIR"
LOGFILE="$LOGDIR/uvicorn.log"

echo "Starting Django website with uvicorn..."
echo "Live reloading enabled for Python code and HTML templates..."

# Activate poetry environment and run uvicorn with comprehensive reload configuration
poetry run uvicorn gemnar.asgi:application --host 0.0.0.0 --port 8000 --reload \
  --reload-dir templates \
  --reload-dir website/templates \
  --reload-dir chat/templates \
  --reload-dir website \
  --reload-dir chat \
  --reload-include="*.html" \
  --reload-include="*.py" \
  --reload-include="*.css" \
  --reload-include="*.js" \
  --log-level info --access-log \
  2>&1 | tee -a "$LOGFILE"