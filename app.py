#!/usr/bin/env python3
"""Security Heartbeat User Story Generator - GUI Application (tkinter)."""
import sys
import os
import logging
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime

from config import load_state, save_state, load_history, VERSION, APP_TITLE, APP_DESC
from config import JIRA_URL, JIRA_TOKEN, TEAM_NAME
from i18n import get_strings
from translator import translate_to_english

# --- LOG setup (cleared on each launch) ---
LOG_FILE = Path(__file__).parent / "securityHeartbeatGenerator.log"
LOG_FILE.write_text("")  # clear on launch
logging.basicConfig(
    filename=str(LOG_FILE), level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s", datefmt="%H:%M:%S"
)
log = logging.getLogger("secheartbeat")

# Log app configuration header
from config import JIRA_PROJECT, BOARD_ID, MAX_EPICS, EPIC_NAME_PATTERN
log.info("=" * 60)
log.info(f"  {APP_TITLE} v{VERSION}")
log.info(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
log.info(f"  User: {os.environ.get('USER', os.environ.get('USERNAME', 'unknown'))}")
log.info(f"  Language: {'IT' if '--ita' in sys.argv else 'EN'}")
log.info(f"  Jira URL: {JIRA_URL or '(not set)'}")
log.info(f"  Jira Token: {'***' if JIRA_TOKEN else '(not set)'}")
log.info(f"  Project: {JIRA_PROJECT}")
log.info(f"  Team: {TEAM_NAME}")
log.info(f"  Board ID: {BOARD_ID}")
log.info(f"  Max Epics: {MAX_EPICS}")
log.info(f"  Epic Pattern: {EPIC_NAME_PATTERN}")
log.info("=" * 60)


class ToolTip:
    """Simple tooltip on hover for tkinter widgets."""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None):
        x = self.widget.winfo_rootx() + 20
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        lbl = tk.Label(self.tip, text=self.text, font=("Consolas", 9),
                       bg="#333333", fg="#ffffff", padx=8, pady=5,
                       wraplength=350, justify="left")
        lbl.pack()
        # Ensure tooltip stays within screen bounds
        self.tip.update_idletasks()
        sw = self.tip.winfo_screenwidth()
        sh = self.tip.winfo_screenheight()
        tw = self.tip.winfo_width()
        th = self.tip.winfo_height()
        if x + tw > sw:
            x = sw - tw - 5
        if y + th > sh:
            y = self.widget.winfo_rooty() - th - 2
        self.tip.wm_geometry(f"+{x}+{y}")

    def _hide(self, event=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None

LANG = "it" if "--ita" in sys.argv else "en"
S = get_strings(LANG)

ASSETS_DIR = Path(__file__).parent / "assets"

# Colors - Ericsson brand inspired
BG_DARK = "#001135"       # Ericsson dark navy
BG_PANEL = "#002255"      # Ericsson deep blue
BG_CARD = "#003366"       # Ericsson primary blue
FG_TEXT = "#f2f2f2"       # Near white
FG_TITLE = "#4fc3f7"      # Ericsson light blue accent
FG_ACCENT = "#29b6f6"     # Ericsson secondary blue
FG_WARN = "#ff7043"       # Warm orange warning
BTN_PRIMARY = "#0082f0"   # Ericsson blue
BTN_SUCCESS = "#26a69a"   # Teal green
BTN_DANGER = "#ef5350"    # Red
BTN_INFO = "#5c6bc0"      # Indigo
BORDER_COLOR = "#0082f0"  # Ericsson blue

JIRA_MARKUP_HELP = (
    "╔════════════════════════════════════════╗\n"
    "║   JIRA / CONFLUENCE MARKUP SYNTAX     ║\n"
    "╚════════════════════════════════════════╝\n"
    "\n"
    "┌─── Text Formatting ──────────────────┐\n"
    "│  *bold*            → bold            │\n"
    "│  _italic_          → italic          │\n"
    "│  -strikethrough-   → strikethrough   │\n"
    "│  +underline+       → underline       │\n"
    "│  {{monospace}}     → monospace       │\n"
    "│  ??citation??      → citation        │\n"
    "└──────────────────────────────────────┘\n"
    "\n"
    "┌─── Headings ─────────────────────────┐\n"
    "│  h1. Title         h2. Subtitle      │\n"
    "│  h3. Section       h4. Subsection    │\n"
    "└──────────────────────────────────────┘\n"
    "\n"
    "┌─── Lists ────────────────────────────┐\n"
    "│  * bullet          # numbered        │\n"
    "│  ** sub-bullet     ## sub-numbered   │\n"
    "└──────────────────────────────────────┘\n"
    "\n"
    "┌─── Links & Media ────────────────────┐\n"
    "│  [title|http://url]                  │\n"
    "│  !image.png!       !img|width=300!   │\n"
    "└──────────────────────────────────────┘\n"
    "\n"
    "┌─── Blocks ───────────────────────────┐\n"
    "│  {code}...{code}     code block      │\n"
    "│  {quote}...{quote}   quote block     │\n"
    "│  {noformat}...{noformat} preformat   │\n"
    "│  {color:red}text{color} colored      │\n"
    "└──────────────────────────────────────┘\n"
    "\n"
    "┌─── Tables ───────────────────────────┐\n"
    "│  ||header 1||header 2||              │\n"
    "│  |cell 1   |cell 2   |              │\n"
    "└──────────────────────────────────────┘\n"
    "\n"
    "  ----  → horizontal rule\n"
)

# Check Jira availability - deferred to after GUI init
JIRA_AVAILABLE = False


def _init_jira(url, user, token):
    global JIRA_AVAILABLE
    if url and token:
        try:
            import config
            config.JIRA_URL = url
            config.JIRA_TOKEN = token
            import importlib
            import jira_client
            importlib.reload(jira_client)
            client = jira_client.get_client()
            client.myself()
            JIRA_AVAILABLE = True
            log.info("Jira connection established")
            return True
        except Exception as e:
            err = str(e)[:200]
            log.error(f"Jira init error: {err}")
            JIRA_AVAILABLE = False
    else:
        JIRA_AVAILABLE = False
    return False


class SecurityHeartbeatApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{APP_TITLE} v{VERSION}")
        self.root.geometry("1200x850")
        self.root.configure(bg=BG_DARK)
        self.root.minsize(1000, 700)

        self.epics = []
        self.selected_epic = None
        self.story_tabs = []  # list of dicts: {title, description, sprint}
        self.story_checkboxes = []  # (var, story_data)
        self.tab_widgets = []  # list of widget refs per tab
        self.sprints = []  # sprint names from board
        self._epic_stories_cache = {}  # epic_key -> list of stories
        self._add_to_epic_btn = None
        self._blink_id = None  # after() id for blinking
        self._popups = {}  # track open popups by type

        self._setup_style()
        self._load_logos()
        self._build_banner()
        self._build_main()
        self._build_credentials_panel()
        self._build_status_bar()

        self._init_jira_from_state()
        self._load_sprints()
        self._load_epics()
        self._restore_state()

        log.info("Application started")

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Control-s>", lambda e: self._save())
        self.root.bind("<Control-q>", lambda e: self._on_close())

    def _setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=BG_DARK, borderwidth=0)
        style.configure("TNotebook.Tab", background=BG_CARD, foreground=FG_TEXT,
                        padding=[8, 3], font=("Segoe UI", 7))
        style.map("TNotebook.Tab",
                  background=[("selected", BTN_PRIMARY)],
                  foreground=[("selected", "#ffffff")])
        style.configure("TFrame", background=BG_DARK)
        style.configure("Card.TFrame", background=BG_CARD)
        style.configure("TLabel", background=BG_DARK, foreground=FG_TEXT, font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=BG_DARK, foreground=FG_TITLE,
                        font=("Segoe UI", 14, "bold"))
        style.configure("TCheckbutton", background=BG_PANEL, foreground=FG_TEXT,
                        font=("Segoe UI", 9))

    def _load_logos(self):
        self.hydra_img = None
        self.ericsson_img = None
        try:
            from PIL import Image, ImageTk
            # Hydra logo (PNG)
            hydra_path = ASSETS_DIR / "hydra_d.png"
            if hydra_path.exists():
                img = Image.open(hydra_path).resize((48, 48), Image.LANCZOS)
                self.hydra_img = ImageTk.PhotoImage(img)

            # Ericsson logo (SVG -> PNG via cairosvg)
            ericsson_path = ASSETS_DIR / "elogo.svg"
            if ericsson_path.exists():
                try:
                    import cairosvg
                    import io
                    png_data = cairosvg.svg2png(url=str(ericsson_path), output_width=48, output_height=48)
                    img = Image.open(io.BytesIO(png_data)).resize((48, 48), Image.LANCZOS)
                    self.ericsson_img = ImageTk.PhotoImage(img)
                except Exception:
                    pass
        except ImportError:
            pass

    def _build_banner(self):
        banner = tk.Frame(self.root, bg=BG_PANEL, height=70, bd=0,
                          highlightbackground=BORDER_COLOR, highlightthickness=1)
        banner.pack(fill="x", padx=5, pady=(5, 0))
        banner.pack_propagate(False)

        # Left logo
        if self.hydra_img:
            lbl = tk.Label(banner, image=self.hydra_img, bg=BG_PANEL)
            lbl.pack(side="left", padx=10)

        # Center text
        center = tk.Frame(banner, bg=BG_PANEL)
        center.pack(side="left", expand=True, fill="both")
        tk.Label(center, text=APP_TITLE, font=("Segoe UI", 16, "bold"),
                 fg=FG_TITLE, bg=BG_PANEL).pack(pady=(10, 0))
        tk.Label(center, text=f"{APP_DESC}  •  v{VERSION}",
                 font=("Segoe UI", 9), fg="#aaaaaa", bg=BG_PANEL).pack()

        # Right logo
        if self.ericsson_img:
            lbl = tk.Label(banner, image=self.ericsson_img, bg=BG_PANEL)
            lbl.pack(side="right", padx=10)

    def _build_main(self):
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel: epic selection + story list
        left = tk.Frame(main, bg=BG_PANEL, width=380,
                        highlightbackground=BORDER_COLOR, highlightthickness=1)
        left.pack(side="left", fill="y", padx=(0, 5))
        left.pack_propagate(False)
        self._build_left_panel(left)

        # Right panel: tabs for user stories
        right = tk.Frame(main, bg=BG_DARK)
        right.pack(side="left", fill="both", expand=True)
        self._build_right_panel(right)

    def _build_left_panel(self, parent):
        # Epic selector
        lbl_epic = tk.Label(parent, text=S["select_epic"], font=("Segoe UI", 11, "bold"),
                 fg=FG_ACCENT, bg=BG_PANEL)
        lbl_epic.pack(anchor="w", padx=10, pady=(10, 2))
        ToolTip(lbl_epic, "Select a Security Heartbeat epic to load its stories")

        self.epic_var = tk.StringVar()
        self.epic_combo = tk.Listbox(parent, font=("Segoe UI", 9), height=4,
                                      bg="#001a40", fg=FG_TEXT, selectbackground=BTN_PRIMARY,
                                      selectforeground="white", bd=0, highlightthickness=1,
                                      highlightbackground=BORDER_COLOR, exportselection=False)
        self.epic_combo.pack(fill="x", padx=10, pady=(0, 5))
        self.epic_combo.bind("<<ListboxSelect>>", self._on_epic_selected)
        ToolTip(self.epic_combo, "🟢 = Open (can create stories), 🔴 = Resolved (read-only)")

        # Epic count
        self.epic_count_lbl = tk.Label(parent, text="Epics: 0", font=("Segoe UI", 9),
                                        fg="#aaaaaa", bg=BG_PANEL)
        self.epic_count_lbl.pack(anchor="w", padx=10)

        # Epic description
        lbl_desc = tk.Label(parent, text=S["epic_description"], font=("Segoe UI", 10, "bold"),
                 fg=FG_TEXT, bg=BG_PANEL)
        lbl_desc.pack(anchor="w", padx=10, pady=(5, 2))
        ToolTip(lbl_desc, "Full description of the selected epic from Jira")
        self.epic_desc = scrolledtext.ScrolledText(parent, height=5, font=("Consolas", 9),
                                                    bg="#0a0a1a", fg=FG_TEXT, insertbackground=FG_TEXT,
                                                    bd=0, wrap="word")
        self.epic_desc.pack(fill="x", padx=10, pady=(0, 10))

        # Separator
        tk.Frame(parent, bg=BORDER_COLOR, height=1).pack(fill="x", padx=10, pady=5)

        # Stories header with count
        stories_header = tk.Frame(parent, bg=BG_PANEL)
        stories_header.pack(fill="x", padx=10, pady=(5, 2))
        tk.Label(stories_header, text=S["historical_stories"], font=("Segoe UI", 10, "bold"),
                 fg=FG_TEXT, bg=BG_PANEL).pack(side="left")
        self.stories_count_lbl = tk.Label(stories_header, text="(0)", font=("Segoe UI", 9),
                                           fg="#aaaaaa", bg=BG_PANEL)
        self.stories_count_lbl.pack(side="left", padx=5)

        self.stories_frame = tk.Frame(parent, bg=BG_PANEL)
        # Add scrollbar
        canvas = tk.Canvas(self.stories_frame, bg=BG_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.stories_frame, orient="vertical", command=canvas.yview)
        self.stories_inner = tk.Frame(canvas, bg=BG_PANEL)
        self.stories_inner.bind("<Configure>",
                                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.stories_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        # Mousewheel scroll
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>",
                    lambda ev: canvas.yview_scroll(-1 * (ev.delta // 120), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<Button-4>",
                    lambda ev: canvas.yview_scroll(-1, "units")), add="+")
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<Button-5>",
                    lambda ev: canvas.yview_scroll(1, "units")), add="+")
        canvas.bind("<Leave>", lambda e: (canvas.unbind_all("<Button-4>"),
                    canvas.unbind_all("<Button-5>")), add="+")
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.stories_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # Buttons row
        btn_frame = tk.Frame(parent, bg=BG_PANEL)
        btn_frame.pack(fill="x", padx=10, pady=5)
        self._make_btn(btn_frame, S["add_story"], BTN_SUCCESS, self._add_story).pack(side="left")
        self._make_btn(btn_frame, S["load_stories"], BTN_INFO, self._load_from_epic).pack(side="left", padx=5)

    def _build_right_panel(self, parent):
        # Tab area header
        header = tk.Frame(parent, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 5))
        tk.Label(header, text="📝 User Stories", font=("Segoe UI", 12, "bold"),
                 fg=FG_TITLE, bg=BG_DARK).pack(side="left")

        # Notebook for story tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)

        # Bottom action bar
        actions = tk.Frame(parent, bg=BG_DARK)
        actions.pack(fill="x", pady=(5, 0))
        self.btn_create = self._make_btn(actions, S["confirm_create"], BTN_PRIMARY, self._create_stories)
        self.btn_create.pack(side="left")
        self._make_btn(actions, "💾 Save US", BTN_SUCCESS, self._save_stories_to_file).pack(side="left", padx=5)
        self._make_btn(actions, "⏻ Quit", BTN_DANGER, self._on_close).pack(side="right")
        self._make_btn(actions, S["history"], BTN_INFO, self._show_history).pack(side="right", padx=5)

    def _build_credentials_panel(self):
        """Build credentials input panel at the bottom."""
        cred_frame = tk.Frame(self.root, bg=BG_PANEL, height=45,
                              highlightbackground=BORDER_COLOR, highlightthickness=1)
        cred_frame.pack(fill="x", padx=5, pady=(0, 0), side="bottom")
        cred_frame.pack_propagate(False)

        lbl = tk.Label(cred_frame, text="🔐 Jira:", font=("Segoe UI", 9, "bold"),
                       fg=FG_ACCENT, bg=BG_PANEL)
        lbl.pack(side="left", padx=(10, 5))
        ToolTip(lbl, "Jira connection (saved between sessions)")

        tk.Label(cred_frame, text="API Token:", font=("Segoe UI", 9),
                 fg=FG_TEXT, bg=BG_PANEL).pack(side="left")
        self.cred_token = tk.Entry(cred_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                                   insertbackground=FG_TEXT, bd=0, width=45, show="•",
                                   highlightbackground=BORDER_COLOR, highlightthickness=1)
        self.cred_token.pack(side="left", padx=(3, 10))
        _pat_tooltip = (
            "🔑 HOW TO CREATE THE TOKEN:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣  Open Jira in your browser\n"
            "2️⃣  Click your profile icon (top-right)\n"
            "3️⃣  Select 'Personal Access Tokens'\n"
            "4️⃣  Click 'Create token'\n"
            "5️⃣  Give it a name (e.g. 'Heartbeat App')\n"
            "6️⃣  Copy the generated token\n"
            "7️⃣  Paste it here\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠ No username needed, only the token!"
        ) if LANG == "en" else (
            "🔑 COME CREARE IL TOKEN:\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "1️⃣  Apri Jira nel browser\n"
            "2️⃣  Clicca la tua icona profilo (in alto a destra)\n"
            "3️⃣  Seleziona 'Personal Access Tokens'\n"
            "4️⃣  Clicca 'Create token'\n"
            "5️⃣  Dai un nome (es. 'Heartbeat App')\n"
            "6️⃣  Copia il token generato\n"
            "7️⃣  Incollalo qui\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠ Non serve username, solo il token!"
        )
        ToolTip(self.cred_token, _pat_tooltip)

        self.btn_connect = self._make_btn(cred_frame, "🔗 Connect", BTN_SUCCESS, self._connect_jira)
        self.btn_connect.pack(side="left", padx=5)
        ToolTip(self.btn_connect, "Test connection and reload epics from Jira")

        # Pre-fill from state
        state = load_state()
        if state.get("jira_token"):
            self.cred_token.insert(0, state["jira_token"])
        elif JIRA_TOKEN:
            self.cred_token.insert(0, JIRA_TOKEN)

    def _init_jira_from_state(self):
        """Try to initialize Jira from saved token or env var."""
        state = load_state()
        token = state.get("jira_token", "") or JIRA_TOKEN
        _init_jira(JIRA_URL, "", token)

    def _connect_jira(self):
        """Connect to Jira with token from GUI field."""
        token = self.cred_token.get().strip()
        if not token:
            self._set_status("⚠ Enter API token")
            return
        from config import JIRA_URL
        if not JIRA_URL:
            self._set_status("⚠ jira_url not set in app_config.json")
            return
        if _init_jira(JIRA_URL, "", token):
            self._load_sprints()
            self._load_epics()
            self._set_status(f"✓ Connected to Jira — {len(self.epics)} epics loaded")
        else:
            self._set_status("✗ Connection failed — check token or jira_url")

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=BG_PANEL, height=25)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        mode = "JIRA" if JIRA_AVAILABLE else "DEMO"
        # Blinking indicator
        self.indicator_lbl = tk.Label(bar, text="●", font=("Segoe UI", 10),
                                      fg="#888888", bg=BG_PANEL)
        self.indicator_lbl.pack(side="left", padx=(5, 0))
        self._indicator_tooltip = ToolTip(self.indicator_lbl, "Idle")
        self.status_lbl = tk.Label(bar, text=f"  Mode: {mode}  |  Ctrl+S: Save  |  Ctrl+Q: Quit",
                                    font=("Segoe UI", 8), fg="#888888", bg=BG_PANEL)
        self.status_lbl.pack(side="left", padx=5)
        # Log file path on the right
        self.status_right = tk.Label(bar, text=f"v{VERSION} | LOG: {LOG_FILE.name}",
                                      font=("Segoe UI", 8), fg="#888888", bg=BG_PANEL)
        self.status_right.pack(side="right", padx=5)
        ToolTip(self.status_right, str(LOG_FILE))

    def _make_btn(self, parent, text, color, command, debounce_ms=400):
        def debounced():
            btn.config(state="disabled")
            command()
            try:
                btn.after(debounce_ms, lambda: btn.config(state="normal") if btn.winfo_exists() else None)
            except Exception:
                pass
        btn = tk.Button(parent, text=text, font=("Segoe UI", 9, "bold"),
                        bg=color, fg="white", activebackground=color,
                        activeforeground="white", bd=0, padx=12, pady=4,
                        cursor="hand2", command=debounced)
        return btn

    # --- Indicator ---

    def _indicator_set(self, state: str):
        """Set indicator: 'loading', 'ok', 'error'."""
        if self._blink_id:
            self.root.after_cancel(self._blink_id)
            self._blink_id = None
        if state == "loading":
            self._indicator_tooltip.text = "Reading User Stories..."
            self._blink_yellow()
        elif state == "ok":
            self.indicator_lbl.config(fg="#66bb6a")
            self._indicator_tooltip.text = "User Stories updated"
        elif state == "error":
            self.indicator_lbl.config(fg="#ef5350")
            self._indicator_tooltip.text = "Timeout reading User Stories"

    def _blink_yellow(self):
        cur = self.indicator_lbl.cget("fg")
        nxt = "#ffca28" if cur != "#ffca28" else BG_PANEL
        self.indicator_lbl.config(fg=nxt)
        self._blink_id = self.root.after(500, self._blink_yellow)

    # --- Data Loading ---

    def _load_sprints(self):
        """Load sprint names from the configured board."""
        if JIRA_AVAILABLE:
            try:
                import jira_client
                self.sprints = jira_client.get_board_sprints()
                log.info(f"Loaded {len(self.sprints)} sprints")
            except Exception as e:
                log.error(f"Failed to load sprints: {e}")
                self.sprints = []
        else:
            self.sprints = []

    def _load_epics(self):
        global JIRA_AVAILABLE
        self._indicator_set("loading")
        log.info("Loading epics...")
        if JIRA_AVAILABLE:
            try:
                import jira_client
                self.epics = jira_client.get_open_epics()
                log.info(f"Loaded {len(self.epics)} epics")
            except Exception as e:
                self._set_status(f"Jira error: {e}")
                log.error(f"Failed to load epics: {e}")
                self.epics = []
        else:
            self.epics = []
            self._set_status("⚠ Jira not configured. Enter credentials below and click Connect.")
        self.epic_combo.delete(0, "end")
        for e in self.epics:
            resolved = e.get("resolution", "Unresolved").lower() != "unresolved"
            icon = "🔴" if resolved else "🟢"
            self.epic_combo.insert("end", f"{icon} [{e['key']}] {e['summary']}")
        self.epic_count_lbl.config(text=f"Epics: {len(self.epics)}")

        # Preload stories count per epic to determine source epic
        self._epic_stories_cache = {}
        if JIRA_AVAILABLE and self.epics:
            import jira_client
            for e in self.epics:
                try:
                    stories = jira_client.get_epic_stories(e["key"])
                    self._epic_stories_cache[e["key"]] = stories
                    log.info(f"  Epic {e['key']}: {len(stories)} stories")
                except Exception as ex:
                    log.error(f"  Epic {e['key']}: failed to load stories: {ex}")
                    self._epic_stories_cache[e["key"]] = []

        self._indicator_set("ok")

        # Auto-select first epic
        if self.epics:
            self.epic_combo.selection_set(0)
            self._on_epic_selected()

    def _on_epic_selected(self, event=None):
        sel = self.epic_combo.curselection()
        if not sel:
            return
        idx = sel[0]
        self.selected_epic = self.epics[idx]
        self.epic_desc.config(state="normal")
        self.epic_desc.delete("1.0", "end")
        desc = f"[{self.selected_epic['key']}] {self.selected_epic.get('summary', '')}\n\n"
        desc += self.selected_epic.get("description", "")
        self.epic_desc.insert("1.0", desc)
        self.epic_desc.config(state="disabled")

        # Enable/disable create button based on resolution
        is_resolved = self.selected_epic.get("resolution", "Unresolved").lower() != "unresolved"
        if is_resolved:
            self.btn_create.config(state="disabled", bg="#555555")
            self._set_status(f"Read-only: epic resolved ({self.selected_epic.get('resolution', '')})")
        else:
            self.btn_create.config(state="normal", bg=BTN_PRIMARY)

        self._load_stories_for_epic()

    def _get_source_epic_index(self) -> int:
        """Determine which epic to use as source for stories.

        Returns the index of the latest epic that has linked stories,
        falling back to the penultimate if the latest has none.
        """
        if not self.epics:
            return -1
        first_key = self.epics[0]["key"]
        if self._epic_stories_cache.get(first_key):
            return 0
        # Latest has no stories, use the next one that does
        for i in range(1, len(self.epics)):
            if self._epic_stories_cache.get(self.epics[i]["key"]):
                return i
        return -1

    def _is_story_editable(self, story: dict, is_new: bool) -> bool:
        """A story is editable only if not yet created or if its status is Open."""
        if is_new:
            return True
        status = story.get("status", "").lower()
        return status in ("open", "backlog", "reopened", "")

    def _load_stories_for_epic(self):
        """Load stories for the selected epic with editability and old-epic logic."""
        if not self.selected_epic:
            return

        # Clean up add-to-epic button
        if self._add_to_epic_btn:
            try:
                self._add_to_epic_btn.destroy()
            except Exception:
                pass
            self._add_to_epic_btn = None

        self._indicator_set("loading")
        log.info(f"Loading stories for epic {self.selected_epic['key']}")

        # Determine the target epic (latest one, for creating new stories)
        target_epic = self.epics[0] if self.epics else self.selected_epic
        selected_key = self.selected_epic["key"]
        selected_idx = next((i for i, e in enumerate(self.epics) if e["key"] == selected_key), 0)

        # Source epic = latest that has stories (or latest if it has stories)
        source_idx = self._get_source_epic_index()

        stories = []
        from_template = False
        is_old_epic = False  # stories come from an older epic (not the target)

        if JIRA_AVAILABLE:
            # If selecting the target (latest) epic
            if selected_idx == 0:
                target_stories = self._epic_stories_cache.get(selected_key, [])
                if target_stories:
                    stories = target_stories
                elif source_idx >= 0:
                    # Latest has no stories, use source as template
                    source_key = self.epics[source_idx]["key"]
                    stories = self._epic_stories_cache.get(source_key, [])
                    from_template = True
                    is_old_epic = True
                else:
                    from_template = True
                    try:
                        import jira_client
                        stories = jira_client.get_historical_stories()
                    except Exception:
                        pass
            else:
                # Selecting an older epic — show its stories
                stories = self._epic_stories_cache.get(selected_key, [])
                is_old_epic = True
        else:
            self._set_status("⚠ Jira not available — cannot load stories")

        log.info(f"  Found {len(stories)} stories (template={from_template}, old_epic={is_old_epic})")

        # Update stories count
        self.stories_count_lbl.config(text=f"({len(stories)})")

        # Populate checkboxes
        for w in self.stories_inner.winfo_children():
            w.destroy()
        self.story_checkboxes = []

        for i, s in enumerate(stories):
            # Stories from old epics are unchecked by default
            var = tk.BooleanVar(value=not is_old_epic)
            cb = tk.Checkbutton(self.stories_inner, text=f"[{s.get('key', 'NEW')}] {s['summary']}",
                                variable=var, bg=BG_PANEL, fg=FG_TEXT,
                                selectcolor=BG_CARD, activebackground=BG_PANEL,
                                activeforeground=FG_ACCENT, font=("Segoe UI", 8),
                                anchor="w", wraplength=320,
                                command=lambda idx=i: self._select_tab_by_index(idx))
            cb.pack(fill="x", anchor="w", pady=1)
            self.story_checkboxes.append((var, s))

        # Create tabs from stories
        is_resolved = target_epic.get("resolution", "Unresolved").lower() != "unresolved"
        self._clear_tabs()
        for s in stories:
            if from_template or is_old_epic:
                # Template from older epic — editable, not yet created
                self._add_tab(s["summary"], s.get("description", ""),
                              key="", existing=False, readonly=False,
                              status="", resolution="", assignee="",
                              acceptance_criteria=s.get("acceptance_criteria", ""),
                              sprint=s.get("sprint", ""),
                              labels=s.get("labels"),
                              assignee_key=s.get("assignee_key", ""),
                              components=s.get("components"),
                              priority=s.get("priority", ""))
            else:
                # Existing stories — editable only if Open or not created
                editable = self._is_story_editable(s, False)
                readonly = is_resolved or not editable
                self._add_tab(s["summary"], s.get("description", ""),
                              key=s.get("key", ""), existing=True, readonly=readonly,
                              status=s.get("status", ""),
                              resolution=s.get("resolution", ""),
                              assignee=s.get("assignee", ""),
                              acceptance_criteria=s.get("acceptance_criteria", ""),
                              sprint=s.get("sprint", ""),
                              labels=s.get("labels"),
                              assignee_key=s.get("assignee_key", ""),
                              components=s.get("components"),
                              priority=s.get("priority", ""))

        # Show "Add to Epic" button if stories come from older epic
        if is_old_epic:
            self._show_add_to_epic_button(target_epic)

        self._indicator_set("ok")

    def _select_tab_by_index(self, idx):
        """Select the notebook tab corresponding to the clicked story."""
        tabs = self.notebook.tabs()
        if idx < len(tabs):
            self.notebook.select(tabs[idx])

    def _load_from_epic(self):
        """Reload stories from the selected epic."""
        self._load_stories_for_epic()
        self._set_status("Stories loaded from epic")

    def _show_add_to_epic_button(self, target_epic):
        """Show the 'Add to Epic' button when viewing stories from an older epic."""
        # Remove previous add button if any
        if hasattr(self, '_add_to_epic_btn') and self._add_to_epic_btn:
            try:
                self._add_to_epic_btn.destroy()
            except Exception:
                pass
        btn_frame = self.stories_frame.master  # parent of stories_frame
        self._add_to_epic_btn = self._make_btn(
            btn_frame, f"➕ Add selected to {target_epic['key']}", BTN_SUCCESS,
            lambda: self._add_stories_to_epic(target_epic))
        self._add_to_epic_btn.pack(fill="x", padx=10, pady=(5, 0))
        ToolTip(self._add_to_epic_btn,
                f"Clone selected stories and link them to epic {target_epic['key']}")

    def _add_stories_to_epic(self, target_epic):
        """Clone selected stories from old epic and create them under the target epic."""
        if not JIRA_AVAILABLE:
            messagebox.showerror("Error", "Jira not available.")
            return

        selected = [(var, s) for var, s in self.story_checkboxes if var.get()]
        if not selected:
            messagebox.showwarning("No Selection", "Select at least one story to add.")
            return

        msg = f"Clone {len(selected)} stories to epic {target_epic['key']}?"
        if not messagebox.askyesno("Confirm", msg):
            return

        log.info(f"Cloning {len(selected)} stories to {target_epic['key']}")
        import jira_client
        created = []
        relinked = []
        errors = []
        for _, s in selected:
            try:
                if s.get("key") and s.get("epic_link") != target_epic["key"]:
                    # Existing story from old epic — update its epic link
                    jira_client.update_epic_link(s["key"], target_epic["key"])
                    relinked.append(s["key"])
                    log.info(f"  Re-linked {s['key']} to {target_epic['key']}")
                else:
                    # No key (template) — create new story
                    desc = s.get("description", "")
                    ac = s.get("acceptance_criteria", "")
                    key = jira_client.create_story(
                        target_epic["key"], s["summary"], desc,
                        s.get("sprint", ""), s.get("labels"),
                        s.get("assignee_key", ""), s.get("components"),
                        s.get("priority", ""), ac)
                    created.append(key)
                    log.info(f"  Created {key}: {s['summary']}")
            except Exception as e:
                errors.append(f"{s.get('key', s['summary'])}: {e}")
                log.error(f"  Failed: {s.get('key', s['summary'])}: {e}")

        msg = ""
        if created:
            msg += f"✓ Created: {', '.join(created)}\n"
        if relinked:
            msg += f"✓ Re-linked: {', '.join(relinked)}\n"
        if errors:
            msg += f"\n✗ Errors:\n" + "\n".join(errors)
        messagebox.showinfo("Results", msg)
        self._set_status(f"Added {len(created)} created, {len(relinked)} re-linked to {target_epic['key']}")

        # Refresh cache and reload
        if created or relinked:
            try:
                self._epic_stories_cache[target_epic["key"]] = jira_client.get_epic_stories(target_epic["key"])
            except Exception:
                pass
            self._load_stories_for_epic()

    # --- Tab Management ---

    def _clear_tabs(self):
        for tab_id in self.notebook.tabs():
            self.notebook.forget(tab_id)
        self.tab_widgets = []
        self.story_tabs = []

    def _add_story(self):
        self._add_tab("New Story", "", existing=False, readonly=False)

    def _add_tab(self, title: str = "New Story", description: str = "",
                 sprint: str = "", key: str = "", existing: bool = False,
                 readonly: bool = False, status: str = "", resolution: str = "",
                 assignee: str = "", acceptance_criteria: str = "",
                 labels: list = None, assignee_key: str = "",
                 components: list = None, priority: str = ""):
        frame = tk.Frame(self.notebook, bg=BG_CARD)

        # Header row: key + status + resolution + assignee
        hdr = tk.Frame(frame, bg=BG_CARD)
        hdr.pack(fill="x", padx=10, pady=(5, 0))
        if key:
            tk.Label(hdr, text=f"🔑 {key}", font=("Segoe UI", 9),
                     fg="#aaaaaa", bg=BG_CARD).pack(side="left")
        else:
            tk.Label(hdr, text="🆕 New", font=("Segoe UI", 9, "bold"),
                     fg=FG_ACCENT, bg=BG_CARD).pack(side="left")
        if status:
            status_colors = {
                "open": "#4fc3f7", "backlog": "#4fc3f7", "reopened": "#4fc3f7",
                "pending development": "#4fc3f7", "pending customer": "#4fc3f7",
                "in progress": "#ffb74d", "in development": "#ffb74d",
                "ready for development": "#ffb74d", "development done": "#ffb74d",
                "test": "#ce93d8", "testing": "#ce93d8", "in testing": "#ce93d8",
                "testing/review": "#ce93d8", "integration test": "#ce93d8",
                "ready for review": "#81d4fa", "review": "#81d4fa", "in review": "#81d4fa",
                "ready for verification": "#81d4fa", "verified": "#81d4fa",
                "ready for integration": "#a5d6a7", "integration": "#a5d6a7",
                "analysis": "#ffcc80", "demo": "#ffcc80",
                "customer acceptance": "#ffcc80", "acceptance testing done": "#66bb6a",
                "on hold": "#ef9a9a", "blocked": "#ef5350",
                "resolved": "#66bb6a", "closed": "#66bb6a", "done": "#66bb6a",
            }
            sc = status_colors.get(status.lower(), "#aaaaaa")
            tk.Label(hdr, text=f"  ● {status}", font=("Segoe UI", 9, "bold"),
                     fg=sc, bg=BG_CARD).pack(side="left", padx=(10, 0))
        if resolution:
            rc = "#66bb6a" if resolution.lower() == "done" else "#aaaaaa"
            tk.Label(hdr, text=f"  [{resolution}]", font=("Segoe UI", 8),
                     fg=rc, bg=BG_CARD).pack(side="left", padx=(5, 0))
        if assignee:
            tk.Label(hdr, text=f"  👤 {assignee}", font=("Segoe UI", 8),
                     fg="#b0bec5", bg=BG_CARD).pack(side="right")

        # Title
        lbl_title = tk.Label(frame, text=S["us_title"], font=("Segoe UI", 10, "bold"),
                 fg=FG_ACCENT, bg=BG_CARD)
        lbl_title.pack(anchor="w", padx=10, pady=(5, 2))
        ToolTip(lbl_title, "User story summary/title as it will appear in Jira")
        state = "disabled" if readonly else "normal"
        title_entry = tk.Entry(frame, font=("Segoe UI", 10), bg="#0a0a1a", fg=FG_TEXT,
                               insertbackground=FG_TEXT, bd=0, highlightbackground=BORDER_COLOR,
                               highlightthickness=1, state="normal")
        title_entry.pack(fill="x", padx=10, pady=(0, 5))
        title_entry.insert(0, title)
        title_entry.config(state=state)

        # Description
        desc_hdr = tk.Frame(frame, bg=BG_CARD)
        desc_hdr.pack(fill="x", padx=10, pady=(5, 2))
        lbl_desc_tab = tk.Label(desc_hdr, text=S["us_description"], font=("Segoe UI", 10, "bold"),
                 fg=FG_ACCENT, bg=BG_CARD)
        lbl_desc_tab.pack(side="left")
        ToolTip(lbl_desc_tab, "Detailed description of the user story (Jira wiki markup)")
        btn_help = tk.Button(desc_hdr, text="?", font=("Segoe UI", 7, "bold"),
                             bg=BTN_INFO, fg="white", bd=0, padx=4, pady=0,
                             cursor="hand2", command=self._show_markup_help)
        btn_help.pack(side="left", padx=5)
        ToolTip(btn_help, "Show Jira text formatting syntax")
        desc_text = scrolledtext.ScrolledText(frame, height=8, font=("Consolas", 9),
                                              bg="#0a0a1a", fg=FG_TEXT, insertbackground=FG_TEXT,
                                              bd=0, wrap="word", highlightbackground=BORDER_COLOR,
                                              highlightthickness=1)
        desc_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        desc_text.insert("1.0", description)
        if not readonly:
            btn_tr_desc = tk.Button(desc_hdr, text="IT→EN", font=("Segoe UI", 8, "bold"),
                                    bg="#f39c12", fg="white", bd=0, padx=4, pady=0,
                                    cursor="hand2",
                                    command=lambda: self._translate_popup(desc_text))
            btn_tr_desc.pack(side="left", padx=3)
            ToolTip(btn_tr_desc, "Translate Italian text to English")
        if readonly:
            desc_text.config(state="disabled")

        # Acceptance Criteria
        ac_hdr = tk.Frame(frame, bg=BG_CARD)
        ac_hdr.pack(fill="x", padx=10, pady=(5, 2))
        lbl_ac = tk.Label(ac_hdr, text="Acceptance Criteria:", font=("Segoe UI", 10, "bold"),
                 fg=FG_ACCENT, bg=BG_CARD)
        lbl_ac.pack(side="left")
        ToolTip(lbl_ac, "Conditions that must be met for the story to be considered done")
        btn_help_ac = tk.Button(ac_hdr, text="?", font=("Segoe UI", 7, "bold"),
                                bg=BTN_INFO, fg="white", bd=0, padx=4, pady=0,
                                cursor="hand2", command=self._show_markup_help)
        btn_help_ac.pack(side="left", padx=5)
        ToolTip(btn_help_ac, "Show Jira text formatting syntax")
        ac_text = scrolledtext.ScrolledText(frame, height=4, font=("Consolas", 9),
                                            bg="#0a0a1a", fg=FG_TEXT, insertbackground=FG_TEXT,
                                            bd=0, wrap="word", highlightbackground=BORDER_COLOR,
                                            highlightthickness=1)
        ac_text.pack(fill="x", padx=10, pady=(0, 5))
        if not readonly:
            btn_tr_ac = tk.Button(ac_hdr, text="IT→EN", font=("Segoe UI", 8, "bold"),
                                  bg="#f39c12", fg="white", bd=0, padx=4, pady=0,
                                  cursor="hand2",
                                  command=lambda: self._translate_popup(ac_text))
            btn_tr_ac.pack(side="left", padx=3)
            ToolTip(btn_tr_ac, "Translate Italian text to English")
        ac_text.insert("1.0", acceptance_criteria)
        if readonly:
            ac_text.config(state="disabled")

        # Sprint
        sprint_frame = tk.Frame(frame, bg=BG_CARD)
        sprint_frame.pack(fill="x", padx=10, pady=(5, 5))
        lbl_sprint = tk.Label(sprint_frame, text=S["us_sprint"], font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_sprint.pack(side="left")
        ToolTip(lbl_sprint, "Sprint to assign the story to (from team board)")
        sprint_combo = ttk.Combobox(sprint_frame, font=("Segoe UI", 9), width=30,
                                    values=self.sprints, state="readonly" if readonly else "normal")
        sprint_combo.pack(side="left", padx=(5, 0))
        if sprint:
            sprint_combo.set(sprint)
        elif self.sprints:
            sprint_combo.set(self.sprints[0])

        # Labels
        labels_frame = tk.Frame(frame, bg=BG_CARD)
        labels_frame.pack(fill="x", padx=10, pady=(5, 5))
        lbl_labels = tk.Label(labels_frame, text="Labels:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_labels.pack(side="left")
        ToolTip(lbl_labels, "Comma-separated labels (e.g. 25.10,Hydra)")
        # Default labels: sprint number + team name
        sprint_num = ""
        sprint_val = sprint or ""
        if sprint_val and TEAM_NAME and TEAM_NAME.lower() in sprint_val.lower():
            sprint_num = sprint_val.replace(TEAM_NAME, "").strip()
        if labels is not None:
            # Ensure sprint number is in labels
            if sprint_num and sprint_num not in labels:
                labels = list(labels) + [sprint_num]
            default_labels = ",".join(labels)
        else:
            default_labels = ",".join(filter(None, [sprint_num, TEAM_NAME]))
        labels_entry = tk.Entry(labels_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                                insertbackground=FG_TEXT, bd=0, width=30,
                                highlightbackground=BORDER_COLOR, highlightthickness=1,
                                state="normal")
        labels_entry.pack(side="left", padx=(5, 0))
        labels_entry.insert(0, default_labels)
        if readonly:
            labels_entry.config(state="disabled")

        # Assignee
        assign_frame = tk.Frame(frame, bg=BG_CARD)
        assign_frame.pack(fill="x", padx=10, pady=(2, 2))
        lbl_assign = tk.Label(assign_frame, text="Assignee:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_assign.pack(side="left")
        ToolTip(lbl_assign, "Jira username (signum) of the assignee")
        assignee_entry = tk.Entry(assign_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                                  insertbackground=FG_TEXT, bd=0, width=20,
                                  highlightbackground=BORDER_COLOR, highlightthickness=1)
        assignee_entry.pack(side="left", padx=(5, 10))
        assignee_entry.insert(0, assignee_key or assignee)
        if readonly:
            assignee_entry.config(state="disabled")

        # Components
        lbl_comp = tk.Label(assign_frame, text="Components:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_comp.pack(side="left")
        ToolTip(lbl_comp, "Comma-separated component names")
        components_entry = tk.Entry(assign_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                                    insertbackground=FG_TEXT, bd=0, width=15,
                                    highlightbackground=BORDER_COLOR, highlightthickness=1)
        components_entry.pack(side="left", padx=(5, 10))
        components_entry.insert(0, ",".join(components or []))
        if readonly:
            components_entry.config(state="disabled")

        # Priority
        lbl_prio = tk.Label(assign_frame, text="Priority:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_prio.pack(side="left")
        ToolTip(lbl_prio, "Issue priority (e.g. Minor, Major, Critical)")
        priority_entry = tk.Entry(assign_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                                  insertbackground=FG_TEXT, bd=0, width=10,
                                  highlightbackground=BORDER_COLOR, highlightthickness=1)
        priority_entry.pack(side="left", padx=(5, 0))
        priority_entry.insert(0, priority)
        if readonly:
            priority_entry.config(state="disabled")

        # Buttons (only if not readonly)
        btn_frame = tk.Frame(frame, bg=BG_CARD)
        btn_frame.pack(fill="x", padx=10, pady=(0, 5))

        if not readonly:
            tab_idx = len(self.tab_widgets)
            self._make_btn(btn_frame, S["split_story"], "#f39c12",
                           lambda i=tab_idx: self._split_tab(i)).pack(side="left", padx=5)
            self._make_btn(btn_frame, S["remove_tab"], BTN_DANGER,
                           lambda i=tab_idx: self._remove_tab(i)).pack(side="right")

        # Info banner for template stories (not yet created)
        if not existing and not readonly:
            banner = tk.Frame(frame, bg="#1a3a5c", height=24)
            banner.pack(fill="x", padx=10, pady=(0, 5))
            tk.Label(banner, text="⚠ Template from previous epic — modify content before creation",
                     font=("Segoe UI", 8, "italic"), fg="#ffcc80", bg="#1a3a5c").pack(pady=2)

        # Tab title: Jira key or "New"
        tab_label = key if key else "🆕 New"
        self.notebook.add(frame, text=tab_label)
        self.tab_widgets.append({"frame": frame, "title": title_entry,
                                  "desc": desc_text, "sprint": sprint_combo,
                                  "labels": labels_entry, "ac": ac_text,
                                  "assignee": assignee_entry,
                                  "components": components_entry,
                                  "priority": priority_entry,
                                  "existing": existing, "readonly": readonly})
        self.story_tabs.append({"title": title, "description": description, "sprint": sprint})

        # Select the new tab
        self.notebook.select(frame)

    def _open_popup(self, popup_type: str, title: str, geometry: str) -> tk.Toplevel:
        """Open a single popup per type, closing any previous one."""
        if popup_type in self._popups:
            try:
                self._popups[popup_type].destroy()
            except Exception:
                pass
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(geometry)
        win.configure(bg=BG_DARK)
        self._popups[popup_type] = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_popup(popup_type))
        return win

    def _close_popup(self, popup_type: str):
        if popup_type in self._popups:
            try:
                self._popups[popup_type].destroy()
            except Exception:
                pass
            del self._popups[popup_type]

    def _translate_popup(self, text_widget):
        """Open popup with translated text, Confirm replaces original, Skip closes."""
        original = text_widget.get("1.0", "end-1c")
        if not original.strip():
            self._set_status("No text to translate")
            return

        from translator import translate_to_english
        translated = translate_to_english(original)

        if translated == original:
            self._set_status("Translation unchanged — text may already be in English")
            return

        win = self._open_popup("translate", "Translation Preview", "600x350")
        win.resizable(True, True)

        tk.Label(win, text="[EN] English Translation:", font=("Segoe UI", 10, "bold"),
                 fg=FG_TITLE, bg=BG_DARK).pack(anchor="w", padx=10, pady=(10, 2))
        preview = scrolledtext.ScrolledText(win, height=12, font=("Consolas", 9),
                                            bg="#0a0a1a", fg=FG_TEXT, bd=0, wrap="word")
        preview.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        preview.insert("1.0", translated)
        preview.config(state="disabled")

        btn_frame = tk.Frame(win, bg=BG_DARK)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        def confirm():
            text_widget.delete("1.0", "end")
            text_widget.insert("1.0", translated)
            win.destroy()

        self._make_btn(btn_frame, "✓ Confirm", BTN_SUCCESS, confirm).pack(side="left", padx=5)
        self._make_btn(btn_frame, "✗ Skip", BTN_DANGER, win.destroy).pack(side="left", padx=5)

    def _show_markup_help(self):
        """Show Jira markup syntax in a popup window."""
        win = self._open_popup("markup_help", "Jira Markup Syntax", "440x520")
        win.resizable(False, False)
        text = tk.Text(win, font=("Consolas", 10), bg="#0a0a1a", fg=FG_TEXT,
                       bd=0, padx=10, pady=10)
        text.pack(fill="both", expand=True, padx=5, pady=5)
        text.insert("1.0", JIRA_MARKUP_HELP)
        text.config(state="disabled")
        self._make_btn(win, "Close", BTN_DANGER, win.destroy).pack(pady=5)

    def _translate_tab(self, idx):
        if idx >= len(self.tab_widgets):
            return
        w = self.tab_widgets[idx]
        title = w["title"].get()
        desc = w["desc"].get("1.0", "end-1c")

        if is_italian(title):
            title = translate_to_english(title)
            w["title"].delete(0, "end")
            w["title"].insert(0, title)
        if is_italian(desc):
            desc = translate_to_english(desc)
            w["desc"].delete("1.0", "end")
            w["desc"].insert("1.0", desc)

        self._set_status("Translation applied")

    def _split_tab(self, idx):
        if idx >= len(self.tab_widgets):
            return
        w = self.tab_widgets[idx]
        title = w["title"].get()
        desc = w["desc"].get("1.0", "end-1c")
        self._add_tab(f"{title} (part 2)", desc, w["sprint"].get())
        self._set_status("Story split into new tab")

    def _remove_tab(self, idx):
        if idx >= len(self.tab_widgets):
            return
        frame = self.tab_widgets[idx]["frame"]
        self.notebook.forget(frame)
        self.tab_widgets[idx] = None  # mark as removed
        self._set_status("Tab removed")

    # --- Actions ---

    def _collect_stories(self) -> list[dict]:
        stories = []
        for w in self.tab_widgets:
            if w is None:
                continue
            title = w["title"].get().strip()
            desc = w["desc"].get("1.0", "end-1c").strip()
            sprint = w["sprint"].get().strip()
            ac = w["ac"].get("1.0", "end-1c").strip() if "ac" in w else ""
            labels_str = w["labels"].get().strip() if "labels" in w else ""
            labels = [l.strip() for l in labels_str.split(",") if l.strip()]
            assignee_key = w["assignee"].get().strip() if "assignee" in w else ""
            comp_str = w["components"].get().strip() if "components" in w else ""
            components = [c.strip() for c in comp_str.split(",") if c.strip()]
            priority = w["priority"].get().strip() if "priority" in w else ""
            if title:
                stories.append({"title": title, "description": desc,
                                "acceptance_criteria": ac,
                                "sprint": sprint, "labels": labels,
                                "assignee_key": assignee_key,
                                "components": components, "priority": priority})
        return stories

    def _save_stories_to_file(self):
        """Save stories to a JSON file with all fields ready for creation."""
        stories = self._collect_stories()
        if not stories:
            messagebox.showwarning("No Stories", "No stories to save.")
            return

        epic_key = self.selected_epic["key"] if self.selected_epic else "NO_EPIC"
        epic_summary = self.selected_epic.get("summary", "") if self.selected_epic else ""

        from config import JIRA_PROJECT, STORY_ISSUETYPE
        export = {
            "epic_key": epic_key,
            "epic_summary": epic_summary,
            "project": JIRA_PROJECT,
            "issuetype": STORY_ISSUETYPE,
            "stories": stories,
        }

        from tkinter import filedialog
        import json
        default_name = f"{epic_key}_user_stories.json"
        filepath = filedialog.asksaveasfilename(
            title="Save User Stories",
            initialfile=default_name,
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filepath:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(export, f, indent=2, ensure_ascii=False)
            self._set_status(f"Saved {len(stories)} stories to {filepath}")

    def _create_stories(self):
        stories = self._collect_stories()
        if not stories:
            messagebox.showwarning("No Stories", "No stories to create.")
            return

        if not self.selected_epic:
            messagebox.showerror("Error", "No epic selected!")
            return

        if not JIRA_AVAILABLE:
            messagebox.showerror("Error",
                                 "Jira not configured.\nEnter credentials and click Connect, or set environment variables.")
            return

        # Custom confirmation dialog
        confirmed = [False]
        win = self._open_popup("confirm_create", "Confirm Creation", "650x450")
        win.resizable(False, True)
        win.grab_set()

        # Header
        hdr = tk.Frame(win, bg=BG_PANEL)
        hdr.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(hdr, text=f"🚀 Create {len(stories)} User Stories?",
                 font=("Segoe UI", 13, "bold"), fg=FG_TITLE, bg=BG_PANEL).pack(side="left")

        # Epic info
        tk.Label(win, text=f"Epic: [{self.selected_epic['key']}] {self.selected_epic.get('summary', '')}",
                 font=("Segoe UI", 9), fg="#aaaaaa", bg=BG_DARK, wraplength=600, justify="left"
                 ).pack(anchor="w", padx=10, pady=(0, 8))

        # Stories list with columns
        list_frame = tk.Frame(win, bg=BG_DARK)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # Header row
        col_hdr = tk.Frame(list_frame, bg=ERICSSON_LIGHT if 'ERICSSON_LIGHT' in dir() else BTN_PRIMARY)
        col_hdr.pack(fill="x")
        tk.Label(col_hdr, text=" # ", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, width=3).pack(side="left")
        tk.Label(col_hdr, text=" Title", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Label(col_hdr, text="Sprint ", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, width=18).pack(side="right")
        tk.Label(col_hdr, text="Assignee ", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, width=10).pack(side="right")

        # Scrollable list
        canvas = tk.Canvas(list_frame, bg=BG_DARK, highlightthickness=0, height=250)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=610)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for i, s in enumerate(stories, 1):
            bg = "#0a1a2e" if i % 2 == 0 else "#0d2240"
            row = tk.Frame(inner, bg=bg)
            row.pack(fill="x")
            tk.Label(row, text=f" {i:2d}", font=("Consolas", 9),
                     fg=FG_ACCENT, bg=bg, width=3).pack(side="left")
            tk.Label(row, text=f" {s['title'][:55]}{'…' if len(s['title'])>55 else ''}",
                     font=("Segoe UI", 9), fg=FG_TEXT, bg=bg,
                     anchor="w").pack(side="left", fill="x", expand=True)
            sprint_txt = s.get("sprint", "—")[:18]
            tk.Label(row, text=sprint_txt, font=("Segoe UI", 8),
                     fg="#90caf9", bg=bg, width=18).pack(side="right")
            assign_txt = s.get("assignee_key", "—")[:10]
            tk.Label(row, text=assign_txt, font=("Segoe UI", 8),
                     fg="#b0bec5", bg=bg, width=10).pack(side="right")

        # Summary footer
        footer = tk.Frame(win, bg=BG_PANEL)
        footer.pack(fill="x", padx=10, pady=(5, 5))
        tk.Label(footer, text=f"📊 Total: {len(stories)} stories  |  "
                 f"Assignees: {len(set(s.get('assignee_key','') for s in stories if s.get('assignee_key')))}  |  "
                 f"Sprints: {len(set(s.get('sprint','') for s in stories if s.get('sprint')))}",
                 font=("Segoe UI", 9), fg="#aaaaaa", bg=BG_PANEL).pack(anchor="w")

        # Buttons
        btn_frame = tk.Frame(win, bg=BG_DARK)
        btn_frame.pack(fill="x", padx=10, pady=(5, 10))

        def do_confirm():
            confirmed[0] = True
            win.grab_release()
            win.destroy()

        def do_cancel():
            win.grab_release()
            win.destroy()

        self._make_btn(btn_frame, "✓ Confirm & Create", BTN_SUCCESS, do_confirm).pack(side="left", padx=5)
        self._make_btn(btn_frame, "✗ Cancel", BTN_DANGER, do_cancel).pack(side="left", padx=5)

        win.wait_window()
        if not confirmed[0]:
            return

        epic_key = self.selected_epic["key"]
        created = []
        errors = []
        log.info(f"Creating {len(stories)} stories for epic {epic_key}")
        import jira_client
        for s in stories:
            try:
                key = jira_client.create_story(epic_key, s["title"], s["description"],
                                               s.get("sprint"), s.get("labels"),
                                               s.get("assignee_key"), s.get("components"),
                                               s.get("priority"), s.get("acceptance_criteria", ""))
                created.append(key)
                log.info(f"  Created {key}: {s['title']}")
            except Exception as e:
                errors.append(f"{s['title']}: {e}")
                log.error(f"  Failed: {s['title']}: {e}")

        msg = ""
        if created:
            msg += f"✓ Created: {', '.join(created)}\n"
        if errors:
            msg += f"\n✗ Errors:\n" + "\n".join(errors)
        messagebox.showinfo("Results", msg)
        self._set_status(f"Created {len(created)} stories")

    def _save(self):
        sel = self.epic_combo.curselection()
        state = {
            "epic_key": self.selected_epic["key"] if self.selected_epic else None,
            "epic_idx": sel[0] if sel else -1,
            "stories": self._collect_stories(),
            "jira_token": self.cred_token.get().strip(),
        }
        save_state(state)
        self._set_status("State saved ✓")

    def _restore_state(self):
        state = load_state()
        if not state:
            return
        # Restore epic selection (override auto-select)
        epic_idx = state.get("epic_idx", -1)
        if epic_idx >= 0 and epic_idx < len(self.epics):
            self.epic_combo.selection_clear(0, "end")
            self.epic_combo.selection_set(epic_idx)
            self._on_epic_selected()
        elif not self.epics:
            # No Jira connection — restore saved stories
            stories = state.get("stories", [])
            if stories:
                self._clear_tabs()
                for s in stories:
                    self._add_tab(s.get("title", ""), s.get("description", ""),
                                  sprint=s.get("sprint", ""))

    def _show_history(self):
        """Show application version history / changelog."""
        win = self._open_popup("history", "Application History", "600x400")

        text = scrolledtext.ScrolledText(win, font=("Consolas", 9),
                                          bg="#0a0a1a", fg=FG_TEXT, bd=0)
        text.pack(fill="both", expand=True, padx=10, pady=10)

        changelog = (
            "═══ v1.1.0 (2026-06-08) ═══\n"
            "  • Stories editable only if Open or not yet created\n"
            "  • Story list updates when selecting different epics\n"
            "  • Old epic stories shown unchecked with 'Add to Epic' button\n"
            "  • Blinking status indicator (yellow=reading, green=done, red=timeout)\n"
            "  • Application log file (cleared on each launch)\n"
            "  • Log file path displayed in status bar\n"
            "\n"
            "═══ v1.0.0 (2026-06-05) ═══\n"
            "  • Initial release\n"
            "  • Load open/closed epics from Jira\n"
            "  • Create user stories linked to epics\n"
            "  • Split stories into multiple tabs\n"
            "  • Italian to English translation\n"
            "  • Sprint assignment\n"
            "  • Auto-persist state on exit\n"
            "  • Ericsson brand color scheme\n"
            "  • Hydra team + Ericsson logos\n"
            "  • English/Italian UI (--ita flag)\n"
            "  • Read-only mode for closed epics\n"
            "  • Click story list to navigate tabs\n"
            "\n"
        )
        text.insert("1.0", changelog)
        text.config(state="disabled")
        text.tag_config("header", foreground=FG_TITLE, font=("Consolas", 9, "bold"))

        self._make_btn(win, S["close"], BTN_DANGER, win.destroy).pack(pady=5)

    def _set_status(self, msg: str):
        self.status_lbl.config(text=f"  {msg}")
        self.root.after(5000, lambda: self.status_lbl.config(
            text=f"  Mode: {'JIRA' if JIRA_AVAILABLE else 'DEMO'}  |  Ctrl+S: Save  |  Ctrl+Q: Quit"))

    def _on_close(self):
        self._save()
        log.info("Application closed")
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = SecurityHeartbeatApp()
    app.run()


if __name__ == "__main__":
    main()
