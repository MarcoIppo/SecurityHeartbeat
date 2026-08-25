"""Contextual help texts for all GUI widgets (EN/IT)."""


def get_help(lang: str = "en") -> dict:
    """Return help texts dictionary for the given language."""
    if lang == "it":
        return _IT
    return _EN


_EN = {
    "select_epic": (
        "📋 SELECT EPIC — Choose the Security Heartbeat epic to work with. "
        "The tool loads the most recent epics matching the configured pattern. "
        "Once selected, its linked User Stories will appear in the editing tabs."
    ),
    "epic_list": (
        "📋 EPIC LIST — 🟢 Open epic: you can create/update stories. "
        "🔴 Resolved epic: read-only, no modifications allowed. "
        "Click an epic to select it. Sorted by creation date (most recent first)."
    ),
    "epic_desc": (
        "📝 EPIC DESCRIPTION (Read-Only) — Shows the full description of the selected epic from Jira. "
        "This field cannot be edited here. To modify it, open the epic directly in Jira."
    ),
    "epic_desc_help": (
        "❓ This field is read-only. To change the epic description: "
        "1) Open the epic in Jira → 2) Edit the Description field → 3) Reload epics in this tool."
    ),
    "add_story": (
        "➕ ADD STORY — Creates a new blank User Story tab. Fill in title, description, "
        "acceptance criteria, sprint, and other fields before pushing to Jira. "
        "New stories will be linked to the currently selected epic."
    ),
    "load_stories": (
        "📥 LOAD STORIES — Reloads User Stories from the selected epic. "
        "If the latest epic has no stories, templates from the previous epic are loaded. "
        "Template stories have sprint reset to 'Unplanned' — assign a real sprint before creating."
    ),
    "scheduling": (
        "📅 SCHEDULING — Opens a table view showing User Stories distributed across sprints. "
        "Columns = sprints (with dates), Rows = story keys. "
        "Stories without a sprint appear in the 'Unplanned' column. "
        "Use this to verify sprint load balance before creating."
    ),
    "create_update": (
        "🚀 CREATE/UPDATE — Pushes stories to Jira under the selected epic. "
        "🆕 New → created | ✏️ Modified → updated | ═ Unchanged → skipped. "
        "A confirmation popup shows the full list with status icons, "
        "followed by a final 'Are you sure?' prompt. This action cannot be undone!"
    ),
    "save_us": (
        "💾 SAVE USER STORIES — Exports all current stories to a JSON file. "
        "Use this to review before pushing to Jira, share with colleagues, "
        "or keep a local backup. Includes all fields: title, description, AC, sprint, labels, etc."
    ),
    "quit": (
        "⏻ QUIT — Saves the current application state (selected epic, token, stories) "
        "and exits. State is automatically restored on next launch. Shortcut: Ctrl+Q"
    ),
    "tag_generated": (
        "🏷️ TAG AS GENERATED\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "When enabled, each created User Story will include:\n\n"
        "  • A 'tool-generated' label — allows filtering in Jira\n"
        "    (JQL: labels = tool-generated)\n"
        "  • A small footer line at the bottom of the description\n"
        "    indicating the tool name and version that generated it\n\n"
        "This does NOT affect the story content displayed in this tool —\n"
        "the tag is only visible on Jira after creation.\n\n"
        "Disable this if you prefer clean stories with no automation trace."
    ),
    "history": (
        "📋 HISTORY — Shows the application version history and changelog. "
        "Each entry lists new features, bug fixes, and improvements."
    ),
    "jira_cred": (
        "🔐 JIRA CONNECTION — Authentication panel for Jira access. "
        "The token is saved (obfuscated) between sessions, so you don't need to re-enter it every time. "
        "Connection status is shown in the status bar."
    ),
    "connect": (
        "🔗 CONNECT — Tests the connection to Jira using the provided API token. "
        "On success: loads sprints from the board and epics matching the pattern. "
        "On failure: check that your token is valid and jira_url is correct in app_config.json."
    ),
    "us_title": (
        "📌 TITLE — The summary/title of the User Story as it appears in Jira. "
        "Keep it concise but descriptive (max 255 chars). "
        "Example: 'Run Security Heartbeat scan on cENM 25.10 Drop 3'"
    ),
    "us_desc": (
        "📝 DESCRIPTION — Detailed description using Jira wiki markup. "
        "Supports *bold*, _italic_, h1./h2. headings, * bullet lists, # numbered lists, "
        "{code}...{code} blocks. Click '?' for full syntax reference. "
        "Click 'IT→EN' to translate Italian text to English."
    ),
    "us_ac": (
        "✅ ACCEPTANCE CRITERIA — Conditions that must be satisfied for the story to be Done. "
        "Use a numbered list (# item), each criterion must be verifiable. "
        "Example: # Scan executed without errors  # Report uploaded to Confluence"
    ),
    "us_sprint": (
        "🏃 SPRINT — Assign this story to a sprint from the team board. "
        "Shows active and future sprints from the configured Jira board. "
        "'— Unplanned —' means no sprint assigned yet — stories must have a real sprint before creation."
    ),
    "sprint_link": "🔗 Open the backlog planning page in Jira (disabled for Unplanned).",
    "us_story_points": "📐 STORY POINTS — Effort estimate for this story. Numeric value (e.g. 1, 2, 3, 5, 8, 13).",
    "us_labels": (
        "🏷️ LABELS — Comma-separated Jira labels to tag the story. "
        "Common labels: sprint number (25.10), team name (Hydra), category (Security). "
        "Labels help filter and search stories on the board. Example: 25.10,Hydra,Security"
    ),
    "us_assignee": (
        "👤 ASSIGNEE — Jira username (signum) of the person who will work on this story. "
        "Enter the lowercase signum (e.g. emaripp, ealbgiu, emarcbo). "
        "Leave empty to leave unassigned."
    ),
    "us_components": (
        "🧩 COMPONENTS — Comma-separated Jira component names to categorize the story. "
        "Components must exist in the Jira project configuration. Example: ENM_Security,cENM"
    ),
    "us_priority": (
        "⚡ PRIORITY — Issue priority in Jira: Blocker (blocks release), Critical (must fix this sprint), "
        "Major (important), Minor (low impact, default), Trivial (cosmetic). "
        "If empty, Jira uses the project default."
    ),
    "markup_help": (
        "❓ MARKUP REFERENCE\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Opens a cheat-sheet popup with the full Jira/Confluence wiki markup syntax.\n\n"
        "Quick examples:\n"
        "  *bold text*         → bold text\n"
        "  _italic text_       → italic text\n"
        "  h2. Section title   → heading\n"
        "  * bullet item       → bullet list\n"
        "  # numbered item     → numbered list\n"
        "  {code}...{code}     → code block\n"
        "  ||col1||col2||      → table header\n"
        "  |val1 |val2 |       → table row\n\n"
        "Use these in Description and Acceptance Criteria fields.\n"
        "The popup stays open while you type — use it as a reference."
    ),
    "translate": (
        "🌐 TRANSLATE (IT → EN)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Translates the field content from Italian to English using Google Translate.\n\n"
        "How it works:\n"
        "  1. Click this button\n"
        "  2. A preview popup shows the translated text\n"
        "  3. 'Confirm' → replaces the field with the translation\n"
        "     'Skip'    → keeps the original text unchanged\n\n"
        "⚠️  Tips:\n"
        "  • Review the translation — automatic translations may have errors\n"
        "  • Jira markup (*bold*, _italic_, etc.) is preserved\n"
        "  • Works best with complete sentences, not single words\n"
        "  • Requires internet connection"
    ),
    "preview_markup": (
        "👁 PREVIEW RENDERED MARKUP\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Opens a popup showing how the Jira wiki markup will be rendered.\n\n"
        "Displays formatted output:\n"
        "  • *bold* → bold   |  _italic_ → italic\n"
        "  • h1./h2./h3. → headings with sizes\n"
        "  • {color:red}text{color} → colored text\n"
        "  • * / # → bullet and numbered lists\n"
        "  • ||header|| / |cell| → formatted tables\n"
        "  • [link text|URL] → clickable links\n"
        "  • {code}...{code} → monospace code block\n\n"
        "Use this to verify your markup is correct before creating the story on Jira."
    ),
    "split_story": (
        "⊕ SPLIT — Duplicates this story into a new tab with the same description. "
        "Useful when a story is too large and needs to be broken into smaller pieces. "
        "The new tab is named '<title> (part 2)' and can be freely edited."
    ),
    "remove_tab": (
        "✕ REMOVE — Removes this tab from the editing area. "
        "This only removes it from the tool, NOT from Jira. "
        "If the story already exists on Jira, it remains there."
    ),
    "status_bar": (
        "📊 STATUS — Mode: JIRA = connected to server, DEMO = offline/no connection. "
        "Shortcuts: Ctrl+S = Save state to disk, Ctrl+Q = Save and quit."
    ),
    "indicator": "● = Connected to Jira (live data) | ○ = Not connected (showing cached data). Color: green = OK, yellow blink = loading, red = error.",
    "add_to_epic": (
        "➕ ADD TO EPIC — Clones the selected stories from the older epic and creates them "
        "as NEW stories linked to the target (latest) epic. The original stories remain "
        "unchanged in their old epic — nothing is moved or re-linked."
    ),
    "story_list_header": (
        "📋 STORY LIST — Shows all User Stories linked to the selected epic. "
        "Check the stories you want to include in batch operations (Create, Save). "
        "Click a story to navigate to its editing tab on the right."
    ),
    "story_list_area": (
        "Scroll to browse all stories. Check/uncheck to select stories for batch operations. "
        "Click a story name to navigate to its editing tab."
    ),
    "us_panel_header": (
        "📝 USER STORIES PANEL — Editing area for User Stories. "
        "Each tab represents a story to be created or updated on Jira. "
        "Fill in all fields, then use 'Create/Update' to push to Jira."
    ),
}

_IT = {
    "select_epic": (
        "📋 SELEZIONA EPICA — Scegli l'epica Security Heartbeat su cui lavorare. "
        "Il tool carica le epiche più recenti che corrispondono al pattern configurato. "
        "Una volta selezionata, le User Stories collegate appariranno nei tab di editing."
    ),
    "epic_list": (
        "📋 LISTA EPICHE — 🟢 Epica aperta: puoi creare/aggiornare le stories. "
        "🔴 Epica risolta: sola lettura, nessuna modifica consentita. "
        "Clicca un'epica per selezionarla. Ordinata per data creazione (più recente prima)."
    ),
    "epic_desc": (
        "📝 DESCRIZIONE EPICA (Sola Lettura) — Mostra la descrizione completa dell'epica da Jira. "
        "Questo campo non è modificabile qui. Per modificarlo, apri l'epica direttamente in Jira."
    ),
    "epic_desc_help": (
        "❓ Questo campo è in sola lettura. Per cambiare la descrizione: "
        "1) Apri l'epica in Jira → 2) Modifica il campo Descrizione → 3) Ricarica le epiche nel tool."
    ),
    "add_story": (
        "➕ AGGIUNGI STORIA — Crea un nuovo tab vuoto per una User Story. Compila titolo, "
        "descrizione, criteri di accettazione, sprint e altri campi prima di inviarla su Jira. "
        "Le nuove stories saranno collegate all'epica selezionata."
    ),
    "load_stories": (
        "📥 CARICA STORIE — Ricarica le User Stories dall'epica selezionata. "
        "Se l'ultima epica non ha stories, vengono caricate quelle della precedente come template. "
        "Le stories template hanno lo sprint resettato a 'Unplanned' — assegna uno sprint prima di crearle."
    ),
    "scheduling": (
        "📅 PIANIFICAZIONE — Apre una tabella con la distribuzione delle stories negli sprint. "
        "Colonne = sprint (con date), Righe = chiavi delle stories. "
        "Le stories senza sprint appaiono nella colonna 'Unplanned'. "
        "Usa questa vista per verificare il bilanciamento del carico."
    ),
    "create_update": (
        "🚀 CREA/AGGIORNA — Invia le stories su Jira sotto l'epica selezionata. "
        "🆕 Nuove → create | ✏️ Modificate → aggiornate | ═ Invariate → saltate. "
        "Un popup di conferma mostra la lista con icone di stato, "
        "seguito da un prompt finale 'Sei sicuro?'. Azione non reversibile!"
    ),
    "save_us": (
        "💾 SALVA USER STORIES — Esporta tutte le stories in un file JSON. "
        "Utile per revisionare prima di inviare a Jira, condividere con colleghi, "
        "o mantenere un backup. Include tutti i campi: titolo, descrizione, AC, sprint, label, ecc."
    ),
    "quit": (
        "⏻ ESCI — Salva lo stato corrente (epica selezionata, token, stories) "
        "e chiude l'applicazione. Lo stato viene ripristinato al prossimo avvio. Scorciatoia: Ctrl+Q"
    ),
    "tag_generated": (
        "🏷️ MARCA COME GENERATA\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Quando abilitata, ogni User Story creata includerà:\n\n"
        "  • Una label 'tool-generated' — permette filtri in Jira\n"
        "    (JQL: labels = tool-generated)\n"
        "  • Una riga a piè di pagina nella descrizione che indica\n"
        "    il nome del tool e la versione che l'ha generata\n\n"
        "Questo NON modifica il contenuto visibile in questo tool —\n"
        "il tag è visibile solo su Jira dopo la creazione.\n\n"
        "Disabilita se preferisci stories pulite senza traccia di automazione."
    ),
    "history": (
        "📋 CRONOLOGIA — Mostra la cronologia delle versioni e il changelog. "
        "Ogni voce elenca nuove funzionalità, correzioni e miglioramenti."
    ),
    "jira_cred": (
        "🔐 CONNESSIONE JIRA — Pannello di autenticazione per Jira. "
        "Il token viene salvato (offuscato) tra le sessioni, non serve reinserirlo ogni volta. "
        "Lo stato della connessione è mostrato nella barra di stato."
    ),
    "connect": (
        "🔗 CONNETTI — Testa la connessione a Jira con il token fornito. "
        "In caso di successo: carica sprint dal board e epiche dal pattern. "
        "In caso di errore: verifica che il token sia valido e jira_url corretto in app_config.json."
    ),
    "us_title": (
        "📌 TITOLO — Il summary/titolo della User Story come apparirà in Jira. "
        "Conciso ma descrittivo (max 255 caratteri). "
        "Esempio: 'Run Security Heartbeat scan on cENM 25.10 Drop 3'"
    ),
    "us_desc": (
        "📝 DESCRIZIONE — Descrizione dettagliata con Jira wiki markup. "
        "Supporta *grassetto*, _corsivo_, h1./h2. titoli, * liste puntate, # liste numerate, "
        "{code}...{code}. Clicca '?' per il riferimento completo. "
        "Clicca 'IT→EN' per tradurre dall'italiano all'inglese."
    ),
    "us_ac": (
        "✅ CRITERI DI ACCETTAZIONE — Condizioni da soddisfare perché la story sia Done. "
        "Usa una lista numerata (# voce), ogni criterio deve essere verificabile. "
        "Esempio: # Scan eseguita senza errori  # Report caricato su Confluence"
    ),
    "us_sprint": (
        "🏃 SPRINT — Assegna questa story a uno sprint dal board del team. "
        "Mostra sprint attivi e futuri dal board Jira configurato. "
        "'— Unplanned —' = nessuno sprint assegnato — le stories devono avere uno sprint reale prima della creazione."
    ),
    "sprint_link": "🔗 Apri la pagina backlog planning in Jira (disabilitato per Unplanned).",
    "us_story_points": "📐 STORY POINTS — Stima dell'effort per questa story. Valore numerico (es. 1, 2, 3, 5, 8, 13).",
    "us_labels": (
        "🏷️ LABEL — Label Jira separate da virgola per taggare la story. "
        "Label comuni: numero sprint (25.10), nome team (Hydra), categoria (Security). "
        "Aiutano a filtrare e cercare sulla board. Esempio: 25.10,Hydra,Security"
    ),
    "us_assignee": (
        "👤 ASSEGNATARIO — Username Jira (signum) di chi lavorerà sulla story. "
        "Inserisci il signum minuscolo (es. emaripp, ealbgiu, emarcbo). "
        "Lascia vuoto per non assegnare."
    ),
    "us_components": (
        "🧩 COMPONENTI — Nomi componenti Jira separati da virgola. "
        "I componenti devono esistere nella configurazione del progetto Jira. Esempio: ENM_Security,cENM"
    ),
    "us_priority": (
        "⚡ PRIORITÀ — Priorità dell'issue: Blocker (blocca release), Critical (da risolvere subito), "
        "Major (importante), Minor (basso impatto, default), Trivial (cosmetico). "
        "Se vuoto, Jira usa il default del progetto."
    ),
    "markup_help": (
        "❓ RIFERIMENTO MARKUP\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Apre un popup con la sintassi completa del wiki markup Jira/Confluence.\n\n"
        "Esempi rapidi:\n"
        "  *testo grassetto*   → testo grassetto\n"
        "  _testo corsivo_     → testo corsivo\n"
        "  h2. Titolo sezione  → intestazione\n"
        "  * elemento          → lista puntata\n"
        "  # elemento          → lista numerata\n"
        "  {code}...{code}     → blocco codice\n"
        "  ||col1||col2||      → intestazione tabella\n"
        "  |val1 |val2 |       → riga tabella\n\n"
        "Usa questi formati nei campi Descrizione e Criteri di Accettazione.\n"
        "Il popup rimane aperto mentre scrivi — usalo come riferimento."
    ),
    "translate": (
        "🌐 TRADUCI (IT → EN)\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Traduce il contenuto del campo dall'italiano all'inglese tramite Google Translate.\n\n"
        "Come funziona:\n"
        "  1. Clicca questo pulsante\n"
        "  2. Un popup mostra l'anteprima della traduzione\n"
        "  3. 'Conferma' → sostituisce il campo con la traduzione\n"
        "     'Salta'    → mantiene il testo originale invariato\n\n"
        "⚠️  Suggerimenti:\n"
        "  • Controlla la traduzione — le traduzioni automatiche possono avere errori\n"
        "  • Il markup Jira (*grassetto*, _corsivo_, ecc.) viene preservato\n"
        "  • Funziona meglio con frasi complete, non singole parole\n"
        "  • Richiede connessione internet"
    ),
    "preview_markup": (
        "👁 ANTEPRIMA MARKUP RENDERIZZATO\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Apre un popup che mostra come il markup Jira verrà visualizzato.\n\n"
        "Mostra il formato renderizzato:\n"
        "  • *grassetto* → grassetto  |  _corsivo_ → corsivo\n"
        "  • h1./h2./h3. → intestazioni con dimensioni\n"
        "  • {color:red}testo{color} → testo colorato\n"
        "  • * / # → liste puntate e numerate\n"
        "  • ||intestazione|| / |cella| → tabelle formattate\n"
        "  • [testo link|URL] → link cliccabili\n"
        "  • {code}...{code} → blocco codice monospace\n\n"
        "Usa questa funzione per verificare che il markup sia corretto prima di creare la story su Jira."
    ),
    "split_story": (
        "⊕ DIVIDI — Duplica questa story in un nuovo tab con lo stesso contenuto. "
        "Utile quando una story è troppo grande e va suddivisa in parti. "
        "Il nuovo tab si chiama '<titolo> (part 2)' e può essere modificato liberamente."
    ),
    "remove_tab": (
        "✕ RIMUOVI — Rimuove questo tab dall'area di editing. "
        "Lo rimuove solo dal tool, NON da Jira. "
        "Se la story esiste già su Jira, rimane lì."
    ),
    "status_bar": (
        "📊 STATO — Mode: JIRA = connesso al server, DEMO = offline/nessuna connessione. "
        "Scorciatoie: Ctrl+S = Salva stato, Ctrl+Q = Salva e esci."
    ),
    "indicator": "● = Connesso a Jira (dati live) | ○ = Non connesso (dati dalla cache). Colore: verde = OK, giallo lampeggiante = caricamento, rosso = errore.",
    "add_to_epic": (
        "➕ AGGIUNGI ALL'EPICA — Clona le stories selezionate dalla vecchia epica "
        "e le crea come NUOVE storie collegate all'epica target (più recente). Le storie "
        "originali restano invariate nella vecchia epica — nulla viene spostato o re-linkato."
    ),
    "story_list_header": (
        "📋 LISTA STORIE — Mostra tutte le User Stories collegate all'epica selezionata. "
        "Spunta le storie da includere nelle operazioni batch (Crea, Salva). "
        "Clicca una storia per navigare al suo tab di editing a destra."
    ),
    "story_list_area": (
        "Scorri per sfogliare tutte le storie. Spunta/deseleziona per scegliere le storie per le operazioni batch. "
        "Clicca il nome di una storia per navigare al suo tab di editing."
    ),
    "us_panel_header": (
        "📝 PANNELLO USER STORIES — Area di editing per le User Stories. "
        "Ogni tab rappresenta una storia da creare o aggiornare su Jira. "
        "Compila tutti i campi, poi usa 'Crea/Aggiorna' per inviarle a Jira."
    ),
}
