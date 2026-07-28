"""
Test Criticità #2 — JQL Injection nelle query Jira

PRIMA del fix: valori utente inseriti direttamente nelle stringhe JQL senza escaping.
DOPO il fix: tutti i valori sono sanitizzati e le issue key validate con regex.

Include test di non-regressione per la costruzione corretta delle query.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from jira_client import _sanitize_jql_value, _validate_issue_key


class TestSanitizeJqlValue:
    """Verifica che i valori JQL vengano sanitizzati correttamente."""

    def test_normal_value_unchanged(self):
        """Valori normali non vengono alterati."""
        assert _sanitize_jql_value("TORF") == "TORF"
        assert _sanitize_jql_value("Security") == "Security"
        assert _sanitize_jql_value("Story") == "Story"

    def test_removes_or_injection(self):
        """DOPO il fix: operatore OR viene rimosso."""
        result = _sanitize_jql_value("TORF-123 OR project = SECRET")
        # "OR" as a standalone JQL operator is removed
        # Note: "OR" inside "TORF" is fine (word boundary match in regex)
        assert " OR " not in f" {result} "

    def test_removes_and_injection(self):
        """DOPO il fix: operatore AND viene rimosso."""
        result = _sanitize_jql_value("Epic AND status = Open")
        assert " AND " not in result

    def test_removes_semicolons(self):
        """DOPO il fix: punto e virgola rimosso (statement separator)."""
        result = _sanitize_jql_value("value; DROP TABLE")
        assert ";" not in result

    def test_removes_pipes(self):
        """DOPO il fix: pipe rimosso."""
        result = _sanitize_jql_value("value|other")
        assert "|" not in result

    def test_removes_newlines(self):
        """DOPO il fix: newlines rimosse (multi-line injection)."""
        result = _sanitize_jql_value("value\nOR secret = true")
        assert "\n" not in result

    def test_empty_value(self):
        """Valore vuoto restituisce stringa vuota."""
        assert _sanitize_jql_value("") == ""
        assert _sanitize_jql_value(None) == ""

    def test_preserves_spaces_in_phrases(self):
        """Spazi nelle frasi di ricerca sono preservati."""
        result = _sanitize_jql_value("Security heartbeat recurrent")
        assert result == "Security heartbeat recurrent"


class TestValidateIssueKey:
    """Verifica che le issue key vengano validate rigorosamente."""

    def test_valid_keys(self):
        """Key valide passano la validazione."""
        assert _validate_issue_key("TORF-123") == "TORF-123"
        assert _validate_issue_key("TORF-907685") == "TORF-907685"
        assert _validate_issue_key("AB-1") == "AB-1"

    def test_invalid_key_injection(self):
        """DOPO il fix: key con injection vengono rifiutate."""
        with pytest.raises(ValueError, match="Invalid Jira issue key"):
            _validate_issue_key("TORF-123 OR project = X")

    def test_invalid_key_no_dash(self):
        """Key senza trattino rifiutata."""
        with pytest.raises(ValueError, match="Invalid Jira issue key"):
            _validate_issue_key("TORF123")

    def test_invalid_key_lowercase(self):
        """Key con progetto minuscolo rifiutata."""
        with pytest.raises(ValueError, match="Invalid Jira issue key"):
            _validate_issue_key("torf-123")

    def test_invalid_key_empty(self):
        """Key vuota rifiutata."""
        with pytest.raises(ValueError, match="Invalid Jira issue key"):
            _validate_issue_key("")

    def test_invalid_key_special_chars(self):
        """Key con caratteri speciali rifiutata."""
        with pytest.raises(ValueError, match="Invalid Jira issue key"):
            _validate_issue_key("TORF-123; rm -rf /")

    def test_strips_whitespace(self):
        """Whitespace attorno alla key viene rimosso."""
        assert _validate_issue_key("  TORF-456  ") == "TORF-456"


class TestNonRegressione:
    """Verifica che le funzioni di sanitizzazione non rompano l'uso normale."""

    def test_project_key_torf(self):
        """Il progetto TORF passa la sanitizzazione."""
        assert _sanitize_jql_value("TORF") == "TORF"

    def test_story_issuetype(self):
        """Issue type 'Story' passa la sanitizzazione."""
        assert _sanitize_jql_value("Story") == "Story"

    def test_epic_issuetype(self):
        """Issue type 'Epic' passa la sanitizzazione."""
        assert _sanitize_jql_value("Epic") == "Epic"

    def test_summary_pattern_with_commas(self):
        """Pattern con virgole (usato per keyword split) funziona."""
        # Le virgole sono OK — il parsing delle keyword è a monte
        result = _sanitize_jql_value("Security heartbeat recurrent test activities for")
        assert "Security" in result
        assert "heartbeat" in result

    def test_typical_epic_key(self):
        """Epic key tipiche del progetto."""
        assert _validate_issue_key("TORF-898980") == "TORF-898980"
        assert _validate_issue_key("TORF-907685") == "TORF-907685"

    def test_team_name_in_summary(self):
        """Team name 'Hydra' nella summary non viene alterato."""
        assert _sanitize_jql_value("Hydra") == "Hydra"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
