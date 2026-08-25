#!/usr/bin/env python3
"""Generate the user manual PDF for Security Heartbeat US Generator."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, Image, ListFlowable,
                                 ListItem, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus.flowables import HRFlowable
from pathlib import Path
import os

# Paths
BASE_DIR = Path(__file__).parent
ASSETS_DIR = BASE_DIR / "assets"
OUTPUT_PDF = BASE_DIR / "docs" / "Manuale_Utente_SecurityHeartbeat.pdf"
OUTPUT_PDF.parent.mkdir(exist_ok=True)

# Colors
ERICSSON_BLUE = HexColor("#001135")
ERICSSON_MID = HexColor("#003366")
ERICSSON_LIGHT = HexColor("#0082f0")
ACCENT = HexColor("#4fc3f7")
SUCCESS = HexColor("#26a69a")
WARN = HexColor("#ff7043")
LIGHT_BG = HexColor("#f0f4f8")

# Styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name='DocTitle', fontSize=24, leading=30, alignment=TA_CENTER,
    textColor=ERICSSON_BLUE, fontName='Helvetica-Bold', spaceAfter=10
))
styles.add(ParagraphStyle(
    name='DocSubtitle', fontSize=12, leading=16, alignment=TA_CENTER,
    textColor=HexColor("#555555"), fontName='Helvetica', spaceAfter=30
))
styles.add(ParagraphStyle(
    name='H1', fontSize=16, leading=20, textColor=ERICSSON_BLUE,
    fontName='Helvetica-Bold', spaceBefore=20, spaceAfter=10
))
styles.add(ParagraphStyle(
    name='H2', fontSize=13, leading=17, textColor=ERICSSON_MID,
    fontName='Helvetica-Bold', spaceBefore=15, spaceAfter=8
))
styles.add(ParagraphStyle(
    name='H3', fontSize=11, leading=14, textColor=HexColor("#003366"),
    fontName='Helvetica-Bold', spaceBefore=10, spaceAfter=5
))
styles.add(ParagraphStyle(
    name='Body', fontSize=10, leading=14, alignment=TA_JUSTIFY,
    textColor=black, fontName='Helvetica', spaceAfter=6
))
styles.add(ParagraphStyle(
    name='Note', fontSize=9, leading=12, textColor=HexColor("#555555"),
    fontName='Helvetica-Oblique', leftIndent=20, spaceAfter=6
))
styles.add(ParagraphStyle(
    name='CodeBlock', fontSize=9, leading=12, textColor=HexColor("#333333"),
    fontName='Courier', leftIndent=20, spaceAfter=6, backColor=LIGHT_BG
))
styles.add(ParagraphStyle(
    name='TableHeader', fontSize=9, leading=11, textColor=white,
    fontName='Helvetica-Bold', alignment=TA_CENTER
))
styles.add(ParagraphStyle(
    name='TableCell', fontSize=9, leading=11, textColor=black,
    fontName='Helvetica'
))


DOCS_DIR = BASE_DIR / "docs"


def add_screenshot(story, filename, caption, max_w=14*cm, max_h=10*cm):
    """Add a screenshot image with caption, fitting within max dimensions."""
    img_path = DOCS_DIR / filename
    if not img_path.exists():
        return
    from reportlab.lib.utils import ImageReader
    img_reader = ImageReader(str(img_path))
    iw, ih = img_reader.getSize()
    ratio_w = max_w / iw
    ratio_h = max_h / ih
    ratio = min(ratio_w, ratio_h)
    w, h = iw * ratio, ih * ratio
    story.append(Image(str(img_path), width=w, height=h))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(f"<i>{caption}</i>", styles['Note']))
    story.append(Spacer(1, 5*mm))


def build_pdf():
    doc = SimpleDocTemplate(str(OUTPUT_PDF), pagesize=A4,
                            leftMargin=2*cm, rightMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []

    # ========== COVER PAGE ==========
    story.append(Spacer(1, 3*cm))

    # Logo
    hydra_path = ASSETS_DIR / "hydra_d.png"
    if hydra_path.exists():
        story.append(Image(str(hydra_path), width=3*cm, height=3*cm))
        story.append(Spacer(1, 1*cm))

    story.append(Paragraph("Security Heartbeat US Generator", styles['DocTitle']))
    story.append(Paragraph("Manuale Utente — v1.1.0", styles['DocSubtitle']))
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="60%", thickness=2, color=ERICSSON_LIGHT))
    story.append(Spacer(1, 1*cm))
    story.append(Paragraph("Team Hydra — Ericsson", styles['DocSubtitle']))
    story.append(Paragraph("Giugno 2026", styles['DocSubtitle']))
    story.append(PageBreak())

    # ========== TABLE OF CONTENTS ==========
    story.append(Paragraph("Indice", styles['H1']))
    toc_items = [
        "1. Introduzione",
        "2. Concetti Base: Epiche e User Stories in Jira",
        "3. Requisiti e Installazione",
        "4. Configurazione",
        "5. Primo Avvio e Connessione a Jira",
        "6. Interfaccia — Panoramica",
        "7. Pannello Sinistro: Selezione Epica e Lista Storie",
        "8. Pannello Destro: Dettaglio User Story",
        "9. Operazioni Principali",
        "10. Indicatore di Stato",
        "11. File di Log",
        "12. Traduzione IT→EN",
        "13. Risoluzione Problemi",
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles['Body']))
    story.append(PageBreak())

    # ========== 1. INTRODUZIONE ==========
    story.append(Paragraph("1. Introduzione", styles['H1']))
    story.append(Paragraph(
        "Il <b>Security Heartbeat US Generator</b> è un'applicazione desktop che automatizza "
        "la creazione e gestione delle User Stories Jira per le attività ricorrenti di test "
        "del Security Heartbeat nelle release ENM/cENM.", styles['Body']))
    story.append(Paragraph(
        "Per ogni nuova release, il team deve creare un insieme di User Stories identiche nella "
        "struttura ma con riferimenti aggiornati (sprint, epica, assegnatari). Questo tool "
        "elimina il lavoro manuale ripetitivo garantendo consistenza.", styles['Body']))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph("<b>Cosa fa l'applicazione:</b>", styles['Body']))
    story.append(ListFlowable([
        ListItem(Paragraph("Si connette a Jira e carica le Epiche Security Heartbeat", styles['Body'])),
        ListItem(Paragraph("Mostra le User Stories associate a ciascuna Epica", styles['Body'])),
        ListItem(Paragraph("Permette di modificare, clonare e creare nuove storie in batch", styles['Body'])),
        ListItem(Paragraph("Traduce automaticamente i contenuti da italiano a inglese", styles['Body'])),
        ListItem(Paragraph("Salva i dati in formato JSON per revisione pre-creazione", styles['Body'])),
    ], bulletType='bullet', start='•'))

    # ========== 2. CONCETTI BASE ==========
    story.append(Paragraph("2. Concetti Base: Epiche e User Stories in Jira", styles['H1']))
    story.append(Paragraph(
        "Se non hai familiarità con Jira, ecco i concetti fondamentali:", styles['Body']))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("<b>Epic (Epica)</b>", styles['H3']))
    story.append(Paragraph(
        "Un'Epica è un contenitore che raggruppa più User Stories correlate. "
        "Nel nostro caso, ogni release ENM ha un'epica chiamata "
        "\"Security heartbeat recurrent test activities for [release]\". "
        "L'epica rappresenta l'obiettivo complessivo di quella release.", styles['Body']))

    story.append(Paragraph("<b>User Story (Storia Utente)</b>", styles['H3']))
    story.append(Paragraph(
        "Una User Story è un'unità di lavoro assegnabile a una persona. "
        "Ogni story ha un titolo, una descrizione dettagliata, criteri di accettazione, "
        "uno sprint di riferimento, un assegnatario, labels e priorità. "
        "Le stories sono collegate alla loro epica padre tramite il campo \"Epic Link\".", styles['Body']))

    story.append(Paragraph("<b>Sprint</b>", styles['H3']))
    story.append(Paragraph(
        "Uno Sprint è un periodo di tempo (tipicamente 2-3 settimane) durante il quale "
        "il team lavora sulle stories assegnate. Ogni story viene associata a uno sprint "
        "specifico dalla board del team.", styles['Body']))

    story.append(Paragraph("<b>Status (Stato)</b>", styles['H3']))
    story.append(Paragraph(
        "Ogni story ha uno stato che indica il suo avanzamento: Open (aperta, modificabile), "
        "In Progress (in lavorazione), Done/Closed (completata). "
        "In questa applicazione, <b>solo le stories con stato Open o non ancora create sono modificabili</b>.", styles['Body']))

    # ========== 3. REQUISITI ==========
    story.append(PageBreak())
    story.append(Paragraph("3. Requisiti e Installazione", styles['H1']))
    story.append(Paragraph("<b>Requisiti:</b>", styles['H2']))
    story.append(ListFlowable([
        ListItem(Paragraph("Python 3.10 o superiore", styles['Body'])),
        ListItem(Paragraph("Accesso alla rete Ericsson (Jira eteamproject-alpha)", styles['Body'])),
        ListItem(Paragraph("Un Personal Access Token (PAT) Jira", styles['Body'])),
    ], bulletType='bullet', start='•'))

    story.append(Paragraph("<b>Dipendenze di sistema (Ubuntu/Debian):</b>", styles['H2']))
    story.append(Paragraph(
        "L'applicazione utilizza librerie Python che richiedono pacchetti di sistema "
        "non sempre preinstallati. Su Ubuntu/Debian è necessario installarli prima di "
        "procedere con <font name='Courier'>pip install</font>:", styles['Body']))
    story.append(Spacer(1, 3*mm))

    deps_data = [
        [Paragraph("<b>Pacchetto</b>", styles['TableHeader']),
         Paragraph("<b>Necessario per</b>", styles['TableHeader'])],
        ["python3-tk", "GUI dell'applicazione (tkinter non è incluso in tutte le installazioni Python)"],
        ["libcairo2-dev", "Rendering SVG → PNG (logo Ericsson) tramite cairosvg"],
        ["libffi-dev", "Compilazione estensioni native richieste da cairosvg"],
        ["python3-dev", "Headers Python per compilare Pillow e cairosvg"],
    ]
    deps_table = Table(deps_data, colWidths=[4*cm, 12*cm])
    deps_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ERICSSON_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(deps_table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "sudo apt install python3-tk libcairo2-dev libffi-dev python3-dev", styles['CodeBlock']))
    story.append(Paragraph(
        "<i>Nota: sulle workstation Ericsson preconfigurate questi pacchetti sono generalmente già presenti. "
        "Verificare solo in caso di errore durante l'installazione delle dipendenze Python.</i>",
        styles['Note']))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("<b>Installazione:</b>", styles['H2']))
    story.append(Paragraph("git clone https://github.com/MarcoIppo/SecurityHeartbeat.git", styles['CodeBlock']))
    story.append(Paragraph("cd SecurityHeartbeat", styles['CodeBlock']))
    story.append(Paragraph("python3 -m venv .venv", styles['CodeBlock']))
    story.append(Paragraph("source .venv/bin/activate", styles['CodeBlock']))
    story.append(Paragraph("pip install -r requirements.txt", styles['CodeBlock']))

    story.append(Paragraph("<b>Avvio:</b>", styles['H2']))
    story.append(Paragraph("./run.sh          # Interfaccia in inglese", styles['CodeBlock']))
    story.append(Paragraph("./run.sh --ita    # Interfaccia in italiano", styles['CodeBlock']))

    # ========== 4. CONFIGURAZIONE ==========
    story.append(Paragraph("4. Configurazione", styles['H1']))
    story.append(Paragraph(
        "Il file <font name='Courier'>app_config.json</font> contiene tutte le impostazioni:", styles['Body']))

    config_data = [
        [Paragraph("<b>Parametro</b>", styles['TableHeader']),
         Paragraph("<b>Descrizione</b>", styles['TableHeader']),
         Paragraph("<b>Default</b>", styles['TableHeader'])],
        ["jira_url", "URL del server Jira Ericsson", "https://eteamproject-alpha..."],
        ["project", "Codice progetto Jira", "TORF"],
        ["issuetype", "Tipo issue per le epiche", "Epic"],
        ["summary_contains", "Pattern per trovare le epiche", "Security heartbeat..."],
        ["story_issuetype", "Tipo issue per le stories", "Story"],
        ["max_epics", "Numero massimo di epiche da caricare", "5"],
        ["team_name", "Nome del team", "Hydra"],
        ["board_id", "ID della board Agile del team", "38770"],
    ]
    config_table = Table(config_data, colWidths=[3.5*cm, 8*cm, 4.5*cm])
    config_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ERICSSON_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(config_table)

    # ========== 5. PRIMO AVVIO ==========
    story.append(PageBreak())
    story.append(Paragraph("5. Primo Avvio e Connessione a Jira", styles['H1']))
    story.append(Paragraph(
        "Al primo avvio l'applicazione è in modalità <b>DEMO</b> (indicato nella barra di stato). "
        "Per attivare tutte le funzionalità è necessario connettersi a Jira.", styles['Body']))

    story.append(Paragraph("<b>Come creare il Token PAT:</b>", styles['H2']))
    story.append(ListFlowable([
        ListItem(Paragraph("Apri Jira nel browser", styles['Body'])),
        ListItem(Paragraph("Clicca la tua icona profilo (in alto a destra)", styles['Body'])),
        ListItem(Paragraph("Seleziona <b>Personal Access Tokens</b>", styles['Body'])),
        ListItem(Paragraph("Clicca <b>Create token</b>", styles['Body'])),
        ListItem(Paragraph("Dai un nome al token (es. \"Heartbeat App\")", styles['Body'])),
        ListItem(Paragraph("Copia il token generato", styles['Body'])),
        ListItem(Paragraph("Incollalo nel campo <b>API Token</b> nell'applicazione", styles['Body'])),
        ListItem(Paragraph("Clicca <b>🔗 Connect</b>", styles['Body'])),
    ], bulletType='1'))
    story.append(Paragraph(
        "<i>Nota: il token viene salvato tra le sessioni. Non è necessario reinserirlo ogni volta.</i>",
        styles['Note']))
    add_screenshot(story, "CreateTocken.png", "Fig. 2 — Tooltip con istruzioni per la creazione del token PAT")

    # ========== 6. INTERFACCIA ==========
    story.append(Paragraph("6. Interfaccia — Panoramica", styles['H1']))
    story.append(Paragraph(
        "L'interfaccia è divisa in aree funzionali:", styles['Body']))

    # Screenshot
    screenshot_path = BASE_DIR / "docs" / "Screenshot_20260608_094628.png"
    if screenshot_path.exists():
        # Fit to page width preserving aspect ratio
        from reportlab.lib.utils import ImageReader
        img_reader = ImageReader(str(screenshot_path))
        iw, ih = img_reader.getSize()
        max_width = 16 * cm
        ratio = max_width / iw
        img_height = ih * ratio
        if img_height > 12 * cm:
            img_height = 12 * cm
            ratio = img_height / ih
            max_width = iw * ratio
        story.append(Image(str(screenshot_path), width=max_width, height=img_height))
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(
            "<i>Fig. 1 — Schermata principale dell'applicazione</i>", styles['Note']))
        story.append(Spacer(1, 5*mm))

    # UI Layout diagram as table
    layout_data = [
        [Paragraph("<b>BANNER</b> — Logo Hydra + Titolo App + Logo Ericsson", styles['TableCell'])],
        [Paragraph("<b>PANNELLO SINISTRO</b>\n• Selezione Epica\n• Descrizione Epica\n• Lista US con checkbox\n• Bottoni: + Add Story, Load Stories"
                   + "        |        " +
                   "<b>PANNELLO DESTRO</b>\n• Tab per ogni User Story\n• Campi editabili\n• Bottoni: Split, Remove", styles['TableCell'])],
        [Paragraph("<b>BARRA AZIONI</b> — 🚀 Create US | 💾 Save US | 📋 History | ⏻ Quit", styles['TableCell'])],
        [Paragraph("<b>BARRA CREDENZIALI</b> — 🔐 Jira: [API Token] [🔗 Connect]", styles['TableCell'])],
        [Paragraph("<b>BARRA DI STATO</b> — ● Indicatore | Stato | Log file", styles['TableCell'])],
    ]
    layout_table = Table(layout_data, colWidths=[16*cm])
    layout_table.setStyle(TableStyle([
        ('GRID', (0, 0), (-1, -1), 1, ERICSSON_LIGHT),
        ('BACKGROUND', (0, 0), (0, 0), HexColor("#e3f2fd")),
        ('BACKGROUND', (0, 2), (0, 2), HexColor("#e8f5e9")),
        ('BACKGROUND', (0, 3), (0, 3), HexColor("#fff3e0")),
        ('BACKGROUND', (0, 4), (0, 4), HexColor("#f3e5f5")),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(layout_table)

    # ========== 7. PANNELLO SINISTRO ==========
    story.append(PageBreak())
    story.append(Paragraph("7. Pannello Sinistro: Selezione Epica e Lista Storie", styles['H1']))

    story.append(Paragraph("<b>Lista Epiche</b>", styles['H2']))
    story.append(Paragraph(
        "Mostra le ultime N epiche Security Heartbeat caricate da Jira, ordinate dalla più recente.", styles['Body']))
    story.append(ListFlowable([
        ListItem(Paragraph("🟢 = Epica aperta (è possibile creare stories)", styles['Body'])),
        ListItem(Paragraph("🔴 = Epica risolta/chiusa (solo lettura)", styles['Body'])),
    ], bulletType='bullet', start='•'))

    story.append(Paragraph("<b>Logica di selezione:</b>", styles['H3']))
    story.append(ListFlowable([
        ListItem(Paragraph("Se selezioni l'<b>ultima epica</b> (la prima in lista) e ha stories → le mostra", styles['Body'])),
        ListItem(Paragraph("Se l'ultima epica <b>non ha stories</b> → mostra quelle della penultima come template editabili", styles['Body'])),
        ListItem(Paragraph("Se selezioni un'<b>epica più vecchia</b> → mostra le sue stories con checkbox deselezionati e il bottone \"➕ Add\" per ri-linkarle all'ultima epica", styles['Body'])),
    ], bulletType='bullet', start='•'))

    story.append(Paragraph("<b>Lista User Stories</b>", styles['H2']))
    story.append(Paragraph(
        "Sotto la descrizione dell'epica, ogni story è mostrata con un checkbox. "
        "Cliccando su una story, il tab corrispondente nel pannello destro viene selezionato.", styles['Body']))

    story.append(Paragraph("<b>Bottoni:</b>", styles['H2']))
    btn_data = [
        [Paragraph("<b>Bottone</b>", styles['TableHeader']),
         Paragraph("<b>Funzione</b>", styles['TableHeader'])],
        ["+ Add Story", "Aggiunge una nuova story vuota (nuovo tab)"],
        ["📥 Load Stories", "Ricarica le stories dall'epica selezionata"],
        ["➕ Add selected to [EPIC]", "Appare solo con epiche vecchie: ri-linka le stories selezionate all'ultima epica"],
    ]
    btn_table = Table(btn_data, colWidths=[5*cm, 11*cm])
    btn_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ERICSSON_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(btn_table)
    add_screenshot(story, "Add User Story to Epic.png", "Fig. 3 — Bottone 'Add to Epic' visibile con epiche più vecchie")

    # ========== 8. PANNELLO DESTRO ==========
    story.append(PageBreak())
    story.append(Paragraph("8. Pannello Destro: Dettaglio User Story", styles['H1']))
    story.append(Paragraph(
        "Ogni User Story è mostrata in un tab separato. I campi disponibili sono:", styles['Body']))

    fields_data = [
        [Paragraph("<b>Campo</b>", styles['TableHeader']),
         Paragraph("<b>Descrizione</b>", styles['TableHeader']),
         Paragraph("<b>Editabile</b>", styles['TableHeader'])],
        ["🔑 Key", "Identificativo Jira (es. TORF-123456). Auto-generato.", "No"],
        ["● Status", "Stato corrente della story (Open, In Progress, Done...)", "No"],
        ["Title (Titolo)", "Il titolo/sommario della story come apparirà in Jira", "Sì*"],
        ["Description (Descrizione)", "Descrizione dettagliata in formato Jira wiki markup", "Sì*"],
        ["Acceptance Criteria", "Condizioni che devono essere soddisfatte per chiudere la story", "Sì*"],
        ["Sprint", "Sprint di assegnazione (dropdown dalla board del team)", "Sì*"],
        ["Labels", "Etichette separate da virgola (es. 25.10,Hydra)", "Sì*"],
        ["Assignee", "Username Jira (signum) dell'assegnatario", "Sì*"],
        ["Components", "Componenti Jira, separati da virgola", "Sì*"],
        ["Priority", "Priorità (Minor, Major, Critical, Blocker)", "Sì*"],
    ]
    fields_table = Table(fields_data, colWidths=[4*cm, 9*cm, 2.5*cm])
    fields_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ERICSSON_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(fields_table)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "<i>* Editabile solo se la story è in stato Open oppure non ancora creata in Jira. "
        "Le stories in stato diverso da Open sono visualizzate in sola lettura.</i>", styles['Note']))

    story.append(Paragraph("<b>Bottoni per tab:</b>", styles['H2']))
    tab_btn_data = [
        [Paragraph("<b>Bottone</b>", styles['TableHeader']),
         Paragraph("<b>Funzione</b>", styles['TableHeader'])],
        ["⊕ Split", "Duplica la story in un nuovo tab (utile per dividere storie troppo grandi)"],
        ["✕ Remove", "Rimuove il tab (non elimina da Jira)"],
        ["IT→EN", "Apre un popup con la traduzione del campo (conferma o annulla)"],
        ["?", "Mostra la guida alla sintassi Jira wiki markup"],
    ]
    tab_btn_table = Table(tab_btn_data, colWidths=[3.5*cm, 12.5*cm])
    tab_btn_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ERICSSON_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(tab_btn_table)
    add_screenshot(story, "MarkUp help.png", "Fig. 4 — Popup di aiuto sulla sintassi Jira Markup")

    # ========== 9. OPERAZIONI PRINCIPALI ==========
    story.append(PageBreak())
    story.append(Paragraph("9. Operazioni Principali", styles['H1']))

    story.append(Paragraph("<b>🚀 Create User Stories</b>", styles['H2']))
    story.append(Paragraph(
        "Crea tutte le stories visualizzate nei tab su Jira, linkandole all'epica selezionata. "
        "Prima della creazione viene mostrato un dialogo di conferma con l'elenco.", styles['Body']))
    story.append(Paragraph(
        "I campi scritti su Jira sono: Summary, Description, Acceptance Criteria (campo custom dedicato), "
        "Sprint, Labels, Assignee, Components, Priority, Epic Link.", styles['Body']))
    add_screenshot(story, "CreationConfirm.png", "Fig. 5 — Dialogo di conferma creazione User Stories")

    story.append(Paragraph("<b>💾 Save US</b>", styles['H2']))
    story.append(Paragraph(
        "Esporta tutte le stories in un file JSON per revisione prima della creazione. "
        "Utile per condividere il piano con il team o come backup.", styles['Body']))

    story.append(Paragraph("<b>➕ Add selected to [EPIC]</b>", styles['H2']))
    story.append(Paragraph(
        "Visibile solo quando si seleziona un'epica più vecchia. Le stories selezionate "
        "(con checkbox) vengono ri-linkate all'ultima epica: se la story ha già un key Jira, "
        "viene aggiornato il campo Epic Link; se è un template, viene creata come nuova.", styles['Body']))

    story.append(Paragraph("<b>📋 History</b>", styles['H2']))
    story.append(Paragraph(
        "Mostra il changelog delle versioni dell'applicazione.", styles['Body']))

    story.append(Paragraph("<b>Ctrl+S</b>", styles['H2']))
    story.append(Paragraph(
        "Salva lo stato corrente (epica selezionata, stories, token) per il prossimo avvio.", styles['Body']))

    # ========== 10. INDICATORE DI STATO ==========
    story.append(Paragraph("10. Indicatore di Stato", styles['H1']))
    story.append(Paragraph(
        "Nella barra di stato in basso a sinistra è presente un pallino colorato:", styles['Body']))

    ind_data = [
        [Paragraph("<b>Colore</b>", styles['TableHeader']),
         Paragraph("<b>Stato</b>", styles['TableHeader']),
         Paragraph("<b>Significato</b>", styles['TableHeader'])],
        ["🟡 Giallo (lampeggiante)", "Loading", "Lettura User Stories in corso da Jira"],
        ["🟢 Verde (fisso)", "OK", "Lettura completata, dati aggiornati"],
        ["🔴 Rosso (fisso)", "Errore", "Timeout o errore nella lettura da Jira"],
        ["⚫ Grigio", "Idle", "Nessuna operazione in corso"],
    ]
    ind_table = Table(ind_data, colWidths=[4.5*cm, 2.5*cm, 9*cm])
    ind_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ERICSSON_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(ind_table)
    story.append(Paragraph(
        "<i>Passando il mouse sull'indicatore appare un tooltip con il dettaglio dello stato.</i>",
        styles['Note']))
    add_screenshot(story, "Updated UserStories.png", "Fig. 6 — Indicatore verde: User Stories aggiornate")

    # ========== 11. FILE DI LOG ==========
    story.append(Paragraph("11. File di Log", styles['H1']))
    story.append(Paragraph(
        "L'applicazione scrive tutte le operazioni nel file:", styles['Body']))
    story.append(Paragraph("<b>securityHeartbeatGenerator.log</b>", styles['CodeBlock']))
    story.append(Paragraph(
        "Il file si trova nella directory dell'applicazione e viene <b>svuotato ad ogni avvio</b>. "
        "Contiene:", styles['Body']))
    story.append(ListFlowable([
        ListItem(Paragraph("Header con configurazione (versione, utente, URL Jira, progetto, team...)", styles['Body'])),
        ListItem(Paragraph("Operazioni di caricamento epiche e stories", styles['Body'])),
        ListItem(Paragraph("Operazioni di creazione/re-link stories", styles['Body'])),
        ListItem(Paragraph("Errori e warning", styles['Body'])),
    ], bulletType='bullet', start='•'))
    story.append(Paragraph(
        "Il nome del file è sempre visibile nella barra di stato in basso a destra.", styles['Body']))

    # ========== 12. TRADUZIONE ==========
    story.append(Paragraph("12. Traduzione IT→EN", styles['H1']))
    story.append(Paragraph(
        "Ogni campo di testo (Description, Acceptance Criteria) ha un bottone <b>IT→EN</b> "
        "che traduce il contenuto dall'italiano all'inglese usando Google Translate.", styles['Body']))
    story.append(Paragraph("<b>Flusso:</b>", styles['H3']))
    story.append(ListFlowable([
        ListItem(Paragraph("Clicca IT→EN accanto al campo", styles['Body'])),
        ListItem(Paragraph("Si apre un popup con l'anteprima della traduzione", styles['Body'])),
        ListItem(Paragraph("<b>✓ Confirm</b> → sostituisce il testo originale con la traduzione", styles['Body'])),
        ListItem(Paragraph("<b>✗ Skip</b> → chiude il popup senza modificare nulla", styles['Body'])),
    ], bulletType='1'))
    add_screenshot(story, "TranslateFunction.png", "Fig. 7 — Popup di traduzione IT→EN con anteprima")

    # ========== 13. RISOLUZIONE PROBLEMI ==========
    story.append(PageBreak())
    story.append(Paragraph("13. Risoluzione Problemi", styles['H1']))

    faq_data = [
        [Paragraph("<b>Problema</b>", styles['TableHeader']),
         Paragraph("<b>Soluzione</b>", styles['TableHeader'])],
        ["Mode: DEMO nella status bar",
         "Non sei connesso a Jira. Inserisci il token e clicca Connect."],
        ["Connection failed",
         "Verifica: 1) di essere sulla rete Ericsson (VPN) 2) che il token sia valido 3) che jira_url in app_config.json sia corretto"],
        ["Stories non si aggiornano",
         "Seleziona l'epica e clicca '📥 Load Stories' per ricaricare"],
        ["Campi non editabili",
         "La story è in stato diverso da Open, oppure l'epica è risolta. Solo stories Open o nuove sono modificabili."],
        ["Indicatore rosso",
         "Errore di comunicazione con Jira. Controlla il file di log per dettagli."],
        ["Token scaduto",
         "Crea un nuovo token su Jira (Profile → Personal Access Tokens) e reinseriscilo."],
    ]
    faq_table = Table(faq_data, colWidths=[5*cm, 11*cm])
    faq_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), ERICSSON_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor("#cccccc")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [white, LIGHT_BG]),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(faq_table)

    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=ERICSSON_LIGHT))
    story.append(Spacer(1, 5*mm))
    story.append(Paragraph(
        "<i>Documento generato automaticamente — Security Heartbeat US Generator v1.1.0 — Team Hydra, Ericsson</i>",
        styles['Note']))

    # Build
    doc.build(story)
    print(f"✓ PDF generato: {OUTPUT_PDF}")


if __name__ == "__main__":
    build_pdf()
