"""
Test Criticità #6 — Funzione is_italian() mai definita + ERICSSON_LIGHT undefined

PRIMA del fix: _translate_tab chiamava is_italian() (NameError), ERICSSON_LIGHT undefined.
DOPO il fix: dead code rimosso, riferimenti a simboli inesistenti eliminati.

Include test di non-regressione per verificare che app.py sia importabile.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

APP_FILE = Path(__file__).parent.parent / "app.py"


class TestDeadCodeRemoved:
    """Verifica la rimozione di codice morto con riferimenti undefined."""

    def test_no_is_italian_reference(self):
        """DOPO il fix: is_italian() non deve essere referenziata."""
        content = APP_FILE.read_text()
        assert "is_italian" not in content, \
            "FAIL: 'is_italian' ancora presente in app.py"

    def test_no_translate_tab_method(self):
        """DOPO il fix: _translate_tab (dead code) rimosso."""
        content = APP_FILE.read_text()
        assert "_translate_tab" not in content, \
            "FAIL: '_translate_tab' ancora presente in app.py"

    def test_no_ericsson_light_undefined(self):
        """DOPO il fix: ERICSSON_LIGHT non usato (non definito)."""
        content = APP_FILE.read_text()
        assert "ERICSSON_LIGHT" not in content, \
            "FAIL: 'ERICSSON_LIGHT' ancora referenziato in app.py"


class TestNonRegressione:
    """Verifica che app.py sia ancora valido dopo le modifiche."""

    def test_app_module_importable(self):
        """app.py si importa senza SyntaxError (no GUI, solo parsing)."""
        import ast
        content = APP_FILE.read_text()
        # Verifica che il file sia parsabile come Python valido
        tree = ast.parse(content)
        assert tree is not None

    def test_translate_popup_still_exists(self):
        """La funzionalità di traduzione (popup) è ancora presente."""
        content = APP_FILE.read_text()
        assert "_translate_popup" in content, \
            "FAIL: _translate_popup rimossa per errore"

    def test_split_tab_still_exists(self):
        """_split_tab (funzionalità attiva) è ancora presente."""
        content = APP_FILE.read_text()
        assert "_split_tab" in content

    def test_no_undefined_name_patterns(self):
        """Nessun pattern noto di nomi undefined nel codice."""
        content = APP_FILE.read_text()
        # Verifica che non ci siano altri riferimenti a variabili non definite note
        undefined_names = ["is_italian", "ERICSSON_LIGHT", "is_english"]
        for name in undefined_names:
            assert name not in content, f"Riferimento undefined '{name}' trovato"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
