"""
Test Criticità #4 — importlib.reload(jira_client) fragile

PRIMA del fix: _init_jira usava importlib.reload() per forzare il reload del modulo.
DOPO il fix: get_client() legge sempre le credenziali correnti da config.

Include test di non-regressione per verificare che get_client usi i valori aggiornati.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import patch, MagicMock


class TestNoReload:
    """Verifica che importlib.reload non sia più usato."""

    def test_no_importlib_reload_in_app(self):
        """DOPO il fix: app.py non deve contenere importlib.reload."""
        app_path = Path(__file__).parent.parent / "app.py"
        content = app_path.read_text()
        assert "importlib.reload" not in content, \
            "FAIL: importlib.reload ancora presente in app.py"

    def test_no_importlib_import_in_app(self):
        """DOPO il fix: app.py non deve importare importlib (non più necessario)."""
        app_path = Path(__file__).parent.parent / "app.py"
        content = app_path.read_text()
        assert "import importlib" not in content, \
            "FAIL: 'import importlib' ancora presente in app.py"


class TestGetClientFreshConfig:
    """Verifica che get_client() legga sempre i valori correnti di config."""

    def test_get_client_reads_current_config(self):
        """DOPO il fix: get_client usa i valori correnti, non quelli al momento dell'import."""
        import config

        # Simula cambio credenziali a runtime
        original_url = config.JIRA_URL
        original_token = config.JIRA_TOKEN

        config.JIRA_URL = "https://new-server.example.com"
        config.JIRA_TOKEN = "new_token_abc"

        try:
            # Mock JIRA constructor to capture what gets passed
            with patch("jira_client.JIRA") as mock_jira:
                from jira_client import get_client
                get_client()
                mock_jira.assert_called_once_with(
                    server="https://new-server.example.com",
                    token_auth="new_token_abc"
                )
        finally:
            # Restore
            config.JIRA_URL = original_url
            config.JIRA_TOKEN = original_token

    def test_get_client_uses_updated_token_after_reconnect(self):
        """Simulazione: utente cambia token → get_client usa il nuovo."""
        import config

        original_token = config.JIRA_TOKEN
        config.JIRA_TOKEN = "first_token"

        try:
            with patch("jira_client.JIRA") as mock_jira:
                from jira_client import get_client
                get_client()
                first_call = mock_jira.call_args

            config.JIRA_TOKEN = "second_token"

            with patch("jira_client.JIRA") as mock_jira:
                from jira_client import get_client
                get_client()
                second_call = mock_jira.call_args

            assert first_call[1]["token_auth"] == "first_token"
            assert second_call[1]["token_auth"] == "second_token"
        finally:
            config.JIRA_TOKEN = original_token


class TestNonRegressione:
    """Verifica che la logica di connessione funzioni ancora."""

    def test_init_jira_sets_config_values(self):
        """_init_jira aggiorna config.JIRA_URL e config.JIRA_TOKEN."""
        import config
        original_url = config.JIRA_URL
        original_token = config.JIRA_TOKEN

        try:
            config.JIRA_URL = ""
            config.JIRA_TOKEN = ""

            # _init_jira should update config values
            from app import _init_jira
            with patch("jira.JIRA") as mock_jira:
                mock_client = MagicMock()
                mock_jira.return_value = mock_client
                result = _init_jira("https://test.com", "", "tok123")

            assert config.JIRA_URL == "https://test.com"
            assert config.JIRA_TOKEN == "tok123"
            assert result is True
        finally:
            config.JIRA_URL = original_url
            config.JIRA_TOKEN = original_token

    def test_init_jira_returns_false_without_credentials(self):
        """Senza credenziali, _init_jira restituisce False."""
        from app import _init_jira
        assert _init_jira("", "", "") is False
        assert _init_jira("https://x.com", "", "") is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
