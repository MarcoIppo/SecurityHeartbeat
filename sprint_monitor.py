#!/usr/bin/env python3
"""Hydra Sprint Monitor — Daily check of Jira issues in active sprint.

Sends email reminders to team members based on issue status:
- Unassigned: notify entire team
- Open (every 2 days): remind assignee to move to In Progress
- In Progress (every 2 days): remind assignee to add progress comment
- Blocked/On Hold (every 3 days): remind assignee to check blockers

Scheduled via cron: 0 8 * * * /path/to/.venv/bin/python3 /path/to/sprint_monitor.py
"""
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, date
from pathlib import Path
from jira import JIRA

# Load config
CONFIG_FILE = Path(__file__).parent / "app_config.json"
STATE_FILE = Path.home() / ".secheartbeat_state.json"
MONITOR_STATE = Path.home() / ".sprint_monitor_state.json"

config = json.loads(CONFIG_FILE.read_text())
state = json.loads(STATE_FILE.read_text())

JIRA_URL = config["jira_url"]
TOKEN = state.get("jira_token", "")
BOARD_ID = config["board_id"]
TEAM_NAME = config["team_name"]

# Email settings
SMTP_SERVER = "smtp.internal.ericsson.com"
SMTP_PORT = 25
FROM_EMAIL = "hydra-sprint-monitor@ericsson.com"
TEAM_DL = "PDLENMHYDR@pdl.internal.ericsson.com"

# Team email mapping
TEAM_EMAILS = {
    "EALBGIU": "alberto.giulianino@ericsson.com",
    "EALDRAV": "aldo.ravaglia@ericsson.com",
    "EMARCBO": "marco.bonardi@ericsson.com",
    "EMARIPP": "marco.ippolito@ericsson.com",
    "EPAOBON": "paola.bona@ericsson.com",
    "ESTEDEL": "stefano.delsonno@ericsson.com",
}


def get_client():
    return JIRA(server=JIRA_URL, token_auth=TOKEN)


def load_monitor_state():
    if MONITOR_STATE.exists():
        try:
            return json.loads(MONITOR_STATE.read_text())
        except json.JSONDecodeError:
            return {}
    return {}


def save_monitor_state(state):
    MONITOR_STATE.write_text(json.dumps(state, indent=2))


def get_active_sprint_issues(client):
    """Get all issues in the active sprint."""
    sprints = client.sprints(BOARD_ID, state="active")
    if not sprints:
        return [], ""
    sprint = sprints[0]
    jql = f'sprint = {sprint.id} AND issuetype = Story ORDER BY status ASC'
    issues = client.search_issues(jql, maxResults=100)
    return issues, sprint.name


def send_email(to, subject, body):
    """Send email via SMTP."""
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = FROM_EMAIL
    msg["To"] = to
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, [to], msg.as_string())
        print(f"  Sent to {to}")
    except Exception as e:
        print(f"  FAILED to {to}: {e}")


def should_notify(issue_key, category, interval_days, monitor_state):
    """Check if enough days have passed since last notification."""
    key = f"{issue_key}_{category}"
    last = monitor_state.get(key)
    if not last:
        return True
    last_date = date.fromisoformat(last)
    return (date.today() - last_date).days >= interval_days


def mark_notified(issue_key, category, monitor_state):
    """Record that a notification was sent."""
    key = f"{issue_key}_{category}"
    monitor_state[key] = date.today().isoformat()


def main():
    print(f"[{datetime.now().isoformat()}] Sprint Monitor starting...")
    client = get_client()
    issues, sprint_name = get_active_sprint_issues(client)

    if not issues:
        print("No active sprint or no issues found.")
        return

    print(f"Sprint: {sprint_name} — {len(issues)} issues")

    monitor_state = load_monitor_state()
    unassigned = []

    for issue in issues:
        key = str(issue.key)
        summary = issue.fields.summary
        status = issue.fields.status.name.lower()
        assignee = issue.fields.assignee
        assignee_name = getattr(assignee, "name", "").upper() if assignee else ""
        assignee_display = assignee.displayName if assignee else "Unassigned"

        print(f"  {key} [{status}] → {assignee_display}")

        # Unassigned
        if not assignee:
            unassigned.append(f"  • {key}: {summary}")
            continue

        email = TEAM_EMAILS.get(assignee_name, "")
        if not email:
            continue

        # Open — every 2 days
        if status in ("open", "backlog", "reopened"):
            if should_notify(key, "open", 2, monitor_state):
                send_email(email,
                    f"[{TEAM_NAME}] Reminder: {key} is still Open",
                    f"Hi {assignee_display},\n\n"
                    f"The story {key} \"{summary}\" in sprint {sprint_name} "
                    f"is still in Open status.\n\n"
                    f"Please move it to In Progress when you start working on it.\n\n"
                    f"Link: {JIRA_URL}/browse/{key}\n\n"
                    f"— Hydra Sprint Monitor")
                mark_notified(key, "open", monitor_state)

        # In Progress — every 2 days
        elif status in ("in progress", "in development"):
            if should_notify(key, "progress", 2, monitor_state):
                send_email(email,
                    f"[{TEAM_NAME}] Reminder: {key} progress update",
                    f"Hi {assignee_display},\n\n"
                    f"The story {key} \"{summary}\" is In Progress.\n\n"
                    f"Please add a comment with your progress update.\n\n"
                    f"Link: {JIRA_URL}/browse/{key}\n\n"
                    f"— Hydra Sprint Monitor")
                mark_notified(key, "progress", monitor_state)

        # Blocked/On Hold — every 3 days
        elif status in ("blocked", "on hold", "impediment"):
            if should_notify(key, "blocked", 3, monitor_state):
                send_email(email,
                    f"[{TEAM_NAME}] Reminder: {key} is Blocked",
                    f"Hi {assignee_display},\n\n"
                    f"The story {key} \"{summary}\" is currently Blocked/On Hold.\n\n"
                    f"Please check if the blocking conditions still persist "
                    f"and update the issue accordingly.\n\n"
                    f"Link: {JIRA_URL}/browse/{key}\n\n"
                    f"— Hydra Sprint Monitor")
                mark_notified(key, "blocked", monitor_state)

    # Send unassigned summary to team
    if unassigned:
        body = (
            f"Hi Team,\n\n"
            f"The following stories in sprint {sprint_name} are *unassigned*:\n\n"
            + "\n".join(unassigned) +
            f"\n\nPlease pick them up or discuss during standup.\n\n"
            f"— Hydra Sprint Monitor"
        )
        send_email(TEAM_DL,
            f"[{TEAM_NAME}] {len(unassigned)} unassigned stories in {sprint_name}",
            body)

    save_monitor_state(monitor_state)
    print("Done.")


if __name__ == "__main__":
    main()
