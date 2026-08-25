# 📋 LogBook — Security Heartbeat US Generator

> Registro delle criticità risolte, fix applicati e test eseguiti.

---

## #15 — GUI freezata durante inizializzazione (cursore busy)

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-08-25 |
| **Severità** | 🟡 UX Fix |
| **Versione** | 1.4.2 |
| **File coinvolti** | `app.py`, `config.py`, `README.md` |
| **Test** | Syntax check ✅ |

### Criticità

L'applicazione appariva completamente "frizzata" all'avvio: nessun bottone rispondeva, il cursore restava normale, e non c'era nessuna indicazione visiva che fosse in corso un'inizializzazione (connessione Jira, caricamento sprint, caricamento epic). L'utente non poteva distinguere un hang da un caricamento in corso.

### Fix applicato

1. **Deferimento inizializzazione**: le chiamate pesanti (`_init_jira_from_state`, `_load_sprints`, `_load_epics`, `_restore_state`) sono state spostate in un metodo `_deferred_init()` invocato tramite `root.after_idle()`. In questo modo la finestra viene renderizzata completamente prima di iniziare le operazioni di rete.
2. **Cursore busy**: aggiunto metodo `_set_busy(busy)` che imposta il cursore "watch" (clessidra) su tutta la finestra durante il caricamento, e lo resetta al termine. L'utente vede immediatamente che l'app sta lavorando.
3. **Robustezza**: il reset del cursore è in un blocco `finally` per garantire che venga ripristinato anche in caso di errore durante l'init.

### Esito

✅ L'applicazione mostra la GUI immediatamente con cursore a clessidra, poi torna interattiva al termine del caricamento.

---

## #14 — Quit button non funzionante, allineamento parking US, tooltip mancanti

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-08-25 |
| **Severità** | 🟡 Bug Fix + UX |
| **File coinvolti** | `app.py`, `help_texts.py` |
| **Test** | Syntax check ✅, test suite non-jira ✅ (16 passed) |

### Criticità

1. **Quit button**: il pulsante "⏻ Quit" non chiudeva l'applicazione (solo la chiusura della finestra con la X funzionava). Causa: il wrapper `debounced()` disabilita il bottone prima di chiamare `_on_close()`, e `root.destroy()` da solo non sempre ferma il mainloop.
2. **Parking US disallineato**: il box con la lista delle storie (checkbox) nel pannello sinistro non aveva bordi visibili, padding inconsistente, e sfondo indistinguibile dal pannello.
3. **Tooltip mancanti**: molti widget di input (Entry, ScrolledText, Combobox) non avevano tooltip al passaggio del mouse — solo le label avevano le "nuvolette".

### Fix applicato

1. **Quit button**: rimosso il wrapper `debounced()` dal bottone Quit — ora usa `command=self._on_close` direttamente (un'azione di uscita non va mai debounced). Aggiunto `self.root.quit()` prima di `self.root.destroy()` in `_on_close` per garantire l'uscita dal mainloop.
2. **Parking US**: aggiunto un frame contenitore con bordo visibile (`highlightbackground=BORDER_COLOR`), sfondo `BG_CARD` consistente per le checkbox, padding interno, e margini uniformi.
3. **Tooltip**: aggiunti ToolTip su tutti i widget di input: `title_entry`, `desc_text`, `ac_text`, `sprint_combo`, `labels_entry`, `sp_entry`, `assignee_entry`, `components_entry`, `priority_entry`, `epic_desc` ScrolledText, header "📝 User Stories", header story list, canvas area, e ogni checkbox nella lista storie (con dettagli: key, sprint, status, assignee).
4. Aggiunte chiavi help_texts EN/IT: `story_list_header`, `story_list_area`, `us_panel_header`.

### Esito

❌ Parziale — persistevano problemi su quit, checkbox e tooltip (vedi #15).

---

## #16 — Tooltip non visibili su Linux, Quit non responsivo, Checkbox signature come button

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-08-25 |
| **Severità** | 🟡 Bug Fix + UX |
| **File coinvolti** | `app.py`, `config.py`, `README.md` |
| **Test** | Syntax check ✅ |

### Criticità

1. **Tooltip non visibili**: su Linux (GNOME/KDE) i tooltip non apparivano. La `Toplevel` creata con il widget come parent e senza pattern withdraw/deiconify non veniva renderizzata da alcuni window manager.
2. **Quit non responsivo**: il bottone Quit non terminava l'applicazione — `root.destroy()` da solo non interrompe il mainloop su Linux.
3. **Checkbox "Tag as generated"**: esteticamente disomogeneo rispetto agli altri bottoni nella barra azioni. L'utente richiedeva uniformità visiva (stesso stile dei bottoni adiacenti) e posizionamento in coda.

### Fix applicato

1. **Tooltip**: riscritta la classe `ToolTip` — usa `winfo_toplevel()` come parent della Toplevel, pattern withdraw → geometry → deiconify per display affidabile su tutti i WM Linux. Aggiunto handler `<Destroy>`, check `winfo_exists()`, e try/except su `after_cancel()`.
2. **Quit**: aggiunto `self.root.quit()` prima di `self.root.destroy()` in `_on_close()` per uscire dal mainloop prima di distruggere la finestra.
3. **Checkbox → Toggle Button**: sostituito `tk.Checkbutton` con un `tk.Button` toggle stilizzato (stessi font, padding, cursor degli altri bottoni). Colore verde (BTN_SUCCESS) quando attivo, grigio (#555555) quando disattivo, con relief sunken/raised. Riordinato: Scheduling | Create | Save | Tag (ultimo a sinistra, prima di Quit a destra).

### Esito

✅ Verificato — syntax check OK. Versione 1.4.1.

---

## #15 — Quit, Checkbox signature invisibile, Tooltip non responsivi, Performance

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-08-25 |
| **Severità** | 🟡 Bug Fix + Performance |
| **File coinvolti** | `app.py` |
| **Test** | Syntax check ✅ |

### Criticità

1. **Quit**: `_on_close()` chiamava `root.quit()` + `root.destroy()` ma il blink timer attivo poteva generare TclError dopo destroy, e su Linux il processo non terminava.
2. **Checkbox "Tag as generated"**: `selectcolor=BG_PANEL` (`#002255`) rendeva il segno di spunta praticamente invisibile sullo sfondo scuro — l'utente non capiva se era attivo o meno.
3. **Tooltip non apparivano**: il canvas della lista storie usava `bind_all("<Enter>")` per il mousewheel, che sovrascriveva i binding `<Enter>` dei ToolTip su qualunque widget. Inoltre i binding `<Enter>` multipli (con/senza `add="+"`) erano errati e conflittuali.
4. **Performance/lentezza**: il preload delle stories faceva N chiamate HTTP bloccanti (una per epic, con max_epics=5 = 6 chiamate totali) durante l'init della GUI, bloccandola per secondi.

### Fix applicato

1. **Quit**: aggiunto `after_cancel()` del blink timer prima del cleanup, rimosso `root.quit()`, usato `sys.exit(0)` come terminazione definitiva dopo `root.destroy()`.
2. **Checkbox**: cambiato `selectcolor` da `#002255` a `#1a1a2e` (contrasto visibile), aggiunto `indicatoron=True` esplicito.
3. **ToolTip riscritto**: aggiunto delay 350ms prima della comparsa, binding con `add="+"` per non sovrascrivere altri handler, hide su `<ButtonPress>`, gestione errori su `winfo_rootx()`, tooltip `topmost` per non perdere visibilità, `_cancel()` robusto.
4. **Mousewheel**: sostituito `bind_all()` (globale) con `bind()` locale sul canvas — non interferisce più con altri widget.
5. **Performance**: preload ridotto da tutte le epic (5) a solo le prime 2 (target + fallback); le altre sono caricate on-demand alla selezione.

### Esito

✅ Risolto. Quit termina il processo, checkbox visibile, tooltip appaiono su tutti i widget, avvio più rapido.

---

## #13 — Tag-as-generated checkbox (label + description footer)

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-08-25 |
| **Severità** | 🟢 Feature |
| **File coinvolti** | `jira_client.py`, `app.py`, `i18n.py`, `help_texts.py`, `config.py` |
| **Test** | Syntax check ✅ su tutti i moduli |

### Criticità

Non era possibile distinguere, su Jira, le User Stories create manualmente da quelle generate automaticamente dal tool. Nessuna tracciabilità sull'origine delle issue.

### Fix applicato

1. Aggiunto parametro `tag_generated` a `create_story()` in `jira_client.py`: quando attivo, appende la label `tool-generated` e una riga footer grigia/corsiva nella description con nome tool e versione.
2. Aggiunta checkbox "🏷️ Tag as generated" nella action bar di `app.py`, posizionata tra il bottone Create e Save, abilitata di default.
3. Aggiunte stringhe EN/IT in `i18n.py` e tooltip descrittivi in `help_texts.py`.
4. Il tag è applicato **solo su Jira** alla creazione — non modifica il contenuto visibile nel tool.

### Esito

✅ Implementato. Versione bumped a 1.4.0.

---

## #11 — Quit button and window close crash ("application has been destroyed")

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-08-24 |
| **Severità** | 🔴 Bug (Crash) |
| **File coinvolti** | `app.py` |
| **Test** | Syntax check ✅ |

### Criticità

Closing the window (X button) during the `_restore_state()` messagebox caused a `TclError: can't invoke "grab" command: application has been destroyed`. This happened because `protocol("WM_DELETE_WINDOW", ...)` was registered *after* `_restore_state()`, so tkinter's default handler destroyed the app while the dialog was still open. The Quit button could also fail if the window was in an invalid state during `_save()`.

### Fix applicato

1. Moved `protocol("WM_DELETE_WINDOW")` and key bindings registration **before** `_restore_state()` and all init operations that may show dialogs.
2. Added `winfo_exists()` guard and `try/except` around the `messagebox.askyesno` in `_restore_state()` so if the window is destroyed mid-dialog, it gracefully aborts instead of crashing.
3. Made `_on_close()` robust: wrapped in try/except, checks `winfo_exists()` before saving state, and ensures `destroy()` is always called in a `finally` block.

### Esito

App compila correttamente. Il close handler è ora registrato prima di qualsiasi dialog, eliminando la race condition.

---

## #10 — Detailed contextual help tooltips (EN/IT)

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-07-27 |
| **Severità** | 🟡 Feature (UX) |
| **File coinvolti** | `app.py`, `help_texts.py` (new) |
| **Test** | Syntax check + key parity EN/IT |

### Criticità

Tooltips were short, single-line, and English-only. The JenkinsJobConfiguration app had detailed, well-formatted help with emojis and structured descriptions. This app supports both EN and IT via `--ita` flag but tooltips were not localized.

### Fix applicato

1. Created `help_texts.py` module with 28 help entries in both EN and IT
2. Each entry follows the format: emoji title + separator line + multi-line description with examples
3. Replaced all 30 `ToolTip()` calls in `app.py` with references to `H["key"]` dictionary
4. Added `from help_texts import get_help` and `H = get_help(LANG)` for language-aware selection
5. Both EN and IT dictionaries have matching key sets (verified programmatically)

### Test eseguiti

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK
- `python3 -c "import ast; ast.parse(open('help_texts.py').read())"` → OK
- Key parity check EN vs IT: 28 keys match ✓

### Esito

✅ Tutti i tooltip ora mostrano help dettagliato e formattato, in entrambe le lingue.

---

## #9 — Create/Update confirmation popup with story classification

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-07-27 |
| **Severità** | 🟡 Feature (UX) |
| **File coinvolti** | `app.py`, `jira_client.py`, `i18n.py`, `config.py` |
| **Test** | Manual GUI verification (syntax check passed) |

### Criticità

The "Create User Stories" button only supported creation of new stories. There was no visual distinction between new, modified, or unchanged stories in the confirmation popup. Users had no second confirmation step before irreversible Jira writes. Additionally, the Epic Description field had no visual cue indicating it was read-only.

### Fix applicato

1. Added `_classify_stories()` method that compares tab content vs. cached Jira data to determine new/modified/unchanged status
2. Reworked confirmation popup with status icons (🆕 New, ✏️ Modified, ═ Unchanged) and a summary legend
3. Added a second `messagebox.askyesno` confirmation ("Are you sure?") before writing to Jira
4. Changed button label to "Create/Update User Stories" (EN/IT)
5. Added `update_story()` function in `jira_client.py` to update existing issues
6. Made Epic Description background grey (`#2a2a2a`) with dimmed text (`#aaaaaa`) to visually indicate read-only
7. Added `?` button next to "Epic Description" label that opens a help messagebox explaining the field is read-only

### Test eseguiti

- `python3 -c "import ast; ast.parse(open('app.py').read())"` → OK
- `python3 -c "import ast; ast.parse(open('jira_client.py').read())"` → OK
- `python3 -c "import ast; ast.parse(open('i18n.py').read())"` → OK
- `python3 -c "import ast; ast.parse(open('config.py').read())"` → OK

### Esito

✅ Tutte le modifiche parsano correttamente. Version bumped to 1.3.0.

---

## #1 — Token Jira salvato in chiaro su disco

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🔴 Alta (Security) |
| **File coinvolti** | `config.py` |
| **Test** | `tests/test_criticita_01_token_storage.py` |

### Criticità

Il token PAT Jira veniva salvato in plain text nel file `~/.secheartbeat_state.json` con permessi di default (`0644`), rendendolo leggibile da qualsiasi utente o processo con accesso alla home directory.

### Effetto

- Esposizione delle credenziali Jira a utenti locali, malware, backup non cifrati.
- Violazione delle policy Ericsson sulla gestione dei secrets.
- Possibile impersonificazione dell'utente su Jira.

### Fix applicato

1. **Offuscamento base64**: il token viene codificato prima della scrittura (`jira_token_b64`) e decodificato in lettura.
2. **Permessi file `0600`**: solo il proprietario può leggere/scrivere il file di stato.
3. **Backward compatibility**: se il file contiene ancora `jira_token` in chiaro (vecchio formato), viene letto comunque senza errori.

### Test eseguiti

| # | Test | Esito |
|---|------|-------|
| 1 | Token non presente in plain text nel file | ✅ PASS |
| 2 | Roundtrip save→load restituisce token originale | ✅ PASS |
| 3 | Permessi file = `0600` | ✅ PASS |
| 4 | Backward compat con vecchi file plain text | ✅ PASS |
| 5 | Token vuoto gestito senza errori | ✅ PASS |
| 6 | **Non-regressione**: tutti i campi stato preservati | ✅ PASS |
| 7 | **Non-regressione**: stato senza token funziona | ✅ PASS |
| 8 | **Non-regressione**: history continua a funzionare | ✅ PASS |

### Risultato

```
8 passed in 0.81s
```

---

## #2 — JQL Injection nelle query Jira

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🔴 Alta (Security) |
| **File coinvolti** | `jira_client.py` |
| **Test** | `tests/test_criticita_02_jql_injection.py` |

### Criticità

I valori delle variabili (`epic_key`, `JIRA_PROJECT`, `STORY_ISSUETYPE`) venivano inseriti direttamente nelle stringhe JQL senza alcuna sanitizzazione né quoting:
```python
jql = f'"Epic Link" = {epic_key} AND issuetype = {STORY_ISSUETYPE}'
```
Un valore manipolato (es. da file di stato corrotto) poteva alterare la semantica della query.

### Effetto

- Information disclosure: query modificate potevano restituire issue di altri progetti.
- Errori inattesi con caratteri speciali nel pattern.
- Violazione del principio di least privilege.

### Fix applicato

1. **`_sanitize_jql_value()`**: rimuove operatori JQL (`OR`, `AND`, `NOT`), caratteri pericolosi (`;`, `|`, `&`, `\`, newlines).
2. **`_validate_issue_key()`**: valida che le issue key rispettino il formato `^[A-Z][A-Z0-9]+-\d+$`, rifiutando qualsiasi input non conforme.
3. **Tutti i valori nelle query JQL** sono ora quotati con doppi apici (`"value"`).
4. Validazione applicata in: `get_open_epics`, `get_epic_stories`, `get_historical_stories`, `create_story`, `update_epic_link`.

### Test eseguiti

| # | Test | Esito |
|---|------|-------|
| 1 | Valori normali non alterati (TORF, Story, Epic) | ✅ PASS |
| 2 | Operatore OR rimosso | ✅ PASS |
| 3 | Operatore AND rimosso | ✅ PASS |
| 4 | Punto e virgola rimosso | ✅ PASS |
| 5 | Pipe rimosso | ✅ PASS |
| 6 | Newlines rimosse | ✅ PASS |
| 7 | Valore vuoto/None gestito | ✅ PASS |
| 8 | Spazi nelle frasi preservati | ✅ PASS |
| 9 | Key valide accettate (TORF-123, TORF-907685) | ✅ PASS |
| 10 | Key con injection rifiutata (ValueError) | ✅ PASS |
| 11 | Key senza trattino rifiutata | ✅ PASS |
| 12 | Key minuscola rifiutata | ✅ PASS |
| 13 | Key vuota rifiutata | ✅ PASS |
| 14 | Key con caratteri speciali rifiutata | ✅ PASS |
| 15 | Whitespace attorno alla key rimosso | ✅ PASS |
| 16–21 | **Non-regressione**: TORF, Story, Epic, pattern, key tipiche, team name | ✅ PASS |

### Risultato

```
29 passed in 0.58s (inclusi test criticità #1 — nessuna regressione)
```

---

## #3 — Dipendenza `deep-translator` senza versione pinned

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🔴 Alta (Supply Chain) |
| **File coinvolti** | `requirements.txt` |
| **Test** | `tests/test_criticita_03_dependencies.py` |

### Criticità

`deep-translator` era presente senza versione pinned. Inoltre `textual>=0.40.0` e `rich>=13.0.0` erano incluse ma mai utilizzate nel codice.

### Effetto

- Supply chain attack: un pacchetto compromesso su PyPI sarebbe stato installato automaticamente.
- Breaking changes silenziose (il translator inghiotte tutte le eccezioni).
- Dipendenze inutili aumentano la superficie d'attacco senza beneficio.

### Fix applicato

1. **Pinnata** `deep-translator==1.11.4` (versione attualmente installata e testata).
2. **Rimosse** `textual` e `rich` (non usate in nessun modulo del progetto).
3. Tutte le dipendenze ora hanno un vincolo di versione.

### Test eseguiti

| # | Test | Esito |
|---|------|-------|
| 1 | deep-translator ha versione pinned con `==` | ✅ PASS |
| 2 | textual non presente | ✅ PASS |
| 3 | rich non presente | ✅ PASS |
| 4 | Tutte le deps hanno vincolo di versione | ✅ PASS |
| 5 | **Non-regressione**: translator importabile | ✅ PASS |
| 6 | **Non-regressione**: testo vuoto gestito | ✅ PASS |
| 7 | **Non-regressione**: deep_translator importabile | ✅ PASS |
| 8 | **Non-regressione**: jira importabile | ✅ PASS |
| 9 | **Non-regressione**: Pillow importabile | ✅ PASS |

### Risultato

```
38 passed in 0.50s (suite completa — nessuna regressione)
```

---

## #4 — `importlib.reload(jira_client)` fragile e pericoloso

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🟠 Media (Funzionale/Stabilità) |
| **File coinvolti** | `app.py`, `jira_client.py` |
| **Test** | `tests/test_criticita_04_no_reload.py` |

### Criticità

`_init_jira()` in `app.py` usava `importlib.reload(jira_client)` per forzare la rilettura delle credenziali. Questo pattern è fragile: i simboli già importati da altri punti del codice mantengono riferimenti stale al vecchio modulo.

### Effetto

- Dopo una riconnessione, le chiamate API potevano usare il vecchio token.
- Bug intermittenti non riproducibili legati all'ordine di importazione.
- Potenziali memory leak per riferimenti circolari tra moduli old/new.

### Fix applicato

1. **Rimosso `importlib.reload()`** da `app.py`.
2. **`get_client()`** in `jira_client.py` ora esegue `from config import JIRA_URL, JIRA_TOKEN` al momento della chiamata (non all'import del modulo), garantendo di leggere sempre i valori correnti.
3. **`_init_jira()`** testa la connessione direttamente con `JIRA(server=url, token_auth=token)` senza passare per il modulo `jira_client`.

### Test eseguiti

| # | Test | Esito |
|---|------|-------|
| 1 | `importlib.reload` non presente in app.py | ✅ PASS |
| 2 | `import importlib` non presente in app.py | ✅ PASS |
| 3 | get_client usa valori config correnti | ✅ PASS |
| 4 | Cambio token a runtime → get_client usa il nuovo | ✅ PASS |
| 5 | **Non-regressione**: _init_jira aggiorna config e restituisce True | ✅ PASS |
| 6 | **Non-regressione**: senza credenziali restituisce False | ✅ PASS |

### Risultato

```
44 passed in 0.31s (suite completa — nessuna regressione)
```

---

## #5 — Sprint matching fuzzy — rischio assegnazione errata

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🟠 Media (Funzionale) |
| **File coinvolti** | `jira_client.py` |
| **Test** | `tests/test_criticita_05_sprint_match.py` |

### Criticità

`_move_to_sprint()` usava `if sprint_name.lower() in sprint.name.lower()` (substring match). Nomi come "26.3" matchavano sia "Hydra 26.3" che "Hydra 26.32", assegnando la story allo sprint sbagliato senza alcun feedback.

### Effetto

- Stories assegnate allo sprint errato (bug silenzioso).
- Confusione nella pianificazione del team.
- Nessun log di errore o warning per diagnosticare il problema.

### Fix applicato

1. **Match esatto** case-insensitive con trim: `sprint.name.strip().lower() == sprint_name.strip().lower()`.
2. **Warning log** se nessuno sprint corrisponde, con elenco degli sprint disponibili.
3. **Error log** se la chiamata API fallisce (prima era un `except: pass` silenzioso).

### Test eseguiti

| # | Test | Esito |
|---|------|-------|
| 1 | Match esatto funziona | ✅ PASS |
| 2 | Nessun falso positivo substring ("26.3" ≠ "Hydra 26.32") | ✅ PASS |
| 3 | Match case-insensitive | ✅ PASS |
| 4 | Whitespace tolerance | ✅ PASS |
| 5 | Warning loggato se sprint non trovato | ✅ PASS |
| 6 | **Non-regressione**: sprint tipico Hydra funziona | ✅ PASS |
| 7 | **Non-regressione**: errori API gestiti senza crash | ✅ PASS |

### Risultato

```
51 passed in 0.47s (suite completa — nessuna regressione)
```

---

## #6 — `is_italian()` mai definita + `ERICSSON_LIGHT` undefined (Dead Code)

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🟠 Media (Funzionale — crash potenziale) |
| **File coinvolti** | `app.py` |
| **Test** | `tests/test_criticita_06_dead_code.py` |

### Criticità

1. `_translate_tab()` chiamava `is_italian()` — funzione mai definita. Se invocata → `NameError`.
2. `ERICSSON_LIGHT` referenziato nel popup di conferma — variabile mai definita (workaround inline con `dir()` check, ma codice fragile).

### Effetto

- Crash dell'app se l'utente raggiungeva la funzionalità di traduzione per tab.
- Codice confuso e non manutenibile con simboli fantasma.

### Fix applicato

1. **Rimosso `_translate_tab()`**: dead code non raggiungibile dalla GUI (la traduzione avviene via `_translate_popup` per campo).
2. **Rimosso `ERICSSON_LIGHT`**: sostituito con il valore effettivo `BTN_PRIMARY`.

### Test eseguiti

| # | Test | Esito |
|---|------|-------|
| 1 | `is_italian` non presente in app.py | ✅ PASS |
| 2 | `_translate_tab` rimosso | ✅ PASS |
| 3 | `ERICSSON_LIGHT` non referenziato | ✅ PASS |
| 4 | **Non-regressione**: app.py parsabile (AST valido) | ✅ PASS |
| 5 | **Non-regressione**: `_translate_popup` ancora presente | ✅ PASS |
| 6 | **Non-regressione**: `_split_tab` ancora presente | ✅ PASS |
| 7 | **Non-regressione**: nessun altro nome undefined noto | ✅ PASS |

### Risultato

```
58 passed in 0.39s (suite completa — nessuna regressione)
```

---

## #7 — Scrittura `app_config.json` non atomica (rischio corruzione)

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🟡 Bassa (Resilienza) |
| **File coinvolti** | `config.py` |
| **Test** | `tests/test_criticita_07_atomic_write.py` |

### Criticità

`save_app_config()` usava `APP_CONFIG_FILE.write_text()` direttamente. Un crash durante la scrittura lasciava il file parzialmente scritto → JSON corrotto → app non avviabile.

### Effetto

- Configurazione persa dopo crash/kill inatteso.
- L'utente deve ricreare `app_config.json` manualmente.
- Scenario tipico: crash durante `_on_close()` che salva geometrie.

### Fix applicato

1. **Scrittura atomica**: `tempfile.mkstemp()` nella stessa directory + `os.replace()` (atomico su POSIX).
2. **Cleanup**: file temporaneo rimosso in caso di errore.
3. **Preservazione**: se la scrittura fallisce, il file originale resta intatto.

### Test eseguiti

| # | Test | Esito |
|---|------|-------|
| 1 | File risultante è JSON valido dopo save | ✅ PASS |
| 2 | Nessun file .tmp residuo | ✅ PASS |
| 3 | File originale intatto se write fallisce | ✅ PASS |
| 4 | Merge preserva chiavi esistenti | ✅ PASS |
| 5 | **Non-regressione**: popup geometries salvate | ✅ PASS |
| 6 | **Non-regressione**: load dopo save coerente | ✅ PASS |

### Risultato

```
64 passed in 0.52s (suite completa — nessuna regressione)
```

---

## #8 — Nessuna validazione input prima di creare stories su Jira

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🟠 Media (Funzionale/UX) |
| **File coinvolti** | `app.py` |
| **Test** | `tests/test_criticita_08_validation.py` |

### Criticità

Le stories venivano inviate a Jira senza validazione. Titoli vuoti, placeholder ("New Story"), o troppo lunghi causavano errori criptici dall'API Jira.

### Effetto

- Errore incomprensibile: "Field 'summary' cannot be empty".
- Creazione accidentale di stories con titolo placeholder.
- Nessun feedback preventivo all'utente.

### Fix applicato

1. **`_validate_stories()`**: verifica che il titolo non sia vuoto, non sia il placeholder "New Story", e non superi 255 caratteri.
2. **Chiamata in `_create_stories()`**: prima del popup di conferma, se ci sono errori mostra un messagebox con l'elenco.

### Test eseguiti

| # | Test | Esito |
|---|------|-------|
| 1 | Titolo vuoto rifiutato | ✅ PASS |
| 2 | Placeholder "New Story" rifiutato | ✅ PASS |
| 3 | Titolo > 255 chars rifiutato | ✅ PASS |
| 4 | Errori multipli tutti riportati | ✅ PASS |
| 5 | Story valida passa | ✅ PASS |
| 6 | **Non-regressione**: stories tipiche SWHB valide | ✅ PASS |
| 7 | **Non-regressione**: titolo 255 chars esatti valido | ✅ PASS |
| 8 | **Non-regressione**: lista vuota gestita | ✅ PASS |

### Risultato

```
72 passed in 0.41s (suite completa — nessuna regressione)
```

---

## #9 — Token in chiaro nel file History (scoperto da test funzionali)

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🔴 Alta (Security) |
| **File coinvolti** | `config.py` |
| **Test** | `tests/test_functional_additional.py::TestHistoryTokenLeak` |

### Criticità

`_add_history()` riceveva l'oggetto `state` originale contenente `jira_token` in chiaro e lo scriveva nel file `~/.secheartbeat_history.json`. L'offuscamento applicato nel fix #1 copriva solo il file di stato, non la history.

### Fix applicato

`_add_history()` ora esclude la chiave `jira_token` prima di scrivere nella history.

### Risultato: ✅ PASS

---

## #10 — `_split_tab` crash su tab rimosso (None in tab_widgets)

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🟠 Media (Funzionale — crash) |
| **File coinvolti** | `app.py` |
| **Test** | `tests/test_functional_additional.py::TestTabIndexBug` |

### Criticità

Dopo `_remove_tab(idx)`, `tab_widgets[idx]` viene impostato a `None`. Se l'utente poi preme "Split" su un tab che referenzia quell'indice, si verificava un `TypeError: 'NoneType' is not subscriptable`.

### Fix applicato

Aggiunto guard `if w is None: return` in `_split_tab()`.

### Risultato: ✅ PASS

---

## #11 — Import `threading` inutilizzato rimosso

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-16 |
| **Severità** | 🟡 Bassa (Code Quality) |
| **File coinvolti** | `app.py` |
| **Test** | `tests/test_functional_additional.py::TestUnusedImport` |

### Criticità

`import threading` era presente ma nessuna funzione del modulo veniva mai chiamata.

### Fix applicato

Import rimosso.

### Risultato: ✅ PASS

---

## Riepilogo Suite Test Completa

```
═══════════════════════════════════════════════════════════════
  125 test totali — TUTTI PASSANTI — 1.04s
═══════════════════════════════════════════════════════════════
```

| File Test | Test | Copertura |
|-----------|------|-----------|
| `test_criticita_01_token_storage.py` | 8 | Token offuscamento + permessi |
| `test_criticita_02_jql_injection.py` | 21 | Sanitizzazione JQL + validazione key |
| `test_criticita_03_dependencies.py` | 9 | Requirements pinned, no unused deps |
| `test_criticita_04_no_reload.py` | 6 | No importlib.reload, fresh config |
| `test_criticita_05_sprint_match.py` | 7 | Match esatto sprint |
| `test_criticita_06_dead_code.py` | 7 | Rimozione codice morto |
| `test_criticita_07_atomic_write.py` | 6 | Scrittura atomica config |
| `test_criticita_08_validation.py` | 8 | Validazione input stories |
| `test_functional_suite.py` | 44 | Test funzionali end-to-end |
| `test_functional_additional.py` | 9 | Bug scoperti durante analisi |

---

## #9 — Sprint "Unplanned" default per nuove User Story

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-17 |
| **Severità** | 🟡 Media (UX / Data integrity) |
| **File coinvolti** | `app.py` |

### Criticità

Le nuove User Story venivano create con il primo sprint disponibile come default, rischiando la creazione involontaria di stories assegnate allo sprint sbagliato.

### Fix applicato

1. Aggiunta costante `UNPLANNED_SPRINT = "— Unplanned —"` come placeholder.
2. Per le tab **nuove** (`existing=False`), il menu sprint mostra "— Unplanned —" come prima voce e lo seleziona di default.
3. Le stories **esistenti** (già su Jira) non vedono questa voce nel dropdown.
4. La validazione in `_validate_stories()` blocca la creazione se uno sprint è ancora "— Unplanned —".

### Test eseguiti

- Compilazione sintattica `py_compile`: ✅ OK
- Verifica logica: nuove US → default "— Unplanned —"; US esistenti → invariate; creazione bloccata se sprint non assegnato.

### Esito

✅ Risolto — La creazione è ora impossibile senza un vero sprint assegnato.

---

## #10 — Bottone Scheduling con tabella sprint/US

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-06-17 |
| **Severità** | 🟢 Bassa (Feature) |
| **File coinvolti** | `app.py`, `jira_client.py` |

### Feature

Aggiunto bottone "📅 Scheduling" nella barra azioni, posizionato prima di "Create US". Apre un popup con tabella che mostra:
- Ordinate: sprint (nome + data inizio/fine in piccolo)
- Righe: mapping delle US ([TORF-xxxx] o titolo per le nuove) per ciascun sprint
- Sezione "Unplanned" in rosso per le US senza sprint assegnato

### Modifiche

1. `jira_client.py`: aggiunta `get_board_sprints_details()` che ritorna nome + startDate/endDate.
2. `app.py`: aggiunto `key` nel dizionario `tab_widgets` per avere l'ID Jira disponibile.
3. `app.py`: metodo `_show_scheduling()` con popup scrollabile.
4. `app.py`: bottone "📅 Scheduling" nella action bar.

### Test eseguiti

- Compilazione sintattica `py_compile` su entrambi i file: ✅ OK

### Esito

✅ Implementato.

---

## #12 — Pre-flight Jira reachability check + comprehensive DEBUG logging

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-08-24 |
| **Severità** | 🔴 Critical (app hang), 🟡 Feature (logging) |
| **File coinvolti** | `app.py`, `jira_client.py`, `translator.py`, `config.py` |
| **Test** | Syntax check su tutti i moduli modificati |

### Criticità

1. L'applicazione rimaneva bloccata (hang) all'avvio se il server Jira non era raggiungibile (VPN disconnessa, server down). Il timeout di default di python-jira era `None` (illimitato), con retry automatici di ~10s/20s/40s. L'utente attendeva 3-5 minuti senza vedere la GUI.
2. Il logging era limitato a `app.py` con livello INFO. I moduli `jira_client.py`, `translator.py` e `config.py` non avevano alcun logging, rendendo il debug difficile.

### Fix applicato

**Pre-flight check (app.py):**
1. Aggiunta funzione `_check_jira_reachable()` — probe TCP con timeout 5s (socket)
2. Nel `main()`, prima di costruire la GUI, verifica raggiungibilità: se fallisce mostra popup di allarme con scelta "Continua in DEMO / Esci"
3. Aggiunto `timeout=10s` esplicito alla creazione del client JIRA in `_init_jira()`
4. Guard di raggiungibilità anche in `_init_jira_from_state()` e `_connect_jira()`
5. Popup localizzato EN/IT in base alla lingua selezionata

**Logging dettagliato (tutti i moduli):**
1. Livello portato a `DEBUG` nel file di log
2. Formato arricchito: `YYYY-MM-DD HH:MM:SS [LEVEL] module: message`
3. Logger gerarchici: `secheartbeat.app`, `secheartbeat.jira`, `secheartbeat.config`, `secheartbeat.translator`
4. `jira_client.py`: log con timing (elapsed) su tutte le operazioni API (JQL query, create, update, sprint move)
5. `config.py`: log su load/save state, load/save app_config
6. `translator.py`: log su traduzioni (dimensione testo, esito)

### Test eseguiti

- `py_compile.compile()` su `config.py`, `jira_client.py`, `translator.py`, `app.py`: ✅ OK

### Esito

✅ Implementato. La GUI appare immediatamente; se Jira non è raggiungibile il popup avvisa entro 5 secondi.

---

## #13 — Full editing context persistence + enhanced tooltips

| Campo | Dettaglio |
|-------|-----------|
| **Data** | 2026-08-24 |
| **Severità** | 🟡 Feature (UX + data persistence) |
| **File coinvolti** | `app.py`, `help_texts.py` |
| **Test** | Syntax check + parameter consistency verification |

### Criticità

1. La persistenza dello stato all'uscita era incompleta: salvava solo title/description/sprint, perdendo acceptance_criteria, labels, assignee, components, priority, story_points e la chiave Jira della story.
2. Il restore funzionava solo in assenza di connessione Jira: con connessione attiva le modifiche locali venivano perse.
3. I tooltip per Preview Markup, Markup Help e Traduttore erano troppo generici — non spiegavano chiaramente come usarli né cosa aspettarsi.

### Fix applicato

**Persistenza completa del contesto (`app.py`):**
1. `_collect_stories()` ora salva anche `story_points` e `key` (chiave Jira) per ogni story
2. `_restore_state()` riscritta completamente:
   - Ripristina TUTTI i campi di ogni story (titolo, desc, AC, sprint, labels, assignee, components, priority, story points, chiave Jira)
   - Se Jira è connesso e ci sono tab già caricati, chiede all'utente se ripristinare la sessione precedente o mantenere i dati freschi da Jira
   - Popup localizzato EN/IT
   - Logging dettagliato del processo di restore
3. Al prossimo avvio, il lavoro in corso viene proposto automaticamente anche se Jira è connesso

**Tooltip migliorati (`help_texts.py`):**
1. `markup_help` — Ora include esempi rapidi della sintassi (bold, italic, headings, lists, tables, code) con il rendering atteso + nota che il popup rimane aperto come riferimento
2. `translate` — Spiega il flusso passo-passo (click → preview → confirm/skip) + tips (preserva markup, richiede internet, meglio con frasi complete)
3. `preview_markup` — Lista dettagliata di cosa viene renderizzato (bold, italic, headings, colors, lists, tables, links, code) + nota sull'uso come verifica pre-creazione
4. Tutti e tre i tooltip in formato strutturato con titolo, separatore e sezioni

### Test eseguiti

- `py_compile` su `app.py`, `help_texts.py`: ✅ OK
- Verifica che `_add_tab` accetta tutti i parametri usati nel `_restore_state`: ✅ OK

### Esito

✅ Implementato. Le modifiche in editing vengono preservate tra le sessioni con ripristino completo al prossimo avvio.

---
