"""
Test Criticità #3 — Dipendenze non pinned e inutilizzate

PRIMA del fix: deep-translator senza versione, textual/rich incluse ma mai usate.
DOPO il fix: deep-translator pinnata, dipendenze inutili rimosse.

Include test di non-regressione per verificare che il translator funzioni.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest

REQUIREMENTS_FILE = Path(__file__).parent.parent / "requirements.txt"


class TestRequirements:
    """Verifica il contenuto del requirements.txt."""

    def _read_requirements(self) -> list[str]:
        return [l.strip() for l in REQUIREMENTS_FILE.read_text().splitlines() if l.strip()]

    def test_deep_translator_pinned(self):
        """DOPO il fix: deep-translator deve avere versione esatta."""
        reqs = self._read_requirements()
        dt_lines = [r for r in reqs if "deep-translator" in r]
        assert len(dt_lines) == 1, f"deep-translator non trovato o duplicato: {dt_lines}"
        assert "==" in dt_lines[0], \
            f"FAIL: deep-translator non pinnata: '{dt_lines[0]}' (atteso '==')"

    def test_no_textual(self):
        """DOPO il fix: textual rimossa (non usata nel progetto)."""
        reqs = self._read_requirements()
        textual_lines = [r for r in reqs if "textual" in r.lower()]
        assert len(textual_lines) == 0, \
            f"FAIL: 'textual' ancora presente: {textual_lines}"

    def test_no_rich(self):
        """DOPO il fix: rich rimossa (non usata nel progetto)."""
        reqs = self._read_requirements()
        rich_lines = [r for r in reqs if r.lower().startswith("rich")]
        assert len(rich_lines) == 0, \
            f"FAIL: 'rich' ancora presente: {rich_lines}"

    def test_all_deps_have_version_constraint(self):
        """Tutte le dipendenze devono avere un vincolo di versione."""
        reqs = self._read_requirements()
        for req in reqs:
            if req.startswith("#") or req.startswith("-"):
                continue
            assert any(op in req for op in ["==", ">=", "<=", "~=", "!="]), \
                f"FAIL: '{req}' non ha vincolo di versione"


class TestNonRegressione:
    """Verifica che il modulo translator funzioni ancora correttamente."""

    def test_translator_import(self):
        """Il modulo translator si importa senza errori."""
        from translator import translate_to_english
        assert callable(translate_to_english)

    def test_translator_empty_text(self):
        """Testo vuoto restituito invariato (no network call)."""
        from translator import translate_to_english
        assert translate_to_english("") == ""
        assert translate_to_english("   ") == "   "

    def test_deep_translator_importable(self):
        """Il pacchetto deep-translator è importabile."""
        from deep_translator import GoogleTranslator
        assert GoogleTranslator is not None

    def test_jira_importable(self):
        """Il pacchetto jira è ancora presente."""
        from jira import JIRA
        assert JIRA is not None

    def test_pillow_importable(self):
        """Pillow è ancora presente."""
        from PIL import Image
        assert Image is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
