#!/bin/bash
# Security Heartbeat US Generator
# Usage: ./run.sh [--ita]
#
# Environment variables:
#   JIRA_URL   - Jira server URL
#   JIRA_USER  - Jira username/email
#   JIRA_TOKEN - Jira API token
#   JIRA_PROJECT - Project key (default: TORF)

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

if [ ! -d "$SCRIPT_DIR/.venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SCRIPT_DIR/.venv"
    source "$SCRIPT_DIR/.venv/bin/activate"
    pip install -r "$SCRIPT_DIR/requirements.txt"
else
    source "$SCRIPT_DIR/.venv/bin/activate"
fi

python "$SCRIPT_DIR/app.py" "$@"
