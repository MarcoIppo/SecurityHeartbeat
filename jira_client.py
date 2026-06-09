"""Jira interaction module."""
from jira import JIRA
from config import JIRA_URL, JIRA_USER, JIRA_TOKEN, JIRA_PROJECT, EPIC_NAME_PATTERN, EPIC_ISSUETYPE, STORY_ISSUETYPE, MAX_EPICS, BOARD_ID


_ac_field_id = None  # cached acceptance criteria field id
_sprint_field_id = "customfield_11910"  # Sprint custom field


def _parse_sprint_name(sprint_val) -> str:
    """Extract sprint name from Jira sprint field (string or object)."""
    if not sprint_val:
        return ""
    if isinstance(sprint_val, list):
        sprint_val = sprint_val[-1] if sprint_val else ""
    if hasattr(sprint_val, "name"):
        return sprint_val.name or ""
    s = str(sprint_val)
    # Parse "name=Hydra 26.32," from Java serialized string
    if "name=" in s:
        start = s.index("name=") + 5
        end = s.index(",", start)
        return s[start:end]
    return ""


def get_client() -> JIRA:
    return JIRA(server=JIRA_URL, token_auth=JIRA_TOKEN)


def _get_ac_field(client) -> str:
    """Find the Acceptance Criteria custom field ID."""
    global _ac_field_id
    if _ac_field_id:
        return _ac_field_id
    for field in client.fields():
        if "acceptance" in field["name"].lower() and "criteria" in field["name"].lower():
            _ac_field_id = field["id"]
            return _ac_field_id
    return ""


def _parse_summary_keywords(pattern: str) -> list[str]:
    """Parse summary_contains into keyword list.

    Supports comma-separated words and quoted phrases:
      "Security,Heartbeat" -> ['Security', 'Heartbeat']
      '"recurrent test",Security' -> ['recurrent test', 'Security']
    """
    import re
    tokens = re.findall(r'"([^"]+)"|([^,]+)', pattern)
    return [quoted or unquoted.strip() for quoted, unquoted in tokens if quoted or unquoted.strip()]


def get_open_epics() -> list[dict]:
    """Get all heartbeat epics (open and closed) with status."""
    client = get_client()
    keywords = _parse_summary_keywords(EPIC_NAME_PATTERN)
    summary_clauses = " AND ".join(f'summary ~ "{kw}"' for kw in keywords)
    jql = (
        f'project = {JIRA_PROJECT} AND issuetype = Epic '
        f'AND {summary_clauses} '
        f'ORDER BY created DESC'
    )
    issues = client.search_issues(jql, maxResults=MAX_EPICS, fields="summary,description,status,resolution")
    return [
        {"key": str(i.key), "summary": i.fields.summary,
         "description": i.fields.description or "",
         "status": i.fields.status.name,
         "resolution": i.fields.resolution.name if i.fields.resolution else "Unresolved"}
        for i in issues
    ]


def get_epic_stories(epic_key: str) -> list[dict]:
    """Get user stories linked to an epic, including acceptance criteria."""
    client = get_client()
    ac_field = _get_ac_field(client)
    epic_link_field = _get_epic_link_field(client)
    jql = f'"Epic Link" = {epic_key} AND issuetype = {STORY_ISSUETYPE} ORDER BY key ASC'
    issues = client.search_issues(jql, maxResults=100)
    results = []
    for i in issues:
        ac = ""
        if ac_field:
            ac = getattr(i.fields, ac_field, "") or ""
        # Get sprint name
        sprint_raw = getattr(i.fields, _sprint_field_id, None)
        sprint_name = _parse_sprint_name(sprint_raw)
        # Assignee
        assignee_name = ""
        assignee_key = ""
        if i.fields.assignee:
            assignee_name = i.fields.assignee.displayName
            assignee_key = getattr(i.fields.assignee, "name", "") or getattr(i.fields.assignee, "key", "")
        # Components
        components = [c.name for c in (i.fields.components or [])]
        # Priority
        priority = i.fields.priority.name if i.fields.priority else ""
        # Epic link
        current_epic = getattr(i.fields, epic_link_field, "") or ""
        results.append({
            "key": str(i.key), "summary": i.fields.summary,
            "description": i.fields.description or "",
            "acceptance_criteria": ac,
            "sprint": sprint_name,
            "labels": i.fields.labels or [],
            "status": i.fields.status.name,
            "resolution": i.fields.resolution.name if i.fields.resolution else "Unresolved",
            "assignee": assignee_name,
            "assignee_key": assignee_key,
            "components": components,
            "priority": priority,
            "epic_link": current_epic,
        })
    return results


def get_historical_stories() -> list[dict]:
    """Get stories from closed heartbeat epics."""
    client = get_client()
    ac_field = _get_ac_field(client)
    epics = client.search_issues(
        f'project = {JIRA_PROJECT} AND issuetype = {EPIC_ISSUETYPE} '
        f'AND summary ~ "{EPIC_NAME_PATTERN}" AND status = Closed '
        f'ORDER BY created DESC',
        maxResults=5
    )
    stories = []
    seen = set()
    for epic in epics:
        jql = f'"Epic Link" = {epic.key} AND issuetype = {STORY_ISSUETYPE}'
        for i in client.search_issues(jql, maxResults=50):
            if i.fields.summary not in seen:
                seen.add(i.fields.summary)
                ac = ""
                if ac_field:
                    ac = getattr(i.fields, ac_field, "") or ""
                stories.append({
                    "key": str(i.key), "summary": i.fields.summary,
                    "description": i.fields.description or "",
                    "acceptance_criteria": ac
                })
    return stories


def get_board_sprints() -> list[str]:
    """Get active and future sprint names from configured board."""
    client = get_client()
    try:
        sprints = client.sprints(BOARD_ID, state="active,future")
        return [s.name for s in sprints]
    except Exception:
        return []


def create_story(epic_key: str, summary: str, description: str,
                 sprint_name: str = "", labels: list = None,
                 assignee_key: str = "", components: list = None,
                 priority: str = "", acceptance_criteria: str = "") -> str:
    """Create a user story linked to the epic."""
    client = get_client()
    fields = {
        "project": {"key": JIRA_PROJECT},
        "issuetype": {"name": STORY_ISSUETYPE},
        "summary": summary,
        "description": description,
    }
    if acceptance_criteria:
        ac_field = _get_ac_field(client)
        if ac_field:
            fields[ac_field] = acceptance_criteria
    if labels:
        fields["labels"] = labels
    if assignee_key:
        fields["assignee"] = {"name": assignee_key}
    if components:
        fields["components"] = [{"name": c} for c in components]
    if priority:
        fields["priority"] = {"name": priority}
    epic_field = _get_epic_link_field(client)
    if epic_field:
        fields[epic_field] = epic_key

    issue = client.create_issue(fields=fields)

    if sprint_name:
        _move_to_sprint(client, str(issue.key), sprint_name)

    return str(issue.key)


def _get_epic_link_field(client) -> str:
    for field in client.fields():
        if field["name"] == "Epic Link":
            return field["id"]
    return "customfield_11911"


def update_epic_link(issue_key: str, epic_key: str):
    """Update the Epic Link field on an existing story."""
    client = get_client()
    epic_field = _get_epic_link_field(client)
    issue = client.issue(issue_key)
    issue.update(fields={epic_field: epic_key})


def _move_to_sprint(client, issue_key: str, sprint_name: str):
    try:
        sprints = client.sprints(BOARD_ID, state="active,future")
        for sprint in sprints:
            if sprint_name.lower() in sprint.name.lower():
                client.add_issues_to_sprint(sprint.id, [issue_key])
                return
    except Exception:
        pass
