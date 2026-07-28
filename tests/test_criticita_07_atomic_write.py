"""
Test Criticità #7 — Scrittura app_config.json non atomica

PRIMA del fix: write_text diretto → rischio corruzione in caso di crash.
DOPO il fix: scrittura atomica via tempfile + os.replace.

Include test di non-regressione per save_app_config.
"""
import sys
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


class TestAtomicWrite:
    """Verifica che la scrittura di app_config sia atomica."""

    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.tmp_dir) / "app_config.json"
        # Create initial config
        self.config_path.write_text(json.dumps({"jira_url": "https://original.com"}))

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_no_partial_write_on_success(self):
        """DOPO il fix: file risultante è JSON valido dopo save."""
        with patch("config.APP_CONFIG_FILE", self.config_path):
            from config import save_app_config
            save_app_config({"window_geometry": "1200x850"})

        content = self.config_path.read_text()
        data = json.loads(content)  # Non deve sollevare JSONDecodeError
        assert data["jira_url"] == "https://original.com"
        assert data["window_geometry"] == "1200x850"

    def test_no_temp_files_left_on_success(self):
        """DOPO il fix: nessun file .tmp residuo dopo scrittura riuscita."""
        with patch("config.APP_CONFIG_FILE", self.config_path):
            from config import save_app_config
            save_app_config({"test": True})

        tmp_files = list(Path(self.tmp_dir).glob("*.tmp"))
        assert len(tmp_files) == 0, f"File temporanei residui: {tmp_files}"

    def test_original_preserved_if_write_fails(self):
        """DOPO il fix: se la scrittura fallisce, il file originale è intatto."""
        original_content = self.config_path.read_text()

        with patch("config.APP_CONFIG_FILE", self.config_path):
            with patch("os.replace", side_effect=OSError("disk full")):
                from config import save_app_config
                with pytest.raises(OSError):
                    save_app_config({"corrupt": True})

        # File originale deve essere intatto
        assert self.config_path.read_text() == original_content

    def test_config_merge_preserves_existing_keys(self):
        """I campi esistenti non vengono persi durante l'update."""
        self.config_path.write_text(json.dumps({
            "jira_url": "https://x.com",
            "project": "TORF",
            "board_id": 38770
        }))

        with patch("config.APP_CONFIG_FILE", self.config_path):
            from config import save_app_config
            save_app_config({"window_geometry": "800x600"})

        data = json.loads(self.config_path.read_text())
        assert data["jira_url"] == "https://x.com"
        assert data["project"] == "TORF"
        assert data["board_id"] == 38770
        assert data["window_geometry"] == "800x600"


class TestNonRegressione:
    """Verifica che save_app_config funzioni come prima."""

    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.tmp_dir) / "app_config.json"
        self.config_path.write_text(json.dumps({"jira_url": "https://test.com"}))

    def teardown_method(self):
        import shutil
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_popup_geometries_saved(self):
        """Le geometrie dei popup vengono salvate correttamente."""
        with patch("config.APP_CONFIG_FILE", self.config_path):
            from config import save_app_config
            save_app_config({"popup_geometries": {"translate": "600x350+100+200"}})

        data = json.loads(self.config_path.read_text())
        assert data["popup_geometries"]["translate"] == "600x350+100+200"

    def test_load_after_save_consistent(self):
        """Load dopo save restituisce gli stessi dati."""
        with patch("config.APP_CONFIG_FILE", self.config_path):
            from config import save_app_config, _load_app_config
            save_app_config({"team_name": "Hydra", "max_epics": 5})
            loaded = _load_app_config()

        assert loaded["team_name"] == "Hydra"
        assert loaded["max_epics"] == 5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
