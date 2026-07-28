"""
Test Criticità #5 — Sprint matching fuzzy

PRIMA del fix: match con 'in' (substring) poteva assegnare sprint errato.
DOPO il fix: match esatto case-insensitive con warning se non trovato.

Include test di non-regressione per il match esatto.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, MagicMock


def _make_sprint(name, id_val):
    s = MagicMock()
    s.name = name
    s.id = id_val
    return s


class TestSprintMatching:
    """Verifica il match esatto degli sprint."""

    def test_exact_match_works(self):
        """DOPO il fix: match esatto funziona."""
        sprints = [_make_sprint("Hydra 26.3", 100), _make_sprint("Hydra 26.32", 101)]
        mock_client = MagicMock()
        mock_client.sprints.return_value = sprints

        from jira_client import _move_to_sprint
        _move_to_sprint(mock_client, "TORF-123", "Hydra 26.3")

        mock_client.add_issues_to_sprint.assert_called_once_with(100, ["TORF-123"])

    def test_no_false_positive_substring(self):
        """DOPO il fix: '26.3' NON matcha 'Hydra 26.32'."""
        sprints = [_make_sprint("Hydra 26.32", 101)]
        mock_client = MagicMock()
        mock_client.sprints.return_value = sprints

        from jira_client import _move_to_sprint
        _move_to_sprint(mock_client, "TORF-123", "26.3")

        # Non deve essere chiamato — nessun match esatto
        mock_client.add_issues_to_sprint.assert_not_called()

    def test_case_insensitive(self):
        """DOPO il fix: il match è case-insensitive."""
        sprints = [_make_sprint("Hydra 26.10", 200)]
        mock_client = MagicMock()
        mock_client.sprints.return_value = sprints

        from jira_client import _move_to_sprint
        _move_to_sprint(mock_client, "TORF-456", "hydra 26.10")

        mock_client.add_issues_to_sprint.assert_called_once_with(200, ["TORF-456"])

    def test_whitespace_tolerance(self):
        """DOPO il fix: whitespace attorno al nome viene trimmato."""
        sprints = [_make_sprint("Hydra 26.10", 200)]
        mock_client = MagicMock()
        mock_client.sprints.return_value = sprints

        from jira_client import _move_to_sprint
        _move_to_sprint(mock_client, "TORF-789", "  Hydra 26.10  ")

        mock_client.add_issues_to_sprint.assert_called_once_with(200, ["TORF-789"])

    def test_no_match_logs_warning(self):
        """DOPO il fix: se non trova lo sprint, logga un warning."""
        sprints = [_make_sprint("Hydra 26.10", 200)]
        mock_client = MagicMock()
        mock_client.sprints.return_value = sprints

        from jira_client import _move_to_sprint
        import logging
        with patch.object(logging.getLogger("secheartbeat"), "warning") as mock_warn:
            _move_to_sprint(mock_client, "TORF-1", "Nonexistent Sprint")
            mock_warn.assert_called_once()
            assert "Nonexistent Sprint" in mock_warn.call_args[0][0]


class TestNonRegressione:
    """Verifica che l'assegnazione sprint continui a funzionare."""

    def test_typical_hydra_sprint(self):
        """Sprint tipico del team Hydra funziona."""
        sprints = [
            _make_sprint("Hydra 26.09", 10),
            _make_sprint("Hydra 26.10", 11),
            _make_sprint("Hydra 26.11", 12),
        ]
        mock_client = MagicMock()
        mock_client.sprints.return_value = sprints

        from jira_client import _move_to_sprint
        _move_to_sprint(mock_client, "TORF-100", "Hydra 26.10")

        mock_client.add_issues_to_sprint.assert_called_once_with(11, ["TORF-100"])

    def test_api_error_handled_gracefully(self):
        """Errori API non causano crash."""
        mock_client = MagicMock()
        mock_client.sprints.side_effect = Exception("Network timeout")

        from jira_client import _move_to_sprint
        # Non deve sollevare eccezioni
        _move_to_sprint(mock_client, "TORF-1", "Sprint X")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
