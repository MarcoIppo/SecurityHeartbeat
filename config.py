"""Configuration and persistence module."""
import json
import os
from pathlib import Path
from datetime import datetime

STATE_FILE = Path.home() / ".secheartbeat_state.json"
HISTORY_FILE = Path.home() / ".secheartbeat_history.json"
APP_CONFIG_FILE = Path(__file__).parent / "app_config.json"


def _load_app_config() -> dict:
    if APP_CONFIG_FILE.exists():
        try:
            return json.loads(APP_CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


_APP_CFG = _load_app_config()

JIRA_URL = _APP_CFG.get("jira_url", os.environ.get("JIRA_URL", ""))
JIRA_USER = os.environ.get("JIRA_USER", "")
JIRA_TOKEN = os.environ.get("JIRA_TOKEN", "")
JIRA_PROJECT = _APP_CFG.get("project", os.environ.get("JIRA_PROJECT", "TORF"))
EPIC_ISSUETYPE = _APP_CFG.get("issuetype", "Epic")
EPIC_NAME_PATTERN = _APP_CFG.get("summary_contains", "Security heartbeat recurrent test activities for")
STORY_ISSUETYPE = _APP_CFG.get("story_issuetype", "Story")
MAX_EPICS = _APP_CFG.get("max_epics", 5)
TEAM_NAME = _APP_CFG.get("team_name", "Hydra")
BOARD_ID = _APP_CFG.get("board_id", 38770)

VERSION = "1.0.0"
APP_TITLE = "Security Heartbeat US Generator"
APP_DESC = "Generate and manage Jira User Stories from Security Heartbeat epics"


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_state(state: dict):
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
    _add_history(state)


def _add_history(state: dict):
    history = load_history()
    history.append({"timestamp": datetime.now().isoformat(), "state": state})
    # Keep last 100 entries
    if len(history) > 100:
        history = history[-100:]
    HISTORY_FILE.write_text(json.dumps(history, indent=2, default=str))


def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            return json.loads(HISTORY_FILE.read_text())
        except json.JSONDecodeError:
            return []
    return []
