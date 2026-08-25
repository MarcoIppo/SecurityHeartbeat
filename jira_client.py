"""Jira interaction module."""
import re
import logging
import time
from jira import JIRA
from config import JIRA_URL, JIRA_USER, JIRA_TOKEN, JIRA_PROJECT, EPIC_NAME_PATTERN, EPIC_ISSUETYPE, STORY_ISSUETYPE, MAX_EPICS, BOARD_ID

log = logging.getLogger("secheartbeat.jira")


_ac_field_id = None  # cached acceptance criteria field id
_sprint_field_id = "customfield_11910"  # Sprint custom field
_story_points_field_id = None  # cached story points field id


def _sanitize_jql_value(value: str) -> str:
    """Sanitize a value for safe inclusion in JQL queries.

    Removes characters that could alter JQL semantics and validates format.
    """
    if not value:
        return ""
    # Remove JQL operators and dangerous characters
    sanitized = re.sub(r'[;|&\\\n\r]', '', str(value))
    # Remove JQL keywords that could form injections
    sanitized = re.sub(r'\b(OR|AND|NOT|ORDER BY|UNION)\b', '', sanitized, flags=re.IGNORECASE)
    return sanitized.strip()


def _validate_issue_key(key: str) -> str:
    """Validate and return a Jira issue key (e.g. TORF-12345)."""
    key = str(key).strip()
    if not re.match(r'^[A-Z][A-Z0-9]+-\d+$', key):
        raise ValueError(f"Invalid Jira issue key format: '{key}'")
    return key


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
    """Create a fresh JIRA client using current config values."""
    from config import JIRA_URL, JIRA_TOKEN
    log.debug(f"Creating JIRA client for server: {JIRA_URL}")
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


def _get_story_points_field(client) -> str:
    """Find the Story Points custom field ID."""
    global _story_points_field_id
    if _story_points_field_id:
        return _story_points_field_id
    for field in client.fields():
        if field["name"].lower() == "story points":
            _story_points_field_id = field["id"]
            return _story_points_field_id
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
    summary_clauses = " AND ".join(
        f'summary ~ "{_sanitize_jql_value(kw)}"' for kw in keywords
    )
    project = _sanitize_jql_value(JIRA_PROJECT)
    jql = (
        f'project = "{project}" AND issuetype = "Epic" '
        f'AND {summary_clauses} '
        f'ORDER BY created DESC'
    )
    log.debug(f"get_open_epics() JQL: {jql}")
    t0 = time.time()
    issues = client.search_issues(jql, maxResults=MAX_EPICS, fields="summary,description,status,resolution")
    elapsed = time.time() - t0
    log.info(f"get_open_epics(): found {len(issues)} epics in {elapsed:.2f}s")
    return [
        {"key": str(i.key), "summary": i.fields.summary,
         "description": i.fields.description or "",
         "status": i.fields.status.name,
         "resolution": i.fields.resolution.name if i.fields.resolution else "Unresolved"}
        for i in issues
    ]


def get_epic_stories(epic_key: str) -> list[dict]:
    """Get user stories linked to an epic, including acceptance criteria."""
    epic_key = _validate_issue_key(epic_key)
    log.debug(f"get_epic_stories({epic_key})")
    t0 = time.time()
    client = get_client()
    ac_field = _get_ac_field(client)
    sp_field = _get_story_points_field(client)
    epic_link_field = _get_epic_link_field(client)
    jql = f'"Epic Link" = "{epic_key}" AND issuetype = "{STORY_ISSUETYPE}" ORDER BY key ASC'
    log.debug(f"  JQL: {jql}")
    issues = client.search_issues(jql, maxResults=100)
    results = []
    for i in issues:
        ac = ""
        if ac_field:
            ac = getattr(i.fields, ac_field, "") or ""
        # Story points
        story_points = ""
        if sp_field:
            sp_val = getattr(i.fields, sp_field, None)
            if sp_val is not None:
                story_points = str(int(sp_val)) if sp_val == int(sp_val) else str(sp_val)
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
            "story_points": story_points,
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
    elapsed = time.time() - t0
    log.info(f"get_epic_stories({epic_key}): {len(results)} stories in {elapsed:.2f}s")
    return results


def get_historical_stories() -> list[dict]:
    """Get stories from closed heartbeat epics."""
    log.debug("get_historical_stories()")
    t0 = time.time()
    client = get_client()
    ac_field = _get_ac_field(client)
    project = _sanitize_jql_value(JIRA_PROJECT)
    epic_type = _sanitize_jql_value(EPIC_ISSUETYPE)
    pattern = _sanitize_jql_value(EPIC_NAME_PATTERN)
    epics = client.search_issues(
        f'project = "{project}" AND issuetype = "{epic_type}" '
        f'AND summary ~ "{pattern}" AND status = "Closed" '
        f'ORDER BY created DESC',
        maxResults=5
    )
    stories = []
    seen = set()
    for epic in epics:
        epic_k = _validate_issue_key(str(epic.key))
        story_type = _sanitize_jql_value(STORY_ISSUETYPE)
        jql = f'"Epic Link" = "{epic_k}" AND issuetype = "{story_type}"'
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
    elapsed = time.time() - t0
    log.info(f"get_historical_stories(): {len(stories)} stories in {elapsed:.2f}s")
    return stories


def get_board_sprints() -> list[str]:
    """Get active and future sprint names from configured board, sorted alphanumerically.

    Filters out stale sprints (year < current year - 1) that were never closed.
    """
    log.debug(f"get_board_sprints() board_id={BOARD_ID}")
    t0 = time.time()
    client = get_client()
    try:
        sprints = client.sprints(BOARD_ID, state="active,future")
        names = [s.name for s in sprints]
        log.debug(f"  Raw sprints from board: {len(names)}")
        # Filter out stale sprints: keep only those with year >= (current - 1)
        import re
        from datetime import datetime
        current_year_short = int(datetime.now().strftime("%y"))  # e.g. 26
        min_year = current_year_short - 1  # e.g. 25
        filtered = []
        for name in names:
            # Try to extract year from sprint name (e.g. "Hydra 25.10" → 25)
            match = re.search(r'\b(\d{2})\.\d{2}\b', name)
            if match:
                year = int(match.group(1))
                if year >= min_year:
                    filtered.append(name)
            else:
                # No recognizable pattern — keep it
                filtered.append(name)
        elapsed = time.time() - t0
        log.info(f"get_board_sprints(): {len(filtered)} sprints (filtered from {len(names)}) in {elapsed:.2f}s")
        return sorted(filtered)
    except Exception as e:
        elapsed = time.time() - t0
        log.error(f"get_board_sprints() FAILED in {elapsed:.2f}s: {e}")
        return []


def get_board_sprints_details() -> list[dict]:
    """Get active and future sprints with name, startDate, endDate."""
    log.debug(f"get_board_sprints_details() board_id={BOARD_ID}")
    client = get_client()
    try:
        sprints = client.sprints(BOARD_ID, state="active,future")
        result = []
        for s in sprints:
            result.append({
                "name": s.name,
                "id": s.id,
                "startDate": getattr(s, "startDate", ""),
                "endDate": getattr(s, "endDate", ""),
            })
        log.debug(f"  Returned {len(result)} sprint details")
        return result
    except Exception as e:
        log.error(f"get_board_sprints_details() FAILED: {e}")
        return []


def create_story(epic_key: str, summary: str, description: str,
                 sprint_name: str = "", labels: list = None,
                 assignee_key: str = "", components: list = None,
                 priority: str = "", acceptance_criteria: str = "",
                 tag_generated: bool = False) -> str:
    """Create a user story linked to the epic.

    Args:
        tag_generated: If True, appends a 'tool-generated' label and a
            footer line to the description indicating automated creation.
    """
    from config import VERSION
    epic_key = _validate_issue_key(epic_key)
    log.info(f"create_story() epic={epic_key}, summary='{summary[:60]}...'")
    log.debug(f"  sprint={sprint_name}, labels={labels}, assignee={assignee_key}, "
              f"components={components}, priority={priority}, tag_generated={tag_generated}")
    t0 = time.time()
    client = get_client()

    # --- Apply generated-by tagging ---
    if tag_generated:
        if labels is None:
            labels = []
        if "tool-generated" not in labels:
            labels.append("tool-generated")
        footer = (
            f"\n\n----\n"
            f"{{color:#999999}}_Generated by Security Heartbeat US Generator (v{VERSION})_{{color}}"
        )
        description = (description or "") + footer

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
    issue_key = str(issue.key)
    elapsed = time.time() - t0
    log.info(f"  Created {issue_key} in {elapsed:.2f}s")

    if sprint_name:
        _move_to_sprint(client, issue_key, sprint_name)

    return issue_key


def _get_epic_link_field(client) -> str:
    for field in client.fields():
        if field["name"] == "Epic Link":
            return field["id"]
    return "customfield_11911"


def update_epic_link(issue_key: str, epic_key: str):
    """Update the Epic Link field on an existing story."""
    issue_key = _validate_issue_key(issue_key)
    epic_key = _validate_issue_key(epic_key)
    log.info(f"update_epic_link() {issue_key} -> epic {epic_key}")
    client = get_client()
    epic_field = _get_epic_link_field(client)
    issue = client.issue(issue_key)
    issue.update(fields={epic_field: epic_key})
    log.debug(f"  Epic link updated successfully")


def update_story(issue_key: str, summary: str, description: str,
                 sprint_name: str = "", labels: list = None,
                 assignee_key: str = "", components: list = None,
                 priority: str = "", acceptance_criteria: str = ""):
    """Update an existing user story with new field values."""
    issue_key = _validate_issue_key(issue_key)
    log.info(f"update_story() key={issue_key}, summary='{summary[:60]}...'")
    log.debug(f"  sprint={sprint_name}, labels={labels}, assignee={assignee_key}, "
              f"components={components}, priority={priority}")
    t0 = time.time()
    client = get_client()
    fields = {
        "summary": summary,
        "description": description,
    }
    if acceptance_criteria is not None:
        ac_field = _get_ac_field(client)
        if ac_field:
            fields[ac_field] = acceptance_criteria
    if labels is not None:
        fields["labels"] = labels
    if assignee_key:
        fields["assignee"] = {"name": assignee_key}
    if components is not None:
        fields["components"] = [{"name": c} for c in components]
    if priority:
        fields["priority"] = {"name": priority}

    issue = client.issue(issue_key)
    issue.update(fields=fields)
    elapsed = time.time() - t0
    log.info(f"  Updated {issue_key} in {elapsed:.2f}s")

    # Move to sprint if specified
    if sprint_name:
        _move_to_sprint(client, issue_key, sprint_name)


def _move_to_sprint(client, issue_key: str, sprint_name: str):
    """Move issue to the sprint with exact name match."""
    log.debug(f"_move_to_sprint({issue_key}, '{sprint_name}')")
    try:
        sprints = client.sprints(BOARD_ID, state="active,future")
        for sprint in sprints:
            if sprint.name.strip().lower() == sprint_name.strip().lower():
                client.add_issues_to_sprint(sprint.id, [issue_key])
                log.info(f"  Moved {issue_key} to sprint '{sprint.name}' (id={sprint.id})")
                return
        log.warning(f"Sprint not found (exact match): '{sprint_name}'. "
                    f"Available: {[s.name for s in sprints]}")
    except Exception as e:
        log.error(f"Failed to move {issue_key} to sprint '{sprint_name}': {e}")
