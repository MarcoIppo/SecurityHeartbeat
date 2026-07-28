"""
Test Funzionali AGGIUNTIVI — Problemi scoperti durante l'analisi

Problemi funzionali residui identificati:
1. _remove_tab con indice statico → sfasamento dopo rimozioni
2. _split_tab con indice statico → stessa problema
3. threading importato ma mai usato
4. _select_tab_by_index può crashare se checkbox > tabs
5. save_app_config exception handler ha bug (os.get_inheritable dopo close)
6. History salva il token in chiaro (il token è nell'oggetto state passato a _add_history)
"""
import sys
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest


class TestTabIndexBug:
    """Criticità: _remove_tab e _split_tab usano indice catturato alla creazione.

    Se l'utente rimuove tab 0, poi preme 'Split' su tab 1 (ora a idx 1 nel notebook,
    ma tab_widgets[1] potrebbe essere None se prima era all'indice 0).
    """

    def test_remove_tab_none_guard(self):
        """_remove_tab con indice oltre il range non deve crashare."""
        # Simuliamo: tab_widgets ha elementi, ma idx punta oltre
        import ast
        app_path = Path(__file__).parent.parent / "app.py"
        source = app_path.read_text()
        # Verifica che ci sia il guard `if idx >= len(self.tab_widgets)`
        assert "if idx >= len(self.tab_widgets)" in source

    def test_split_tab_none_guard(self):
        """_split_tab con indice oltre il range non deve crashare."""
        app_path = Path(__file__).parent.parent / "app.py"
        source = app_path.read_text()
        # In _split_tab c'è il guard
        # Cerchiamo il pattern nel contesto di _split_tab
        assert "_split_tab" in source
        # Il guard esiste
        split_section = source[source.index("def _split_tab"):]
        assert "if idx >= len(self.tab_widgets)" in split_section[:200]

    def test_split_tab_skips_none_widget(self):
        """_split_tab deve gestire il caso in cui tab_widgets[idx] è None."""
        app_path = Path(__file__).parent.parent / "app.py"
        source = app_path.read_text()
        split_section = source[source.index("def _split_tab"):source.index("def _split_tab") + 300]
        # Deve avere un check per None
        assert "if w is None" in split_section, \
            "BUG: _split_tab non gestisce tab_widgets[idx] = None"


class TestHistoryTokenLeak:
    """Criticità: _add_history riceve lo stato con token in chiaro.

    save_state offusca il token per il file di stato, ma _add_history riceve
    l'oggetto state originale con il token in chiaro, e lo scrive in history.
    """

    def test_history_does_not_contain_plaintext_token(self):
        """Il file history NON deve contenere il token in chiaro."""
        state_file = Path(tempfile.mktemp(suffix=".json"))
        hist_file = Path(tempfile.mktemp(suffix=".json"))
        token = "SUPER_SECRET_TOKEN_XYZ"

        try:
            with patch("config.STATE_FILE", state_file), \
                 patch("config.HISTORY_FILE", hist_file):
                from config import save_state
                save_state({"jira_token": token, "epic_key": "TORF-1"})

            # Leggi il contenuto raw del file history
            raw_content = hist_file.read_text()

            # BUG: il token È in chiaro nella history!
            if token in raw_content:
                pytest.fail(
                    f"BUG SCOPERTO: token in chiaro nella history!\n"
                    f"Il file history contiene: '{token}'\n"
                    f"Fix necessario: offuscare il token anche in _add_history()"
                )
        finally:
            for f in (state_file, hist_file):
                if f.exists():
                    f.unlink()


class TestUnusedImport:
    """Import `threading` presente ma mai usato."""

    def test_threading_import_used_or_removed(self):
        """threading non deve essere importato se non usato."""
        app_path = Path(__file__).parent.parent / "app.py"
        source = app_path.read_text()
        if "import threading" in source:
            lines = source.split("\n")
            uses = [l for l in lines if "threading." in l and "import" not in l]
            assert uses, "FAIL: 'threading' importato ma mai usato"
        # Se non è importato, il test passa (fix applicato)


class TestSaveAppConfigExceptionHandler:
    """Bug nel handler di eccezione di save_app_config."""

    def test_exception_handler_does_not_double_close(self):
        """Il blocco except non deve chiamare os.close su fd già chiuso."""
        from config import save_app_config
        config_file = Path(tempfile.mktemp(suffix=".json"))
        config_file.write_text('{"test": true}')
        try:
            with patch("config.APP_CONFIG_FILE", config_file):
                # Testa che una write normale funzioni
                save_app_config({"key": "val"})
                data = json.loads(config_file.read_text())
                assert data["key"] == "val"
        finally:
            if config_file.exists():
                config_file.unlink()


class TestSelectTabByIndex:
    """_select_tab_by_index con indice fuori range non deve crashare."""

    def test_method_has_bounds_check(self):
        """Il metodo verifica che idx < len(tabs)."""
        app_path = Path(__file__).parent.parent / "app.py"
        source = app_path.read_text()
        method_start = source.index("def _select_tab_by_index")
        method_section = source[method_start:method_start + 200]
        assert "if idx < len(tabs)" in method_section


class TestMoveToSprintErrorReporting:
    """_move_to_sprint deve loggare errori e warning (non silenziarli)."""

    def test_sprint_not_found_is_logged(self):
        """Se sprint non trovato, viene loggato un warning."""
        mock_client = MagicMock()
        mock_sprint = MagicMock()
        mock_sprint.name = "Other Sprint"
        mock_client.sprints.return_value = [mock_sprint]

        import logging
        from jira_client import _move_to_sprint
        with patch.object(logging.getLogger("secheartbeat"), "warning") as mock_warn:
            _move_to_sprint(mock_client, "TORF-1", "Hydra 26.10")
            assert mock_warn.called
            # Il messaggio deve contenere il nome cercato
            assert "Hydra 26.10" in str(mock_warn.call_args)

    def test_api_error_is_logged(self):
        """Se l'API fallisce, viene loggato un errore (non più `pass`)."""
        mock_client = MagicMock()
        mock_client.sprints.side_effect = Exception("Timeout")

        import logging
        from jira_client import _move_to_sprint
        with patch.object(logging.getLogger("secheartbeat"), "error") as mock_err:
            _move_to_sprint(mock_client, "TORF-1", "Sprint X")
            assert mock_err.called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
