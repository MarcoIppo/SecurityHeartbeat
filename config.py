"""Configuration and persistence module."""
import json
import os
import base64
import stat
import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger("secheartbeat.config")

STATE_FILE = Path.home() / ".secheartbeat_state.json"
HISTORY_FILE = Path.home() / ".secheartbeat_history.json"
APP_CONFIG_FILE = Path(__file__).parent / "app_config.json"


def _load_app_config() -> dict:
    if APP_CONFIG_FILE.exists():
        try:
            data = json.loads(APP_CONFIG_FILE.read_text())
            log.debug(f"App config loaded: {list(data.keys())}")
            return data
        except json.JSONDecodeError as e:
            log.error(f"Failed to parse app_config.json: {e}")
            return {}
    log.debug("app_config.json not found, using defaults")
    return {}


def save_app_config(updates: dict):
    """Merge updates into app_config.json and save atomically."""
    import tempfile
    log.debug(f"save_app_config() updating keys: {list(updates.keys())}")
    cfg = _load_app_config()
    cfg.update(updates)
    content = json.dumps(cfg, indent=2, ensure_ascii=False)
    # Write to temp file then atomic rename (POSIX guarantees)
    tmp_fd, tmp_path = tempfile.mkstemp(
        dir=str(APP_CONFIG_FILE.parent), suffix=".tmp"
    )
    try:
        os.write(tmp_fd, content.encode("utf-8"))
        os.close(tmp_fd)
        os.replace(tmp_path, str(APP_CONFIG_FILE))
        log.debug(f"  app_config.json saved atomically")
    except Exception:
        os.close(tmp_fd) if not os.get_inheritable(tmp_fd) else None
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise


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

VERSION = "1.4.4"
APP_TITLE = "Security Heartbeat US Generator"
APP_DESC = "Generate and manage Jira User Stories from Security Heartbeat epics"

# Window geometry defaults
DEFAULT_GEOMETRY = "1200x850"
WINDOW_GEOMETRY = _APP_CFG.get("window_geometry", DEFAULT_GEOMETRY)
POPUP_GEOMETRIES = _APP_CFG.get("popup_geometries", {})


def _obfuscate_token(token: str) -> str:
    """Encode token to base64 to prevent casual plain-text exposure."""
    if not token:
        return ""
    return base64.b64encode(token.encode("utf-8")).decode("ascii")


def _deobfuscate_token(encoded: str) -> str:
    """Decode base64-obfuscated token."""
    if not encoded:
        return ""
    try:
        return base64.b64decode(encoded.encode("ascii")).decode("utf-8")
    except Exception:
        # Fallback: treat as plain text (backward compat with old state files)
        return encoded


def load_state() -> dict:
    log.debug(f"load_state() from {STATE_FILE}")
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            # Deobfuscate token on read
            if "jira_token_b64" in data:
                data["jira_token"] = _deobfuscate_token(data.pop("jira_token_b64"))
            log.debug(f"  State loaded: {len(data)} keys")
            return data
        except json.JSONDecodeError as e:
            log.error(f"  Failed to parse state file: {e}")
            return {}
    log.debug("  State file does not exist")
    return {}


def save_state(state: dict):
    log.debug(f"save_state() keys={list(state.keys())}")
    # Obfuscate token before writing
    to_save = dict(state)
    if "jira_token" in to_save:
        to_save["jira_token_b64"] = _obfuscate_token(to_save.pop("jira_token"))
    STATE_FILE.write_text(json.dumps(to_save, indent=2, default=str))
    # Restrict file permissions to owner only (0600)
    STATE_FILE.chmod(stat.S_IRUSR | stat.S_IWUSR)
    log.debug(f"  State saved to {STATE_FILE}")
    _add_history(state)


def _add_history(state: dict):
    history = load_history()
    # Remove token from history entries (security)
    state_for_history = {k: v for k, v in state.items() if k != "jira_token"}
    history.append({"timestamp": datetime.now().isoformat(), "state": state_for_history})
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
