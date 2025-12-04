#!/bin/bash

# Gracefully restart the uvicorn process by sending a SIGHUP signal.
# This is the recommended way to reload the application in a containerized
# environment without needing root privileges.

set -e

echo "Attempting to gracefully restart uvicorn..."

# Find the uvicorn process and send it the SIGHUP signal
# This will cause it to reload the code and restart its workers.
pkill -HUP uvicorn

echo "Uvicorn restart signal sent."