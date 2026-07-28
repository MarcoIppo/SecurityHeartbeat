# Security Heartbeat US Generator

**Version 1.3.5**

A Python/tkinter desktop application to automate the creation and management of Jira User Stories for the Security Heartbeat recurrent test activities in ENM/cENM releases.

---

## Purpose

For every ENM/cENM release, the Security Heartbeat team manually creates a set of User Stories, grouped under Epics and distributed across several sprints. This work is repetitive, time-consuming, and prone to inconsistencies in naming, structure, and assignment.

This application automates the process by:
- Connecting to Jira and loading existing Heartbeat Epics and their associated stories
- Providing a GUI to review, edit, translate, and create new User Stories in batch
- Ensuring consistent structure, labels, sprint mapping, and field population

---

## Features

### Epic & Story Management
- Load the latest N Security Heartbeat epics from Jira (configurable)
- Auto-select the most recent epic and display its User Stories
- View story details: title, description, acceptance criteria, sprint, labels, assignee, components, priority
- Load historical stories from previous epics as templates for new ones

### Editing
- Full in-place editing of all story fields
- Sprint selection via dropdown populated from the team board
- Editable labels (default: sprint number + team name)
- Editable assignee, components, and priority
- Acceptance criteria as a separate field

### Translation
- IT→EN translation powered by Google Translate
- Per-field translation with preview popup and Confirm/Skip buttons

### Batch Operations
- **Create User Stories** — push all stories to Jira linked to the selected epic
- **Save User Stories** — export to JSON file for review before creation

### Configuration
All project-specific settings are in a single `app_config.json` file:
- Jira URL, project key, issue types
- Summary pattern for epic matching
- Maximum epics to load
- Team name and board ID for sprint mapping

### UX
- Persistent state (token saved between sessions)
- Tooltips on all fields
- Jira markup syntax help (popup with formatting reference)
- Ericsson brand color scheme with Hydra team logos
- Status bar with connection feedback

---

## Setup

### Prerequisites
- Python 3.10+
- Access to Ericsson Jira (eteamproject-alpha)
- A Personal Access Token (PAT) from Jira

### Installation

```bash
git clone https://github.com/MarcoIppo/SecurityHeartbeat.git
cd SecurityHeartbeat
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Configuration

Edit `app_config.json`:

```json
{
  "jira_url": "https://eteamproject-alpha.internal.ericsson.com",
  "project": "TORF",
  "issuetype": "Epic",
  "summary_contains": "Security heartbeat recurrent test activities for",
  "story_issuetype": "Story",
  "max_epics": 5,
  "team_name": "Hydra",
  "board_id": 38770
}
```

### Run

```bash
./run.sh          # English UI
./run.sh --ita    # Italian UI
```

On first launch, enter your Jira PAT in the credentials bar at the bottom and click **Connect**.

---

## Project Structure

```
├── app.py              # Main GUI application (tkinter)
├── config.py           # Configuration loader, persistence, constants
├── jira_client.py      # Jira API interactions (Bearer token auth)
├── translator.py       # IT→EN translation (Google Translate)
├── i18n.py             # UI strings (EN/IT)
├── app_config.json     # Application configuration
├── assets/             # Logos (Hydra, Ericsson)
├── run.sh              # Launch script
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## Roadmap

- [ ] Update existing stories (modify fields on already-created issues)
- [ ] Bulk assignee management
- [ ] Template system (save/load story templates)
- [ ] Acceptance criteria as a dedicated Jira custom field
- [ ] Integration with CI/CD pipeline for automated story creation per drop
- [ ] Offline mode with full JSON import/export

---

## Related

- **Jira Epic**: Security Heartbeat recurrent test activities
- **Board**: [Hydra Board](https://eteamproject-alpha.internal.ericsson.com/secure/RapidBoard.jspa?rapidView=38770)
- **Reference Issue**: [TORF-907685](https://eteamproject-alpha.internal.ericsson.com/browse/TORF-907685)

---

## License

Internal Ericsson tool — Hydra Team.
