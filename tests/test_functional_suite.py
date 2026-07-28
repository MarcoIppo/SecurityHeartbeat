"""
Suite di Test Funzionali COMPLETA — Security Heartbeat US Generator

Copre TUTTI i moduli dell'applicazione:
- config.py: caricamento, persistenza, history
- jira_client.py: parsing, validazione, costruzione query, creazione issue
- translator.py: traduzione
- i18n.py: stringhe multilingua
- app.py: logica applicativa (validazione, raccolta dati, stato)

Ogni sezione simula il comportamento end-to-end senza richiedere
connessione Jira reale (mock dove necessario).
"""
import sys
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

sys.path.insert(0, str(Path(__file__).parent.parent))
import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: config.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestConfigLoad:
    """Test caricamento configurazione da app_config.json."""

    def test_load_default_values(self):
        """Valori di default presenti quando config è vuota."""
        from config import JIRA_PROJECT, TEAM_NAME, MAX_EPICS, BOARD_ID
        assert JIRA_PROJECT  # Non vuoto
        assert TEAM_NAME == "Hydra"
        assert isinstance(MAX_EPICS, int) and MAX_EPICS > 0
        assert isinstance(BOARD_ID, int)

    def test_load_app_config_json(self):
        """app_config.json viene letto correttamente."""
        from config import _load_app_config, APP_CONFIG_FILE
        cfg = _load_app_config()
        assert isinstance(cfg, dict)
        assert "jira_url" in cfg

    def test_corrupted_config_returns_empty(self):
        """Config corrotta restituisce dict vuoto (non crash)."""
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        tmp.write("{invalid json!!")
        tmp.close()
        with patch("config.APP_CONFIG_FILE", Path(tmp.name)):
            from config import _load_app_config
            result = _load_app_config()
        os.unlink(tmp.name)
        assert result == {}

    def test_missing_config_returns_empty(self):
        """Config assente restituisce dict vuoto."""
        with patch("config.APP_CONFIG_FILE", Path("/nonexistent/path.json")):
            from config import _load_app_config
            result = _load_app_config()
        assert result == {}


class TestConfigPersistence:
    """Test persistenza stato e history."""

    def setup_method(self):
        self.state_file = Path(tempfile.mktemp(suffix=".json"))
        self.hist_file = Path(tempfile.mktemp(suffix=".json"))

    def teardown_method(self):
        for f in (self.state_file, self.hist_file):
            if f.exists():
                f.unlink()

    def test_save_load_roundtrip(self):
        """Save seguito da load restituisce gli stessi dati."""
        with patch("config.STATE_FILE", self.state_file), \
             patch("config.HISTORY_FILE", self.hist_file):
            from config import save_state, load_state
            state = {"epic_key": "TORF-123", "stories": [{"title": "Test"}]}
            save_state(state)
            loaded = load_state()
        assert loaded["epic_key"] == "TORF-123"
        assert loaded["stories"] == [{"title": "Test"}]

    def test_history_accumulates(self):
        """La history accumula entry fino a 100."""
        with patch("config.STATE_FILE", self.state_file), \
             patch("config.HISTORY_FILE", self.hist_file):
            from config import save_state, load_history
            for i in range(5):
                save_state({"epic_key": f"TORF-{i}"})
            hist = load_history()
        assert len(hist) == 5

    def test_history_caps_at_100(self):
        """La history non supera 100 entries."""
        with patch("config.STATE_FILE", self.state_file), \
             patch("config.HISTORY_FILE", self.hist_file):
            from config import save_state, load_history
            for i in range(110):
                save_state({"n": i})
            hist = load_history()
        assert len(hist) == 100

    def test_load_state_nonexistent_file(self):
        """File di stato inesistente restituisce dict vuoto."""
        with patch("config.STATE_FILE", Path("/tmp/nonexistent_xyz.json")):
            from config import load_state
            assert load_state() == {}


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: jira_client.py — Parsing & Validation
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraClientParsing:
    """Test delle funzioni di parsing in jira_client."""

    def test_parse_sprint_name_object(self):
        """Sprint come oggetto con attributo .name."""
        from jira_client import _parse_sprint_name
        sprint = MagicMock()
        sprint.name = "Hydra 26.10"
        assert _parse_sprint_name(sprint) == "Hydra 26.10"

    def test_parse_sprint_name_java_string(self):
        """Sprint come stringa serializzata Java."""
        from jira_client import _parse_sprint_name
        java_str = "com.atlassian.greenhopper.service.sprint.Sprint@1234[id=100,name=Hydra 26.10,state=ACTIVE]"
        assert _parse_sprint_name(java_str) == "Hydra 26.10"

    def test_parse_sprint_name_list(self):
        """Sprint come lista (prende l'ultimo)."""
        from jira_client import _parse_sprint_name
        s1 = MagicMock()
        s1.name = "Hydra 26.09"
        s2 = MagicMock()
        s2.name = "Hydra 26.10"
        assert _parse_sprint_name([s1, s2]) == "Hydra 26.10"

    def test_parse_sprint_name_none(self):
        """Sprint None restituisce stringa vuota."""
        from jira_client import _parse_sprint_name
        assert _parse_sprint_name(None) == ""

    def test_parse_sprint_name_empty_list(self):
        """Sprint lista vuota restituisce stringa vuota."""
        from jira_client import _parse_sprint_name
        assert _parse_sprint_name([]) == ""

    def test_parse_summary_keywords_simple(self):
        """Parse keywords separate da virgola."""
        from jira_client import _parse_summary_keywords
        result = _parse_summary_keywords("Security,Heartbeat,recurrent")
        assert result == ["Security", "Heartbeat", "recurrent"]

    def test_parse_summary_keywords_quoted(self):
        """Parse keywords con frasi quotate."""
        from jira_client import _parse_summary_keywords
        result = _parse_summary_keywords('"recurrent test",Security')
        assert "recurrent test" in result
        assert "Security" in result

    def test_parse_summary_keywords_empty(self):
        """Pattern vuoto restituisce lista vuota."""
        from jira_client import _parse_summary_keywords
        assert _parse_summary_keywords("") == []


class TestJiraClientValidation:
    """Test validazione issue key e sanitizzazione JQL."""

    def test_valid_keys_accepted(self):
        from jira_client import _validate_issue_key
        assert _validate_issue_key("TORF-1") == "TORF-1"
        assert _validate_issue_key("AB2-99999") == "AB2-99999"

    def test_invalid_keys_rejected(self):
        from jira_client import _validate_issue_key
        invalid = ["", "torf-1", "123-ABC", "TORF", "TORF-", "-123",
                   "TORF-1 OR 1=1", "TORF-1; DROP"]
        for k in invalid:
            with pytest.raises(ValueError):
                _validate_issue_key(k)

    def test_sanitize_preserves_normal_values(self):
        from jira_client import _sanitize_jql_value
        assert _sanitize_jql_value("TORF") == "TORF"
        assert _sanitize_jql_value("Story") == "Story"
        assert _sanitize_jql_value("Security heartbeat") == "Security heartbeat"

    def test_sanitize_removes_dangerous_chars(self):
        from jira_client import _sanitize_jql_value
        result = _sanitize_jql_value("val;ue|with&bad\\chars\n")
        assert ";" not in result
        assert "|" not in result
        assert "&" not in result
        assert "\\" not in result
        assert "\n" not in result


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: jira_client.py — API Calls (mocked)
# ═══════════════════════════════════════════════════════════════════════════════

class TestJiraClientAPI:
    """Test delle chiamate API Jira con mock."""

    def _mock_issue(self, key, summary, desc="", status="Open",
                    resolution=None, labels=None, assignee=None,
                    components=None, priority="Minor"):
        issue = MagicMock()
        issue.key = key
        issue.fields = MagicMock()
        issue.fields.summary = summary
        issue.fields.description = desc
        issue.fields.status.name = status
        issue.fields.resolution = MagicMock(name=resolution) if resolution else None
        if resolution:
            issue.fields.resolution.name = resolution
        issue.fields.labels = labels or []
        issue.fields.assignee = assignee
        issue.fields.components = [MagicMock(name=c) for c in (components or [])]
        for c_mock, c_name in zip(issue.fields.components, components or []):
            c_mock.name = c_name
        issue.fields.priority = MagicMock()
        issue.fields.priority.name = priority
        return issue

    def test_get_open_epics_returns_list(self):
        """get_open_epics restituisce lista di dict con chiavi corrette."""
        mock_issue = self._mock_issue("TORF-100", "Security Heartbeat Epic")
        with patch("jira_client.JIRA") as MockJIRA:
            client = MockJIRA.return_value
            client.search_issues.return_value = [mock_issue]
            from jira_client import get_open_epics
            result = get_open_epics()
        assert len(result) == 1
        assert result[0]["key"] == "TORF-100"
        assert "summary" in result[0]
        assert "status" in result[0]
        assert "resolution" in result[0]

    def test_get_epic_stories_structure(self):
        """get_epic_stories restituisce stories con tutti i campi."""
        mock_issue = self._mock_issue("TORF-200", "Test Story", "Description")
        mock_issue.fields.customfield_11910 = None
        with patch("jira_client.JIRA") as MockJIRA:
            client = MockJIRA.return_value
            client.search_issues.return_value = [mock_issue]
            client.fields.return_value = [
                {"id": "customfield_123", "name": "Acceptance Criteria"},
                {"id": "customfield_456", "name": "Epic Link"},
            ]
            setattr(mock_issue.fields, "customfield_123", "AC text")
            setattr(mock_issue.fields, "customfield_456", "TORF-100")
            from jira_client import get_epic_stories
            # Reset cached field id
            import jira_client
            jira_client._ac_field_id = None
            result = get_epic_stories("TORF-100")
        assert len(result) == 1
        s = result[0]
        required_keys = {"key", "summary", "description", "acceptance_criteria",
                         "sprint", "labels", "status", "resolution",
                         "assignee", "assignee_key", "components", "priority", "epic_link"}
        assert required_keys.issubset(set(s.keys()))

    def test_create_story_builds_correct_fields(self):
        """create_story invia i campi corretti all'API."""
        with patch("jira_client.JIRA") as MockJIRA:
            client = MockJIRA.return_value
            mock_issue = MagicMock()
            mock_issue.key = "TORF-300"
            client.create_issue.return_value = mock_issue
            client.fields.return_value = [
                {"id": "customfield_456", "name": "Epic Link"},
                {"id": "customfield_789", "name": "Acceptance Criteria"},
            ]
            client.sprints.return_value = []
            import jira_client
            jira_client._ac_field_id = None
            result = jira_client.create_story(
                "TORF-100", "My Story", "Description",
                labels=["26.10", "Hydra"],
                assignee_key="EMARIPP",
                components=["Security"],
                priority="Major",
                acceptance_criteria="AC here"
            )
        assert result == "TORF-300"
        call_kwargs = client.create_issue.call_args[1]
        fields = call_kwargs["fields"]
        assert fields["summary"] == "My Story"
        assert fields["labels"] == ["26.10", "Hydra"]
        assert fields["assignee"] == {"name": "EMARIPP"}
        assert fields["components"] == [{"name": "Security"}]
        assert fields["priority"] == {"name": "Major"}

    def test_get_board_sprints_handles_error(self):
        """get_board_sprints restituisce lista vuota su errore."""
        with patch("jira_client.JIRA") as MockJIRA:
            client = MockJIRA.return_value
            client.sprints.side_effect = Exception("Board not found")
            from jira_client import get_board_sprints
            result = get_board_sprints()
        assert result == []

    def test_update_epic_link_validates_both_keys(self):
        """update_epic_link rigetta key invalide."""
        from jira_client import update_epic_link
        with pytest.raises(ValueError):
            update_epic_link("invalid", "TORF-1")
        with pytest.raises(ValueError):
            update_epic_link("TORF-1", "invalid")


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: translator.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestTranslator:
    """Test del modulo di traduzione."""

    def test_empty_text_returns_unchanged(self):
        from translator import translate_to_english
        assert translate_to_english("") == ""
        assert translate_to_english("   ") == "   "

    def test_translation_returns_string(self):
        """Il risultato è sempre una stringa."""
        from translator import translate_to_english
        result = translate_to_english("Ciao mondo")
        assert isinstance(result, str)

    def test_translation_handles_import_error(self):
        """Se deep_translator non è disponibile, restituisce il testo originale."""
        with patch.dict(sys.modules, {"deep_translator": None}):
            # Force reimport
            import importlib
            import translator
            importlib.reload(translator)
            result = translator.translate_to_english("Testo di prova")
        assert isinstance(result, str)
        # Reload back to normal
        import importlib
        import translator
        importlib.reload(translator)


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: i18n.py
# ═══════════════════════════════════════════════════════════════════════════════

class TestI18n:
    """Test del modulo di internazionalizzazione."""

    def test_english_strings_available(self):
        from i18n import get_strings
        s = get_strings("en")
        assert "title" in s
        assert "select_epic" in s
        assert "confirm_create" in s

    def test_italian_strings_available(self):
        from i18n import get_strings
        s = get_strings("it")
        assert "title" in s
        assert "select_epic" in s

    def test_en_and_it_have_same_keys(self):
        """EN e IT devono avere le stesse chiavi."""
        from i18n import get_strings
        en = get_strings("en")
        it = get_strings("it")
        assert set(en.keys()) == set(it.keys()), \
            f"Chiavi mancanti IT: {set(en.keys()) - set(it.keys())}, " \
            f"Chiavi extra IT: {set(it.keys()) - set(en.keys())}"

    def test_unknown_lang_falls_back_to_en(self):
        from i18n import get_strings
        s = get_strings("xx")
        en = get_strings("en")
        assert s == en

    def test_no_empty_strings(self):
        """Nessuna stringa vuota nel dizionario."""
        from i18n import get_strings
        for lang in ("en", "it"):
            s = get_strings(lang)
            for key, val in s.items():
                assert val.strip(), f"[{lang}] '{key}' è vuota"


# ═══════════════════════════════════════════════════════════════════════════════
# MODULE: app.py — Application Logic (no GUI, testabile)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAppLogic:
    """Test della logica applicativa estratta da app.py."""

    def test_validate_stories_valid(self):
        """Stories valide non generano errori."""
        from tests.test_criticita_08_validation import _get_validate_fn
        validate = _get_validate_fn()
        stories = [
            {"title": "SWHB - Test 1", "description": "Desc"},
            {"title": "SWHB - Test 2", "description": ""},
        ]
        assert validate(stories) == []

    def test_validate_stories_placeholder(self):
        """Placeholder 'New Story' genera errore."""
        from tests.test_criticita_08_validation import _get_validate_fn
        validate = _get_validate_fn()
        stories = [{"title": "New Story", "description": ""}]
        errors = validate(stories)
        assert len(errors) == 1

    def test_validate_stories_too_long(self):
        """Titolo > 255 chars genera errore."""
        from tests.test_criticita_08_validation import _get_validate_fn
        validate = _get_validate_fn()
        stories = [{"title": "X" * 256, "description": ""}]
        errors = validate(stories)
        assert len(errors) == 1


# ═══════════════════════════════════════════════════════════════════════════════
# END-TO-END: Flusso completo simulato
# ═══════════════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    """Test del flusso completo: config → epic → stories → creation."""

    def test_full_flow_config_to_creation(self):
        """Simula il flusso: carica config → ottieni epics → ottieni stories → crea."""
        # 1. Config loads correctly
        from config import JIRA_PROJECT, TEAM_NAME
        assert JIRA_PROJECT == "TORF"

        # 2. Mock Jira and get epics
        with patch("jira_client.JIRA") as MockJIRA:
            client = MockJIRA.return_value

            # Epics
            epic_issue = MagicMock()
            epic_issue.key = "TORF-900"
            epic_issue.fields = MagicMock()
            epic_issue.fields.summary = "Security Heartbeat recurrent"
            epic_issue.fields.description = "Epic description"
            epic_issue.fields.status.name = "Open"
            epic_issue.fields.resolution = None

            # Stories
            story_issue = MagicMock()
            story_issue.key = "TORF-901"
            story_issue.fields = MagicMock()
            story_issue.fields.summary = "SWHB - Pen Test"
            story_issue.fields.description = "Run pen test"
            story_issue.fields.status.name = "Open"
            story_issue.fields.resolution = None
            story_issue.fields.labels = ["26.10", "Hydra"]
            story_issue.fields.assignee = MagicMock()
            story_issue.fields.assignee.displayName = "Marco"
            story_issue.fields.assignee.name = "EMARIPP"
            story_issue.fields.components = []
            story_issue.fields.priority.name = "Major"
            story_issue.fields.customfield_11910 = None

            client.search_issues.side_effect = [
                [epic_issue],   # get_open_epics
                [story_issue],  # get_epic_stories
            ]
            client.fields.return_value = [
                {"id": "customfield_456", "name": "Epic Link"},
                {"id": "customfield_789", "name": "Acceptance Criteria"},
            ]
            setattr(story_issue.fields, "customfield_789", "AC content")
            setattr(story_issue.fields, "customfield_456", "TORF-900")

            import jira_client
            jira_client._ac_field_id = None
            epics = jira_client.get_open_epics()
            assert len(epics) == 1
            assert epics[0]["key"] == "TORF-900"

            stories = jira_client.get_epic_stories("TORF-900")
            assert len(stories) == 1
            assert stories[0]["summary"] == "SWHB - Pen Test"
            assert stories[0]["assignee_key"] == "EMARIPP"

        # 3. Validate stories
        from tests.test_criticita_08_validation import _get_validate_fn
        validate = _get_validate_fn()
        to_create = [{"title": s["summary"], "description": s["description"]}
                     for s in stories]
        errors = validate(to_create)
        assert errors == []

    def test_state_persistence_flow(self):
        """Simula: salva stato → chiudi app → riapri → stato recuperato."""
        state_file = Path(tempfile.mktemp(suffix=".json"))
        hist_file = Path(tempfile.mktemp(suffix=".json"))
        try:
            with patch("config.STATE_FILE", state_file), \
                 patch("config.HISTORY_FILE", hist_file):
                from config import save_state, load_state

                # Salva stato con token e stories
                save_state({
                    "epic_key": "TORF-500",
                    "epic_idx": 0,
                    "jira_token": "secret_pat_123",
                    "stories": [
                        {"title": "Story A", "description": "Desc A", "sprint": "Hydra 26.10"},
                        {"title": "Story B", "description": "Desc B", "sprint": "Hydra 26.11"},
                    ]
                })

                # Simula "riapertura" — carica stato
                loaded = load_state()
                assert loaded["epic_key"] == "TORF-500"
                assert loaded["jira_token"] == "secret_pat_123"
                assert len(loaded["stories"]) == 2

                # Token non in chiaro nel file
                raw = json.loads(state_file.read_text())
                assert "jira_token" not in raw
                assert "jira_token_b64" in raw
        finally:
            for f in (state_file, hist_file):
                if f.exists():
                    f.unlink()


# ═══════════════════════════════════════════════════════════════════════════════
# EDGE CASES & ROBUSTNESS
# ═══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    """Test di casi limite e robustezza."""

    def test_sprint_parse_no_comma_after_name(self):
        """Sprint string senza virgola dopo il nome — non deve crashare."""
        from jira_client import _parse_sprint_name
        # Malformed string
        try:
            result = _parse_sprint_name("name=TestSprint")
        except ValueError:
            pass  # Acceptable to raise

    def test_epic_key_with_large_number(self):
        """Issue key con numeri grandi (7+ cifre)."""
        from jira_client import _validate_issue_key
        assert _validate_issue_key("TORF-9999999") == "TORF-9999999"

    def test_sanitize_unicode_preserved(self):
        """Caratteri unicode legittimi non vengono rimossi."""
        from jira_client import _sanitize_jql_value
        result = _sanitize_jql_value("Attività ricorrenti — rete")
        assert "Attività" in result
        assert "—" in result

    def test_config_version_defined(self):
        """VERSION è definita e nel formato corretto."""
        from config import VERSION
        parts = VERSION.split(".")
        assert len(parts) == 3
        assert all(p.isdigit() for p in parts)

    def test_translator_long_text(self):
        """Testo lungo non causa errori (potrebbe essere troncato dal servizio)."""
        from translator import translate_to_english
        long_text = "Questa è una frase molto lunga. " * 50
        result = translate_to_english(long_text)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_i18n_strings_not_too_long(self):
        """Le stringhe UI non sono troppo lunghe per i widget."""
        from i18n import get_strings
        for lang in ("en", "it"):
            s = get_strings(lang)
            for key, val in s.items():
                assert len(val) < 200, f"[{lang}] '{key}' troppo lunga: {len(val)} chars"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
