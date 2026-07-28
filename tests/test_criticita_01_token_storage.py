"""
Test Criticità #1 — Token Jira salvato in chiaro su disco

PRIMA del fix: il token era scritto in plain text nel file di stato.
DOPO il fix: il token è offuscato in base64 e il file ha permessi 0600.

Include test di non-regressione per verificare che load/save state
continui a funzionare correttamente per tutti i campi.
"""
import json
import os
import stat
import tempfile
from pathlib import Path
from unittest.mock import patch

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


class TestTokenStorage:
    """Verifica che il token non sia salvato in chiaro."""

    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state_path = Path(self.tmp.name)

    def teardown_method(self):
        if self.state_path.exists():
            self.state_path.unlink()

    def _save_and_read_raw(self, state: dict) -> dict:
        """Save state and return raw JSON content from file."""
        with patch("config.STATE_FILE", self.state_path):
            from config import save_state
            save_state(state)
        return json.loads(self.state_path.read_text())

    # --- TEST: token NON presente in chiaro nel file ---

    def test_token_not_in_plaintext(self):
        """DOPO il fix: il token non deve apparire in chiaro nel file."""
        token = "MySecretJiraToken123!@#"
        raw = self._save_and_read_raw({"jira_token": token, "epic_key": "TORF-123"})

        # Il campo 'jira_token' non deve esistere nel file
        assert "jira_token" not in raw, \
            f"FAIL: 'jira_token' trovato in chiaro nel file! Contenuto: {raw}"

        # Il campo offuscato deve esistere
        assert "jira_token_b64" in raw, \
            "FAIL: campo 'jira_token_b64' non trovato nel file salvato"

        # Il valore offuscato NON deve essere uguale al token originale
        assert raw["jira_token_b64"] != token, \
            "FAIL: il valore salvato è identico al token originale (non offuscato)"

    # --- TEST: token decodificato correttamente in lettura ---

    def test_token_roundtrip(self):
        """DOPO il fix: save → load restituisce il token originale."""
        token = "Bearer_xyzABC123_special!chars"
        with patch("config.STATE_FILE", self.state_path):
            from config import save_state, load_state
            save_state({"jira_token": token})
            loaded = load_state()

        assert loaded.get("jira_token") == token, \
            f"FAIL: token letto '{loaded.get('jira_token')}' != atteso '{token}'"

    # --- TEST: permessi file 0600 ---

    def test_file_permissions_600(self):
        """DOPO il fix: il file di stato deve avere permessi 0600 (owner only)."""
        with patch("config.STATE_FILE", self.state_path):
            from config import save_state
            save_state({"jira_token": "test_token"})

        file_mode = oct(self.state_path.stat().st_mode & 0o777)
        assert file_mode == "0o600", \
            f"FAIL: permessi file = {file_mode}, atteso '0o600'"

    # --- TEST: backward compatibility con vecchi file (plain text) ---

    def test_backward_compat_old_plaintext_state(self):
        """Se il file ha ancora 'jira_token' in chiaro (vecchio formato),
        deve comunque essere letto correttamente."""
        old_state = {"jira_token": "old_plain_token", "epic_key": "TORF-100"}
        self.state_path.write_text(json.dumps(old_state))

        with patch("config.STATE_FILE", self.state_path):
            from config import load_state
            loaded = load_state()

        # Il campo jira_token deve essere preservato (backward compat)
        assert loaded.get("jira_token") == "old_plain_token"

    # --- TEST: token vuoto gestito correttamente ---

    def test_empty_token(self):
        """Token vuoto non deve causare errori."""
        with patch("config.STATE_FILE", self.state_path):
            from config import save_state, load_state
            save_state({"jira_token": "", "epic_key": "TORF-1"})
            loaded = load_state()

        assert loaded.get("jira_token") == ""


class TestNonRegressione:
    """Verifica che save/load state funzioni per tutti i campi (non solo token)."""

    def setup_method(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp.close()
        self.state_path = Path(self.tmp.name)
        # Also mock history file
        self.tmp_hist = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
        self.tmp_hist.close()
        self.hist_path = Path(self.tmp_hist.name)

    def teardown_method(self):
        for p in (self.state_path, self.hist_path):
            if p.exists():
                p.unlink()

    def test_all_fields_preserved(self):
        """Tutti i campi dello stato devono essere preservati nel roundtrip."""
        state = {
            "epic_key": "TORF-907685",
            "epic_idx": 2,
            "stories": [
                {"title": "Test Story", "description": "Desc", "sprint": "Hydra 26.10"}
            ],
            "jira_token": "PAT_abc123_XYZ",
        }
        with patch("config.STATE_FILE", self.state_path), \
             patch("config.HISTORY_FILE", self.hist_path):
            from config import save_state, load_state
            save_state(state)
            loaded = load_state()

        assert loaded["epic_key"] == "TORF-907685"
        assert loaded["epic_idx"] == 2
        assert loaded["stories"] == state["stories"]
        assert loaded["jira_token"] == "PAT_abc123_XYZ"

    def test_state_without_token(self):
        """Stato senza token deve funzionare senza errori."""
        state = {"epic_key": "TORF-100", "epic_idx": 0, "stories": []}
        with patch("config.STATE_FILE", self.state_path), \
             patch("config.HISTORY_FILE", self.hist_path):
            from config import save_state, load_state
            save_state(state)
            loaded = load_state()

        assert loaded["epic_key"] == "TORF-100"
        assert "jira_token" not in loaded

    def test_history_still_works(self):
        """La history deve continuare a registrare le entries."""
        with patch("config.STATE_FILE", self.state_path), \
             patch("config.HISTORY_FILE", self.hist_path):
            from config import save_state, load_history
            save_state({"jira_token": "tok1", "epic_key": "A"})
            save_state({"jira_token": "tok2", "epic_key": "B"})
            history = load_history()

        assert len(history) == 2
        assert history[0]["state"]["epic_key"] == "A"
        assert history[1]["state"]["epic_key"] == "B"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
