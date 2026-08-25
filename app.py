#!/usr/bin/env python3
"""Security Heartbeat User Story Generator - GUI Application (tkinter)."""
import sys
import os
import logging
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime

from config import load_state, save_state, load_history, VERSION, APP_TITLE, APP_DESC
from config import WINDOW_GEOMETRY, POPUP_GEOMETRIES, save_app_config
from config import JIRA_URL, JIRA_TOKEN, TEAM_NAME
from i18n import get_strings
from translator import translate_to_english
from help_texts import get_help

# --- CLI help ---
if "-h" in sys.argv or "--help" in sys.argv:
    print(f"{APP_TITLE} v{VERSION}")
    print(f"{APP_DESC}\n")
    print("Usage: python app.py [OPTIONS]\n")
    print("Options:")
    print("  --ita        Launch with Italian UI (default: English)")
    print("  -h, --help   Show this help message and exit")
    print()
    print("Environment variables:")
    print("  JIRA_URL     Jira server URL")
    print("  JIRA_TOKEN   Jira Personal Access Token (Bearer)")
    print("  JIRA_USER    Jira username (optional, not used for auth)")
    print("  JIRA_PROJECT Jira project key (default: from app_config.json)")
    sys.exit(0)

# --- LOG setup (cleared on each launch) ---
LOG_FILE = Path(__file__).parent / "securityHeartbeatGenerator.log"
LOG_FILE.write_text("")  # clear on launch
logging.basicConfig(
    filename=str(LOG_FILE), level=logging.DEBUG,
    format="%(asctime)s [%(levelname)-5s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger("secheartbeat.app")

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
    """Simple tooltip on hover for tkinter widgets.

    Works reliably on Linux (GNOME/KDE/Xfce) by using the root window
    as Toplevel parent and forcing geometry updates before display.
    """
    _DELAY_MS = 400  # delay before showing tooltip

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        self._after_id = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")
        # Also hide if widget is destroyed
        widget.bind("<Destroy>", self._hide, add="+")

    def _schedule(self, event=None):
        self._cancel()
        self._after_id = self.widget.after(self._DELAY_MS, self._show)

    def _cancel(self):
        if self._after_id:
            try:
                self.widget.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    def _show(self, event=None):
        self._after_id = None
        if self.tip:
            return
        try:
            if not self.widget.winfo_exists():
                return
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 2
        except Exception:
            return
        # Use winfo_toplevel() as parent for reliable display on Linux
        self.tip = tk.Toplevel(self.widget.winfo_toplevel())
        self.tip.wm_overrideredirect(True)
        # Withdraw first, position, then show — avoids flicker on Linux WMs
        self.tip.withdraw()
        self.tip.wm_geometry(f"+{x}+{y}")
        self.tip.wm_attributes("-topmost", True)
        lbl = tk.Label(self.tip, text=self.text, font=("Segoe UI", 9),
                       bg="#1e1e2e", fg="#e0e0e0", padx=12, pady=8,
                       wraplength=480, justify="left",
                       highlightbackground="#444466", highlightthickness=1)
        lbl.pack()
        # Force geometry computation then reposition within screen
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
        self.tip.deiconify()  # now show it

    def _hide(self, event=None):
        self._cancel()
        if self.tip:
            try:
                self.tip.destroy()
            except Exception:
                pass
            self.tip = None

LANG = "it" if "--ita" in sys.argv else "en"
S = get_strings(LANG)
H = get_help(LANG)

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
UNPLANNED_SPRINT = "— Unplanned —"

# Monospace font — pick first available on the system
def _pick_mono_font():
    try:
        import tkinter.font as tkfont
        families = tkfont.families()
        for candidate in ("Consolas", "DejaVu Sans Mono", "Liberation Mono",
                          "Ubuntu Mono", "Courier New", "Courier"):
            if candidate in families:
                return candidate
    except Exception:
        pass
    return "TkFixedFont"

MONO_FONT = _pick_mono_font()

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
    "│  {code:java}...{code} with language  │\n"
    "│  {quote}...{quote}   quote block     │\n"
    "│  {noformat}...{noformat} preformat   │\n"
    "│  {panel:title=T}...{panel} panel     │\n"
    "│  {color:red}text{color} colored      │\n"
    "│  bq. text            blockquote      │\n"
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

# Connection timeout for Jira operations (seconds)
JIRA_CONNECT_TIMEOUT = 10


def _check_jira_reachable(url: str, timeout: float = 5.0) -> bool:
    """Quick TCP check to verify Jira server is reachable (no auth needed).

    Returns True if a TCP connection to the server can be established
    within the given timeout. This avoids the long default timeout of
    python-jira/urllib3 which can block the GUI for minutes.
    """
    if not url:
        return False
    import socket
    from urllib.parse import urlparse
    try:
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        sock = socket.create_connection((host, port), timeout=timeout)
        sock.close()
        log.info(f"Jira server reachable: {host}:{port}")
        return True
    except (socket.timeout, socket.error, OSError) as e:
        log.warning(f"Jira server NOT reachable: {e}")
        return False


def _init_jira(url, user, token):
    global JIRA_AVAILABLE
    if url and token:
        try:
            import config
            config.JIRA_URL = url
            config.JIRA_TOKEN = token
            from jira import JIRA
            client = JIRA(server=url, token_auth=token, timeout=JIRA_CONNECT_TIMEOUT)
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
        self.root.geometry(WINDOW_GEOMETRY)
        self.root.configure(bg=BG_DARK)
        self.root.minsize(1000, 700)

        self.epics = []
        self.selected_epic = None
        self.story_tabs = []  # list of dicts: {title, description, sprint}
        self.story_checkboxes = []  # (var, story_data)
        self.tab_widgets = []  # list of widget refs per tab
        self.sprints = []  # sprint names from board
        self._sprint_id_map = {}  # sprint name -> sprint ID
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

        # Register window close handler BEFORE any operation that may show dialogs
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Control-s>", lambda e: self._save())
        self.root.bind("<Control-q>", lambda e: self._on_close())

        # Show busy cursor during initialization — deferred so the GUI renders first
        self._set_busy(True)
        self.root.after_idle(self._deferred_init)

    def _deferred_init(self):
        """Run heavy initialization (Jira connection, sprints, epics) after the GUI is visible."""
        try:
            self._init_jira_from_state()
            self._load_sprints()
            self._load_epics()
            self._restore_state()
            log.info("Application started")
        finally:
            self._set_busy(False)

    def _set_busy(self, busy: bool):
        """Set or clear the busy (watch) cursor on the entire application."""
        cursor = "watch" if busy else ""
        self.root.config(cursor=cursor)
        # Force visual update so the cursor change is immediate
        self.root.update_idletasks()

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
        ToolTip(lbl_epic, H["select_epic"])

        self.epic_var = tk.StringVar()
        self.epic_combo = tk.Listbox(parent, font=("Segoe UI", 9), height=4,
                                      bg="#001a40", fg=FG_TEXT, selectbackground=BTN_PRIMARY,
                                      selectforeground="white", bd=0, highlightthickness=1,
                                      highlightbackground=BORDER_COLOR, exportselection=False)
        self.epic_combo.pack(fill="x", padx=10, pady=(0, 5))
        self.epic_combo.bind("<<ListboxSelect>>", self._on_epic_selected)
        ToolTip(self.epic_combo, H["epic_list"])

        # Epic count
        self.epic_count_lbl = tk.Label(parent, text="Epics: 0", font=("Segoe UI", 9),
                                        fg="#aaaaaa", bg=BG_PANEL)
        self.epic_count_lbl.pack(anchor="w", padx=10)

        # Epic description (read-only with visual cue)
        desc_hdr = tk.Frame(parent, bg=BG_PANEL)
        desc_hdr.pack(fill="x", padx=10, pady=(5, 2))
        lbl_desc = tk.Label(desc_hdr, text=S["epic_description"], font=("Segoe UI", 10, "bold"),
                 fg=FG_TEXT, bg=BG_PANEL)
        lbl_desc.pack(side="left")
        ToolTip(lbl_desc, H["epic_desc"])
        btn_desc_help = tk.Button(desc_hdr, text="?", font=("Segoe UI", 7, "bold"),
                                  bg=BTN_INFO, fg="white", bd=0, padx=4, pady=0,
                                  cursor="hand2",
                                  command=self._show_epic_readonly_help)
        btn_desc_help.pack(side="left", padx=5)
        ToolTip(btn_desc_help, H["epic_desc_help"])
        self.epic_desc = scrolledtext.ScrolledText(parent, height=5, font=(MONO_FONT, 9),
                                                    bg="#2a2a2a", fg="#aaaaaa", insertbackground=FG_TEXT,
                                                    bd=0, wrap="word")
        self.epic_desc.pack(fill="x", padx=10, pady=(0, 10))
        ToolTip(self.epic_desc, H["epic_desc"])

        # Separator
        tk.Frame(parent, bg=BORDER_COLOR, height=1).pack(fill="x", padx=10, pady=5)

        # Stories header with count
        stories_header = tk.Frame(parent, bg=BG_PANEL)
        stories_header.pack(fill="x", padx=10, pady=(5, 2))
        lbl_stories_hdr = tk.Label(stories_header, text=S["historical_stories"], font=("Segoe UI", 10, "bold"),
                 fg=FG_TEXT, bg=BG_PANEL)
        lbl_stories_hdr.pack(side="left")
        ToolTip(lbl_stories_hdr, H.get("story_list_header",
                "List of User Stories associated with the selected epic. "
                "Check the stories you want to include in batch operations."))
        self.stories_count_lbl = tk.Label(stories_header, text="(0)", font=("Segoe UI", 9),
                                           fg="#aaaaaa", bg=BG_PANEL)
        self.stories_count_lbl.pack(side="left", padx=5)

        # Stories list container with visible border
        stories_container = tk.Frame(parent, bg=BG_CARD,
                                     highlightbackground=BORDER_COLOR, highlightthickness=1)
        stories_container.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.stories_frame = tk.Frame(stories_container, bg=BG_CARD)
        self.stories_frame.pack(fill="both", expand=True, padx=2, pady=2)
        # Add scrollbar
        canvas = tk.Canvas(self.stories_frame, bg=BG_CARD, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.stories_frame, orient="vertical", command=canvas.yview)
        self.stories_inner = tk.Frame(canvas, bg=BG_CARD)
        self.stories_inner.bind("<Configure>",
                                lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.stories_inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        # Mousewheel scroll — use tag-based binding to avoid global event interference
        self._stories_canvas = canvas

        def _on_canvas_enter(e):
            if sys.platform == "linux":
                canvas.bind("<Button-4>", lambda ev: canvas.yview_scroll(-1, "units"))
                canvas.bind("<Button-5>", lambda ev: canvas.yview_scroll(1, "units"))
            else:
                canvas.bind("<MouseWheel>",
                            lambda ev: canvas.yview_scroll(-1 * (ev.delta // 120), "units"))

        def _on_canvas_leave(e):
            if sys.platform == "linux":
                canvas.unbind("<Button-4>")
                canvas.unbind("<Button-5>")
            else:
                canvas.unbind("<MouseWheel>")

        canvas.bind("<Enter>", _on_canvas_enter)
        canvas.bind("<Leave>", _on_canvas_leave)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        ToolTip(canvas, H.get("story_list_area",
                "Scroll to browse all stories. Check/uncheck to select stories for batch operations."))

        # Buttons row
        btn_frame = tk.Frame(parent, bg=BG_PANEL)
        btn_frame.pack(fill="x", padx=10, pady=5)
        btn_add = self._make_btn(btn_frame, S["add_story"], BTN_SUCCESS, self._add_story)
        btn_add.pack(side="left")
        ToolTip(btn_add, H["add_story"])
        btn_load = self._make_btn(btn_frame, S["load_stories"], BTN_INFO, self._load_from_epic)
        btn_load.pack(side="left", padx=5)
        ToolTip(btn_load, H["load_stories"])

    def _build_right_panel(self, parent):
        # Tab area header
        header = tk.Frame(parent, bg=BG_DARK)
        header.pack(fill="x", pady=(0, 5))
        lbl_us_header = tk.Label(header, text="📝 User Stories", font=("Segoe UI", 12, "bold"),
                 fg=FG_TITLE, bg=BG_DARK)
        lbl_us_header.pack(side="left")
        ToolTip(lbl_us_header, H.get("us_panel_header",
                "Editing area for User Stories. Each tab represents a story to be created or updated on Jira."))

        # Notebook for story tabs
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill="both", expand=True)

        # Bottom action bar
        actions = tk.Frame(parent, bg=BG_DARK)
        actions.pack(fill="x", pady=(5, 0))
        btn_sched = self._make_btn(actions, "📅 Scheduling", BTN_INFO, self._show_scheduling)
        btn_sched.pack(side="left")
        ToolTip(btn_sched, H["scheduling"])
        self.btn_create = self._make_btn(actions, S["confirm_create"], BTN_PRIMARY, self._create_stories)
        self.btn_create.pack(side="left", padx=(5, 0))
        ToolTip(self.btn_create, H["create_update"])
        btn_save = self._make_btn(actions, "💾 Save US", BTN_SUCCESS, self._save_stories_to_file)
        btn_save.pack(side="left", padx=5)
        ToolTip(btn_save, H["save_us"])
        # Tag-as-generated toggle button (styled like neighboring buttons)
        self.tag_generated_var = tk.BooleanVar(value=True)
        self._btn_tag = tk.Button(actions, text=S["tag_generated"],
                                  font=("Segoe UI", 9, "bold"),
                                  bg=BTN_SUCCESS, fg="white",
                                  activebackground=BTN_SUCCESS,
                                  activeforeground="white", bd=0,
                                  padx=12, pady=4, cursor="hand2",
                                  command=self._toggle_tag_generated)
        self._btn_tag.pack(side="left", padx=5)
        self._update_tag_btn_style()
        ToolTip(self._btn_tag, H["tag_generated"])
        btn_quit = tk.Button(actions, text="⏻ Quit", font=("Segoe UI", 9, "bold"),
                             bg=BTN_DANGER, fg="white", activebackground=BTN_DANGER,
                             activeforeground="white", bd=0, padx=12, pady=4,
                             cursor="hand2", command=self._on_close)
        btn_quit.pack(side="right")
        ToolTip(btn_quit, H["quit"])
        btn_hist = self._make_btn(actions, S["history"], BTN_INFO, self._show_history)
        btn_hist.pack(side="right", padx=5)
        ToolTip(btn_hist, H["history"])

    def _build_credentials_panel(self):
        """Build credentials input panel at the bottom."""
        cred_frame = tk.Frame(self.root, bg=BG_PANEL, height=45,
                              highlightbackground=BORDER_COLOR, highlightthickness=1)
        cred_frame.pack(fill="x", padx=5, pady=(0, 0), side="bottom")
        cred_frame.pack_propagate(False)

        lbl = tk.Label(cred_frame, text="🔐 Jira:", font=("Segoe UI", 9, "bold"),
                       fg=FG_ACCENT, bg=BG_PANEL)
        lbl.pack(side="left", padx=(10, 5))
        ToolTip(lbl, H["jira_cred"])

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
        ToolTip(self.btn_connect, H["connect"])

        # Pre-fill from state
        state = load_state()
        if state.get("jira_token"):
            self.cred_token.insert(0, state["jira_token"])
        elif JIRA_TOKEN:
            self.cred_token.insert(0, JIRA_TOKEN)

    def _init_jira_from_state(self):
        """Try to initialize Jira from saved token or env var.

        Skips the heavy connection attempt if the server is not reachable
        (pre-check already done in main, but also guards against slow init).
        """
        state = load_state()
        token = state.get("jira_token", "") or JIRA_TOKEN
        if not token or not JIRA_URL:
            self._indicator_set("disconnected")
            return
        # Quick reachability check (avoids long blocking if server is down)
        if not _check_jira_reachable(JIRA_URL, timeout=5.0):
            log.warning("Jira unreachable during init — starting in DEMO mode")
            self._indicator_set("disconnected")
            return
        if _init_jira(JIRA_URL, "", token):
            self._indicator_set("connected")
        else:
            self._indicator_set("disconnected")

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
        # Quick reachability check before heavy connection attempt
        if not _check_jira_reachable(JIRA_URL, timeout=5.0):
            self._set_status("✗ Jira server unreachable — check VPN/network")
            self._indicator_set("disconnected")
            return
        if _init_jira(JIRA_URL, "", token):
            self._indicator_set("connected")
            self._load_sprints()
            self._load_epics()
            self._set_status(f"✓ Connected to Jira — {len(self.epics)} epics loaded")
        else:
            self._indicator_set("disconnected")
            self._set_status("✗ Connection failed — check token or jira_url")

    def _build_status_bar(self):
        bar = tk.Frame(self.root, bg=BG_PANEL, height=25)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        mode = "JIRA" if JIRA_AVAILABLE else "DEMO"
        # Connection/loading indicator: ○ = not connected, ● = authenticated
        self.indicator_lbl = tk.Label(bar, text="○", font=("Segoe UI", 10),
                                      fg="#888888", bg=BG_PANEL)
        self.indicator_lbl.pack(side="left", padx=(5, 0))
        self._indicator_tooltip = ToolTip(self.indicator_lbl, H["indicator"])
        self.status_lbl = tk.Label(bar, text=f"  Mode: {mode}  |  Ctrl+S: Save  |  Ctrl+Q: Quit",
                                    font=("Segoe UI", 8), fg="#888888", bg=BG_PANEL)
        self.status_lbl.pack(side="left", padx=5)
        ToolTip(self.status_lbl, H["status_bar"])
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

    def _toggle_tag_generated(self):
        """Toggle the tag-as-generated flag and update button appearance."""
        current = self.tag_generated_var.get()
        self.tag_generated_var.set(not current)
        self._update_tag_btn_style()

    def _update_tag_btn_style(self):
        """Update tag button color based on ON/OFF state."""
        if self.tag_generated_var.get():
            self._btn_tag.config(bg=BTN_SUCCESS, activebackground=BTN_SUCCESS,
                                 relief="sunken")
        else:
            self._btn_tag.config(bg="#555555", activebackground="#555555",
                                 relief="raised")

    # --- Indicator ---

    def _indicator_set(self, state: str):
        """Set indicator: 'loading', 'ok', 'error'.

        Shape reflects Jira connection:
          ● (filled) = authenticated
          ○ (outline) = not connected
        Color reflects data-loading state:
          green = stories loaded ok
          yellow blink = loading in progress
          red = timeout/error
          gray = idle
        """
        if self._blink_id:
            self.root.after_cancel(self._blink_id)
            self._blink_id = None
        symbol = "●" if JIRA_AVAILABLE else "○"
        if state == "loading":
            self._indicator_tooltip.text = "Reading User Stories..."
            self.indicator_lbl.config(text=symbol)
            self._blink_yellow()
        elif state == "ok":
            self.indicator_lbl.config(text=symbol, fg="#66bb6a")
            self._indicator_tooltip.text = "User Stories updated"
        elif state == "error":
            self.indicator_lbl.config(text=symbol, fg="#ef5350")
            self._indicator_tooltip.text = "Timeout reading User Stories"
        elif state == "connected":
            self.indicator_lbl.config(text="●", fg="#66bb6a")
            self._indicator_tooltip.text = "Connected to Jira"
        elif state == "disconnected":
            self.indicator_lbl.config(text="○", fg="#888888")
            self._indicator_tooltip.text = "Not connected to Jira — showing cached data"

    def _blink_yellow(self):
        cur = self.indicator_lbl.cget("fg")
        nxt = "#ffca28" if cur != "#ffca28" else BG_PANEL
        self.indicator_lbl.config(fg=nxt)
        self._blink_id = self.root.after(500, self._blink_yellow)

    def _open_sprint_url(self, sprint_name: str):
        """Open the Jira backlog planning page for the team board."""
        from config import JIRA_URL, BOARD_ID
        url = f"{JIRA_URL}/secure/RapidBoard.jspa?rapidView={BOARD_ID}&view=planning.nodetail&issueLimit=100"
        import webbrowser
        webbrowser.open(url)

    # --- Data Loading ---

    def _load_sprints(self):
        """Load sprint names and ID mapping from the configured board."""
        if JIRA_AVAILABLE:
            try:
                import jira_client
                self.sprints = jira_client.get_board_sprints()
                # Build name→ID mapping for sprint links
                details = jira_client.get_board_sprints_details()
                self._sprint_id_map = {d["name"]: d["id"] for d in details}
                log.info(f"Loaded {len(self.sprints)} sprints")
            except Exception as e:
                log.error(f"Failed to load sprints: {e}")
                self.sprints = []
                self._sprint_id_map = {}
        else:
            self.sprints = []
            self._sprint_id_map = {}

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

        # Preload stories only for the first (target) epic — others loaded on demand
        self._epic_stories_cache = {}
        if JIRA_AVAILABLE and self.epics:
            import jira_client
            # Only preload first two epics (target + fallback source)
            for e in self.epics[:2]:
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
            # Load stories on-demand if not cached
            if selected_key not in self._epic_stories_cache:
                try:
                    import jira_client
                    self._epic_stories_cache[selected_key] = jira_client.get_epic_stories(selected_key)
                    log.info(f"  On-demand load: {selected_key} → {len(self._epic_stories_cache[selected_key])} stories")
                except Exception as ex:
                    log.error(f"  On-demand load failed for {selected_key}: {ex}")
                    self._epic_stories_cache[selected_key] = []

            # If selecting the target (latest) epic
            if selected_idx == 0:
                target_stories = self._epic_stories_cache.get(selected_key, [])
                if target_stories:
                    stories = target_stories
                elif source_idx >= 0:
                    # Latest has no stories, use source as template
                    source_key = self.epics[source_idx]["key"]
                    # Also load source on-demand if needed
                    if source_key not in self._epic_stories_cache:
                        try:
                            import jira_client
                            self._epic_stories_cache[source_key] = jira_client.get_epic_stories(source_key)
                        except Exception:
                            self._epic_stories_cache[source_key] = []
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
                                variable=var, bg=BG_CARD, fg=FG_TEXT,
                                selectcolor=BG_CARD, activebackground=BG_CARD,
                                activeforeground=FG_ACCENT, font=("Segoe UI", 8),
                                anchor="w", wraplength=320,
                                command=lambda idx=i: self._select_tab_by_index(idx))
            cb.pack(fill="x", anchor="w", pady=1, padx=4)
            # Tooltip with story details
            tip_text = f"{s.get('key', 'NEW')} — {s['summary']}"
            if s.get("sprint"):
                tip_text += f"\nSprint: {s['sprint']}"
            if s.get("status"):
                tip_text += f"\nStatus: {s['status']}"
            if s.get("assignee"):
                tip_text += f"\nAssignee: {s['assignee']}"
            tip_text += "\n\nClick to navigate to this story tab."
            ToolTip(cb, tip_text)
            self.story_checkboxes.append((var, s))

        # Create tabs from stories
        is_resolved = target_epic.get("resolution", "Unresolved").lower() != "unresolved"
        self._clear_tabs()
        for s in stories:
            if from_template:
                # Template from older epic — new stories, sprint must be unplanned
                self._add_tab(s["summary"], s.get("description", ""),
                              key="", existing=False, readonly=False,
                              status="", resolution="", assignee="",
                              acceptance_criteria=s.get("acceptance_criteria", ""),
                              sprint="",
                              labels=s.get("labels"),
                              assignee_key=s.get("assignee_key", ""),
                              components=s.get("components"),
                              priority=s.get("priority", ""),
                              story_points=s.get("story_points", ""))
            elif is_old_epic:
                # Viewing an older epic — existing stories, readonly
                self._add_tab(s["summary"], s.get("description", ""),
                              key=s.get("key", ""), existing=True, readonly=True,
                              status=s.get("status", ""),
                              resolution=s.get("resolution", ""),
                              assignee=s.get("assignee", ""),
                              acceptance_criteria=s.get("acceptance_criteria", ""),
                              sprint=s.get("sprint", ""),
                              labels=s.get("labels"),
                              assignee_key=s.get("assignee_key", ""),
                              components=s.get("components"),
                              priority=s.get("priority", ""),
                              story_points=s.get("story_points", ""))
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
                              priority=s.get("priority", ""),
                              story_points=s.get("story_points", ""))

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
        ToolTip(self._add_to_epic_btn, H["add_to_epic"])

    def _add_stories_to_epic(self, target_epic):
        """Clone selected stories from old epic and create them as NEW stories under the target epic.

        Always creates new stories — never re-links existing ones. The original
        stories remain untouched in their current epic.
        """
        if not JIRA_AVAILABLE:
            messagebox.showerror("Error", "Jira not available.")
            return

        selected = [(var, s) for var, s in self.story_checkboxes if var.get()]
        if not selected:
            messagebox.showwarning("No Selection", "Select at least one story to add.")
            return

        msg = f"Clone {len(selected)} stories to epic {target_epic['key']}?\n\nNew stories will be created — originals remain unchanged."
        if LANG == "it":
            msg = f"Clonare {len(selected)} storie nell'epica {target_epic['key']}?\n\nVerranno create nuove storie — le originali restano invariate."
        if not messagebox.askyesno("Confirm", msg):
            return

        log.info(f"Cloning {len(selected)} stories to {target_epic['key']}")
        import jira_client
        created = []
        errors = []
        for _, s in selected:
            try:
                desc = s.get("description", "")
                ac = s.get("acceptance_criteria", "")
                key = jira_client.create_story(
                    target_epic["key"], s["summary"], desc,
                    s.get("sprint", ""), s.get("labels"),
                    s.get("assignee_key", ""), s.get("components"),
                    s.get("priority", ""), ac)
                created.append(key)
                log.info(f"  Created {key} (cloned from {s.get('key', 'template')}): {s['summary']}")
            except Exception as e:
                errors.append(f"{s.get('key', s['summary'])}: {e}")
                log.error(f"  Failed: {s.get('key', s['summary'])}: {e}")

        msg = ""
        if created:
            msg += f"✓ Created: {', '.join(created)}\n"
        if errors:
            msg += f"\n✗ Errors:\n" + "\n".join(errors)
        messagebox.showinfo("Results", msg)
        self._set_status(f"Cloned {len(created)} stories to {target_epic['key']}")

        # Refresh cache and reload
        if created:
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
                 components: list = None, priority: str = "",
                 story_points: str = ""):
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
        ToolTip(lbl_title, H["us_title"])
        state = "disabled" if readonly else "normal"
        title_entry = tk.Entry(frame, font=("Segoe UI", 10), bg="#0a0a1a", fg=FG_TEXT,
                               insertbackground=FG_TEXT, bd=0, highlightbackground=BORDER_COLOR,
                               highlightthickness=1, state="normal")
        title_entry.pack(fill="x", padx=10, pady=(0, 5))
        title_entry.insert(0, title)
        title_entry.config(state=state)
        ToolTip(title_entry, H["us_title"])

        # Description
        desc_hdr = tk.Frame(frame, bg=BG_CARD)
        desc_hdr.pack(fill="x", padx=10, pady=(5, 2))
        lbl_desc_tab = tk.Label(desc_hdr, text=S["us_description"], font=("Segoe UI", 10, "bold"),
                 fg=FG_ACCENT, bg=BG_CARD)
        lbl_desc_tab.pack(side="left")
        ToolTip(lbl_desc_tab, H["us_desc"])
        btn_help = tk.Button(desc_hdr, text="?", font=("Segoe UI", 7, "bold"),
                             bg=BTN_INFO, fg="white", bd=0, padx=4, pady=0,
                             cursor="hand2", command=self._show_markup_help)
        btn_help.pack(side="left", padx=5)
        ToolTip(btn_help, H["markup_help"])
        desc_text = scrolledtext.ScrolledText(frame, height=8, font=(MONO_FONT, 9),
                                              bg="#0a0a1a", fg=FG_TEXT, insertbackground=FG_TEXT,
                                              bd=0, wrap="word", highlightbackground=BORDER_COLOR,
                                              highlightthickness=1)
        desc_text.pack(fill="both", expand=True, padx=10, pady=(0, 5))
        desc_text.insert("1.0", description.replace("\r", ""))
        ToolTip(desc_text, H["us_desc"])
        # Preview button (always visible)
        btn_preview_desc = tk.Button(desc_hdr, text="👁", font=("Segoe UI", 9),
                                     bg="#5c6bc0", fg="white", bd=0, padx=4, pady=0,
                                     cursor="hand2",
                                     command=lambda: self._preview_markup(desc_text))
        btn_preview_desc.pack(side="left", padx=3)
        ToolTip(btn_preview_desc, H.get("preview_markup", "Preview rendered markup"))
        if not readonly:
            btn_tr_desc = tk.Button(desc_hdr, text="IT→EN", font=("Segoe UI", 8, "bold"),
                                    bg="#f39c12", fg="white", bd=0, padx=4, pady=0,
                                    cursor="hand2",
                                    command=lambda: self._translate_popup(desc_text))
            btn_tr_desc.pack(side="left", padx=3)
            ToolTip(btn_tr_desc, H["translate"])
        if readonly:
            desc_text.config(state="disabled")

        # Acceptance Criteria
        ac_hdr = tk.Frame(frame, bg=BG_CARD)
        ac_hdr.pack(fill="x", padx=10, pady=(5, 2))
        lbl_ac = tk.Label(ac_hdr, text="Acceptance Criteria:", font=("Segoe UI", 10, "bold"),
                 fg=FG_ACCENT, bg=BG_CARD)
        lbl_ac.pack(side="left")
        ToolTip(lbl_ac, H["us_ac"])
        btn_help_ac = tk.Button(ac_hdr, text="?", font=("Segoe UI", 7, "bold"),
                                bg=BTN_INFO, fg="white", bd=0, padx=4, pady=0,
                                cursor="hand2", command=self._show_markup_help)
        btn_help_ac.pack(side="left", padx=5)
        ToolTip(btn_help_ac, H["markup_help"])
        ac_text = scrolledtext.ScrolledText(frame, height=4, font=(MONO_FONT, 9),
                                            bg="#0a0a1a", fg=FG_TEXT, insertbackground=FG_TEXT,
                                            bd=0, wrap="word", highlightbackground=BORDER_COLOR,
                                            highlightthickness=1)
        ac_text.pack(fill="x", padx=10, pady=(0, 5))
        ToolTip(ac_text, H["us_ac"])
        # Preview button for AC (always visible)
        btn_preview_ac = tk.Button(ac_hdr, text="👁", font=("Segoe UI", 9),
                                   bg="#5c6bc0", fg="white", bd=0, padx=4, pady=0,
                                   cursor="hand2",
                                   command=lambda: self._preview_markup(ac_text))
        btn_preview_ac.pack(side="left", padx=3)
        ToolTip(btn_preview_ac, H.get("preview_markup", "Preview rendered markup"))
        if not readonly:
            btn_tr_ac = tk.Button(ac_hdr, text="IT→EN", font=("Segoe UI", 8, "bold"),
                                  bg="#f39c12", fg="white", bd=0, padx=4, pady=0,
                                  cursor="hand2",
                                  command=lambda: self._translate_popup(ac_text))
            btn_tr_ac.pack(side="left", padx=3)
            ToolTip(btn_tr_ac, H["translate"])
        ac_text.insert("1.0", acceptance_criteria.replace("\r", ""))
        if readonly:
            ac_text.config(state="disabled")

        # Sprint
        sprint_frame = tk.Frame(frame, bg=BG_CARD)
        sprint_frame.pack(fill="x", padx=10, pady=(5, 5))
        lbl_sprint = tk.Label(sprint_frame, text=S["us_sprint"], font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_sprint.pack(side="left")
        ToolTip(lbl_sprint, H["us_sprint"])
        if not existing:
            sprint_values = [UNPLANNED_SPRINT] + self.sprints
        else:
            sprint_values = self.sprints
        sprint_combo = ttk.Combobox(sprint_frame, font=("Segoe UI", 9), width=30,
                                    values=sprint_values, state="readonly" if readonly else "normal")
        sprint_combo.pack(side="left", padx=(5, 0))
        ToolTip(sprint_combo, H["us_sprint"])
        if sprint:
            sprint_combo.set(sprint)
        elif not existing:
            sprint_combo.set(UNPLANNED_SPRINT)
        elif self.sprints:
            sprint_combo.set(self.sprints[0])

        # Sprint link icon
        sprint_link_btn = tk.Label(sprint_frame, text="🔗", font=("Segoe UI", 10),
                                   fg=FG_ACCENT, bg=BG_CARD, cursor="hand2")
        sprint_link_btn.pack(side="left", padx=(5, 0))
        ToolTip(sprint_link_btn, H.get("sprint_link", "Open sprint in Jira"))

        def _update_sprint_link(*_args):
            sel = sprint_combo.get()
            if sel and sel != UNPLANNED_SPRINT and sel in self._sprint_id_map:
                sprint_link_btn.config(fg=FG_ACCENT, cursor="hand2")
                sprint_link_btn.bind("<Button-1>", lambda e: self._open_sprint_url(sel))
            else:
                sprint_link_btn.config(fg="#555555", cursor="arrow")
                sprint_link_btn.unbind("<Button-1>")

        sprint_combo.bind("<<ComboboxSelected>>", _update_sprint_link)
        _update_sprint_link()  # set initial state

        # Labels
        labels_frame = tk.Frame(frame, bg=BG_CARD)
        labels_frame.pack(fill="x", padx=10, pady=(5, 5))
        lbl_labels = tk.Label(labels_frame, text="Labels:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_labels.pack(side="left")
        ToolTip(lbl_labels, H["us_labels"])
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
        ToolTip(labels_entry, H["us_labels"])

        # Story Points (on same row as labels)
        lbl_sp = tk.Label(labels_frame, text="SP:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_sp.pack(side="left", padx=(15, 0))
        ToolTip(lbl_sp, H.get("us_story_points", "Story Points"))
        sp_entry = tk.Entry(labels_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                            insertbackground=FG_TEXT, bd=0, width=4,
                            highlightbackground=BORDER_COLOR, highlightthickness=1,
                            state="normal")
        sp_entry.pack(side="left", padx=(5, 0))
        sp_entry.insert(0, story_points)
        if readonly:
            sp_entry.config(state="disabled")
        ToolTip(sp_entry, H.get("us_story_points", "Story Points"))

        # Assignee
        assign_frame = tk.Frame(frame, bg=BG_CARD)
        assign_frame.pack(fill="x", padx=10, pady=(2, 2))
        lbl_assign = tk.Label(assign_frame, text="Assignee:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_assign.pack(side="left")
        ToolTip(lbl_assign, H["us_assignee"])
        assignee_entry = tk.Entry(assign_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                                  insertbackground=FG_TEXT, bd=0, width=20,
                                  highlightbackground=BORDER_COLOR, highlightthickness=1)
        assignee_entry.pack(side="left", padx=(5, 10))
        assignee_entry.insert(0, assignee_key or assignee)
        if readonly:
            assignee_entry.config(state="disabled")
        ToolTip(assignee_entry, H["us_assignee"])

        # Components
        lbl_comp = tk.Label(assign_frame, text="Components:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_comp.pack(side="left")
        ToolTip(lbl_comp, H["us_components"])
        components_entry = tk.Entry(assign_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                                    insertbackground=FG_TEXT, bd=0, width=15,
                                    highlightbackground=BORDER_COLOR, highlightthickness=1)
        components_entry.pack(side="left", padx=(5, 10))
        components_entry.insert(0, ",".join(components or []))
        if readonly:
            components_entry.config(state="disabled")
        ToolTip(components_entry, H["us_components"])

        # Priority
        lbl_prio = tk.Label(assign_frame, text="Priority:", font=("Segoe UI", 9, "bold"),
                 fg=FG_TEXT, bg=BG_CARD)
        lbl_prio.pack(side="left")
        ToolTip(lbl_prio, H["us_priority"])
        priority_entry = tk.Entry(assign_frame, font=("Segoe UI", 9), bg="#0a0a1a", fg=FG_TEXT,
                                  insertbackground=FG_TEXT, bd=0, width=10,
                                  highlightbackground=BORDER_COLOR, highlightthickness=1)
        priority_entry.pack(side="left", padx=(5, 0))
        priority_entry.insert(0, priority)
        if readonly:
            priority_entry.config(state="disabled")
        ToolTip(priority_entry, H["us_priority"])

        # Buttons (only if not readonly)
        btn_frame = tk.Frame(frame, bg=BG_CARD)
        btn_frame.pack(fill="x", padx=10, pady=(0, 5))

        if not readonly:
            tab_idx = len(self.tab_widgets)
            btn_split = self._make_btn(btn_frame, S["split_story"], "#f39c12",
                           lambda i=tab_idx: self._split_tab(i))
            btn_split.pack(side="left", padx=5)
            ToolTip(btn_split, H["split_story"])
            btn_remove = self._make_btn(btn_frame, S["remove_tab"], BTN_DANGER,
                           lambda i=tab_idx: self._remove_tab(i))
            btn_remove.pack(side="right")
            ToolTip(btn_remove, H["remove_tab"])

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
                                  "story_points": sp_entry,
                                  "existing": existing, "readonly": readonly,
                                  "key": key})
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
        win.geometry(POPUP_GEOMETRIES.get(popup_type, geometry))
        win.configure(bg=BG_DARK)
        self._popups[popup_type] = win
        win.protocol("WM_DELETE_WINDOW", lambda: self._close_popup(popup_type))
        return win

    def _close_popup(self, popup_type: str):
        if popup_type in self._popups:
            try:
                POPUP_GEOMETRIES[popup_type] = self._popups[popup_type].geometry()
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
        preview = scrolledtext.ScrolledText(win, height=12, font=(MONO_FONT, 9),
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
        text = tk.Text(win, font=(MONO_FONT, 10), bg="#0a0a1a", fg=FG_TEXT,
                       bd=0, padx=10, pady=10)
        text.pack(fill="both", expand=True, padx=5, pady=5)
        text.insert("1.0", JIRA_MARKUP_HELP)
        text.config(state="disabled")
        self._make_btn(win, "Close", BTN_DANGER, win.destroy).pack(pady=5)

    def _preview_markup(self, text_widget):
        """Render Jira wiki markup as formatted text in a preview popup."""
        content = text_widget.get("1.0", "end-1c").replace("\r", "")
        if not content.strip():
            self._set_status("No text to preview")
            return

        win = self._open_popup("markup_preview", "Markup Preview", "620x450")
        win.resizable(True, True)

        tk.Label(win, text="Jira Markup Preview", font=("Segoe UI", 11, "bold"),
                 fg=FG_TITLE, bg=BG_DARK).pack(anchor="w", padx=10, pady=(10, 5))

        preview = tk.Text(win, font=("Segoe UI", 10), bg="#0d0d1a", fg=FG_TEXT,
                          bd=0, wrap="word", padx=10, pady=10,
                          highlightbackground=BORDER_COLOR, highlightthickness=1)
        preview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Configure tags for Jira markup rendering
        preview.tag_configure("bold", font=("Segoe UI", 10, "bold"))
        preview.tag_configure("italic", font=("Segoe UI", 10, "italic"))
        preview.tag_configure("bolditalic", font=("Segoe UI", 10, "bold italic"))
        preview.tag_configure("underline", underline=True)
        preview.tag_configure("strikethrough", overstrike=True)
        preview.tag_configure("monospace", font=(MONO_FONT, 9), background="#1a1a2e",
                              foreground="#a5d6a7", lmargin1=20, lmargin2=20)
        preview.tag_configure("code_border", font=(MONO_FONT, 9), foreground="#5c6bc0",
                              background="#0f0f1e")
        preview.tag_configure("h1", font=("Segoe UI", 14, "bold"), foreground=FG_ACCENT)
        preview.tag_configure("h2", font=("Segoe UI", 12, "bold"), foreground=FG_ACCENT)
        preview.tag_configure("h3", font=("Segoe UI", 11, "bold"), foreground=FG_ACCENT)
        preview.tag_configure("h4", font=("Segoe UI", 10, "bold"), foreground=FG_ACCENT)
        preview.tag_configure("color_red", foreground="#ef5350")
        preview.tag_configure("color_green", foreground="#66bb6a")
        preview.tag_configure("color_blue", foreground="#42a5f5")
        preview.tag_configure("color_orange", foreground="#ffa726")
        preview.tag_configure("color_purple", foreground="#ce93d8")
        preview.tag_configure("color_yellow", foreground="#ffee58")
        preview.tag_configure("color_cyan", foreground="#4dd0e1")
        preview.tag_configure("color_gray", foreground="#9e9e9e")
        preview.tag_configure("color_grey", foreground="#9e9e9e")
        preview.tag_configure("color_navy", foreground="#5c6bc0")
        preview.tag_configure("color_teal", foreground="#26a69a")
        preview.tag_configure("color_maroon", foreground="#a1887f")
        preview.tag_configure("color_white", foreground="#ffffff")
        preview.tag_configure("color_black", foreground="#757575")
        preview.tag_configure("quote", foreground="#b0bec5", lmargin1=20, lmargin2=20,
                              font=("Segoe UI", 10, "italic"), background="#0f1520")
        preview.tag_configure("quote_bar", foreground="#5c6bc0", font=("Segoe UI", 10))
        preview.tag_configure("bullet", lmargin1=15, lmargin2=30)
        preview.tag_configure("numbered", lmargin1=15, lmargin2=30)
        preview.tag_configure("table_header", font=(MONO_FONT, 9, "bold"),
                              background="#1a2a4a")
        preview.tag_configure("table_cell", font=(MONO_FONT, 9),
                              background="#0f1a2e")
        preview.tag_configure("table_border", font=(MONO_FONT, 9),
                              foreground="#555555")
        preview.tag_configure("hr", foreground="#555555")
        preview.tag_configure("link", foreground="#42a5f5", underline=True)

        self._render_jira_markup(preview, content)
        preview.config(state="disabled")

        self._make_btn(win, "Close", BTN_DANGER, win.destroy).pack(pady=5)

    def _render_jira_markup(self, text_widget, content: str):
        """Parse and render Jira wiki markup into a tk.Text widget with tags."""
        import re
        lines = content.split("\n")
        in_code_block = False
        in_noformat = False
        in_quote_block = False
        in_panel = False
        numbered_counter = 0
        table_rows = []  # accumulate table rows for column alignment

        def _flush_table():
            """Render accumulated table rows with aligned columns."""
            nonlocal table_rows
            if not table_rows:
                return
            # Calculate max width per column
            max_cols = max(len(row["cells"]) for row in table_rows)
            col_widths = [0] * max_cols
            for row in table_rows:
                for i, cell in enumerate(row["cells"]):
                    col_widths[i] = max(col_widths[i], len(cell))
            # Render each row with padding
            for row in table_rows:
                tag = row["tag"]
                padded = []
                for i, cell in enumerate(row["cells"]):
                    padded.append(cell.ljust(col_widths[i] if i < len(col_widths) else 0))
                text_widget.insert("end", "  ", "table_border")
                text_widget.insert("end", " │ ".join(padded), tag)
                text_widget.insert("end", "\n")
            table_rows = []

        for line in lines:
            # --- Multi-line blocks ---

            # {code} handling — multiple forms:
            # 1. {code} alone on a line → toggle block
            # 2. {code}text...{code} on same line → inline code block
            # 3. {code}text (open with content) → start block, text is first line
            # 4. text{code} (close with content) → text is last line, end block
            if not in_code_block and re.search(r'\{code[^}]*\}', line):
                _flush_table()
                # Check if it's a single-line code: {code}...{code} with content between
                inline_match = re.match(r'^(.*?)\{code[^}]*\}(.+?)\{code\}(.*)$', line)
                if inline_match:
                    # Inline single-line code block
                    before = inline_match.group(1)
                    code_content = inline_match.group(2)
                    after = inline_match.group(3)
                    if before.strip():
                        self._render_inline_markup(text_widget, before)
                        text_widget.insert("end", "\n")
                    text_widget.insert("end", "  ╭───────────────────────────────────────╮\n", "code_border")
                    text_widget.insert("end", "  │  " + code_content + "\n", "monospace")
                    text_widget.insert("end", "  ╰───────────────────────────────────────╯\n", "code_border")
                    if after.strip():
                        self._render_inline_markup(text_widget, after)
                        text_widget.insert("end", "\n")
                    continue
                # Check: {code...} alone on line → start block
                if re.match(r'^\s*\{code[^}]*\}\s*$', line):
                    in_code_block = True
                    lang_match = re.search(r'\{code:(\w+)\}', line)
                    title_match = re.search(r'title=([^|}]+)', line)
                    label = ""
                    if title_match:
                        label = f" {title_match.group(1).strip()}"
                    elif lang_match:
                        label = f" [{lang_match.group(1)}]"
                    text_widget.insert("end", f"  ╭─── code{label} ──────────────────────────╮\n", "code_border")
                    continue
                # {code}text... → start block, text is first code line
                open_match = re.match(r'^\s*\{code[^}]*\}(.+)$', line)
                if open_match:
                    in_code_block = True
                    text_widget.insert("end", "  ╭───────────────────────────────────────╮\n", "code_border")
                    text_widget.insert("end", "  │  " + open_match.group(1) + "\n", "monospace")
                    continue
                # Fallthrough: should not happen, but treat as normal line
            elif in_code_block:
                # Check if line ends the code block
                close_match = re.match(r'^(.*?)\{code\}\s*$', line)
                if close_match:
                    in_code_block = False
                    content_before = close_match.group(1)
                    if content_before.strip():
                        text_widget.insert("end", "  │  " + content_before + "\n", "monospace")
                    text_widget.insert("end", "  ╰───────────────────────────────────────╯\n", "code_border")
                else:
                    text_widget.insert("end", "  │  " + line + "\n", "monospace")
                continue

            # {noformat} — same logic (simplified: assumes alone on line)
            if re.match(r'^\s*\{noformat[^}]*\}\s*$', line):
                _flush_table()
                if in_noformat:
                    in_noformat = False
                    text_widget.insert("end", "  ╰───────────────────────────────────────╯\n", "code_border")
                else:
                    in_noformat = True
                    text_widget.insert("end", "  ╭─── noformat ────────────────────────────╮\n", "code_border")
                continue
            if in_noformat:
                text_widget.insert("end", "  │  " + line + "\n", "monospace")
                continue

            # {quote}
            if re.match(r'^\s*\{quote\}\s*$', line):
                _flush_table()
                if in_quote_block:
                    in_quote_block = False
                else:
                    in_quote_block = True
                continue
            if in_quote_block:
                text_widget.insert("end", "  ┃ ", "quote_bar")
                self._render_inline_markup(text_widget, line)
                text_widget.insert("end", "\n")
                continue

            # {panel} — simplified rendering
            if re.match(r'^\s*\{panel(?::[^}]*)?\}\s*$', line):
                _flush_table()
                if in_panel:
                    in_panel = False
                    text_widget.insert("end", "  └─────────────────────────────\n", "hr")
                else:
                    in_panel = True
                    title_match = re.search(r'title=([^|}]+)', line)
                    if title_match:
                        text_widget.insert("end", f"  ┌─ {title_match.group(1).strip()} ─────────────\n", "table_header")
                    else:
                        text_widget.insert("end", "  ┌─────────────────────────────\n", "hr")
                continue
            if in_panel:
                text_widget.insert("end", "  │ ", "hr")
                self._render_inline_markup(text_widget, line)
                text_widget.insert("end", "\n")
                continue

            # --- Single-line elements ---

            # Headings: h1. through h6.
            h_match = re.match(r'^h([1-6])\.\s*(.*)', line)
            if h_match:
                _flush_table()
                level = int(h_match.group(1))
                heading_text = h_match.group(2)
                tag = f"h{min(level, 4)}"
                text_widget.insert("end", heading_text + "\n", tag)
                numbered_counter = 0
                continue

            # Horizontal rule
            if line.strip() == "----":
                _flush_table()
                text_widget.insert("end", "─" * 50 + "\n", "hr")
                continue

            # Blockquote (single line)
            if line.startswith("bq. "):
                _flush_table()
                text_widget.insert("end", "  ┃ ", "quote_bar")
                self._render_inline_markup(text_widget, line[4:])
                text_widget.insert("end", "\n")
                continue

            # Bullet list (* or ** or ***)
            bullet_match = re.match(r'^(\*+|-)\s+(.*)', line)
            if bullet_match:
                _flush_table()
                depth = len(bullet_match.group(1)) if bullet_match.group(1) != "-" else 1
                indent = "  " * depth
                text_widget.insert("end", indent + "• ", "bullet")
                self._render_inline_markup(text_widget, bullet_match.group(2))
                text_widget.insert("end", "\n")
                numbered_counter = 0
                continue

            # Numbered list (# or ## or ###)
            num_match = re.match(r'^(#+)\s+(.*)', line)
            if num_match:
                _flush_table()
                depth = len(num_match.group(1))
                numbered_counter += 1
                indent = "  " * depth
                text_widget.insert("end", f"{indent}{numbered_counter}. ", "numbered")
                self._render_inline_markup(text_widget, num_match.group(2))
                text_widget.insert("end", "\n")
                continue
            else:
                if numbered_counter:
                    numbered_counter = 0

            # Table row (|| for headers, | for cells) — accumulate for alignment
            if line.strip().startswith("||"):
                cells = [c.strip() for c in re.split(r'\|\|', line.strip()) if c.strip()]
                table_rows.append({"cells": cells, "tag": "table_header"})
                continue
            elif line.strip().startswith("|") and "|" in line.strip()[1:]:
                cells = [c.strip() for c in line.strip().split("|") if c.strip()]
                table_rows.append({"cells": cells, "tag": "table_cell"})
                continue
            else:
                _flush_table()

            # Regular line — apply inline formatting
            self._render_inline_markup(text_widget, line)
            text_widget.insert("end", "\n")

        # Flush any remaining table at end of content
        _flush_table()

    def _render_inline_markup(self, text_widget, line: str):
        """Render inline Jira markup (bold, italic, color, links, etc.) into text widget."""
        import re

        # Emoticons / special symbols
        emoticons = {
            "(/)": "✓", "(x)": "✗", "(i)": "ℹ", "(!)": "⚠",
            "(+)": "⊕", "(-)": "⊖", "(?)": "?", "(on)": "💡", "(off)": "○",
            "(*r)": "★", "(*g)": "★", "(*b)": "★", "(*y)": "★",
        }
        for token, symbol in emoticons.items():
            line = line.replace(token, symbol)

        # Forced line break \\
        line = line.replace("\\\\", "\n")

        # Escaped markup: \* \_ \- \+ → remove backslash
        line = re.sub(r'\\([*_\-+~^{}\[\]])', r'\1', line)

        # Pattern priority order matters — longer/more-specific patterns first
        patterns = [
            (r'\{color:(\w+)\}(.*?)\{color\}', 'color'),
            (r'\{\{(.*?)\}\}', 'monospace'),
            (r'\*_(.*?)_\*', 'bolditalic'),
            (r'_\*(.*?)\*_', 'bolditalic'),
            (r'\*([^*\n]+?)\*', 'bold'),
            (r'(?<!\w)_([^_\n]+?)_(?!\w)', 'italic'),
            (r'\+([^+\n]+?)\+', 'underline'),
            (r'(?<!\w)-([^\-\n]+?)-(?!\w)', 'strikethrough'),
            (r'\^([^^]+?)\^', 'superscript'),
            (r'~([^~]+?)~', 'subscript'),
            (r'\?\?([^?]+?)\?\?', 'citation'),
            (r'\[([^|\]\n]+)\|([^|\]\n]+)(?:\|[^\]\n]*)?\]', 'link_with_text'),
            (r'\[(https?://[^\]\n]+)\]', 'link'),
            (r'\[(mailto:[^\]\n]+)\]', 'link'),
            (r'!([\w./\-]+)(?:\|[^!]*)?\!', 'image'),
        ]

        segments = []  # (start, end, tag, display_text)

        for pattern, tag_type in patterns:
            for m in re.finditer(pattern, line):
                if tag_type == 'color':
                    color_name = m.group(1).lower()
                    known_colors = ("red", "green", "blue", "orange", "purple",
                                    "yellow", "cyan", "gray", "grey", "navy",
                                    "teal", "maroon", "white", "black")
                    if color_name in known_colors:
                        tag = f"color_{color_name}"
                    else:
                        tag = "bold"
                    segments.append((m.start(), m.end(), tag, m.group(2)))
                elif tag_type == 'link_with_text':
                    segments.append((m.start(), m.end(), "link", f"{m.group(1)} ↗"))
                elif tag_type == 'link':
                    segments.append((m.start(), m.end(), "link", f"{m.group(1)} ↗"))
                elif tag_type == 'image':
                    segments.append((m.start(), m.end(), "link", f"[img: {m.group(1)}]"))
                elif tag_type == 'citation':
                    segments.append((m.start(), m.end(), "italic", f"— {m.group(1)}"))
                elif tag_type == 'superscript':
                    segments.append((m.start(), m.end(), "bold", f"^{m.group(1)}"))
                elif tag_type == 'subscript':
                    segments.append((m.start(), m.end(), "italic", f"_{m.group(1)}"))
                else:
                    segments.append((m.start(), m.end(), tag_type, m.group(1)))

        if not segments:
            text_widget.insert("end", line)
            return

        # Sort by position, handle non-overlapping
        segments.sort(key=lambda s: s[0])
        pos = 0
        for start, end, tag, display in segments:
            if start < pos:
                continue  # skip overlapping
            if start > pos:
                text_widget.insert("end", line[pos:start])
            text_widget.insert("end", display, tag)
            pos = end
        if pos < len(line):
            text_widget.insert("end", line[pos:])

    def _show_epic_readonly_help(self):
        """Show a help popup explaining why Epic Description is read-only."""
        messagebox.showinfo(
            "Read-Only Field",
            "The Epic Description field is read-only.\n\n"
            "To modify the epic description, edit it directly\n"
            "in Jira on the epic issue page.\n\n"
            "This tool only creates/updates User Stories\n"
            "linked to the selected epic."
        )

    def _split_tab(self, idx):
        if idx >= len(self.tab_widgets):
            return
        w = self.tab_widgets[idx]
        if w is None:
            return
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
            story_points = w["story_points"].get().strip() if "story_points" in w else ""
            key = w.get("key", "")
            if title:
                stories.append({"title": title, "description": desc,
                                "acceptance_criteria": ac,
                                "sprint": sprint, "labels": labels,
                                "assignee_key": assignee_key,
                                "components": components, "priority": priority,
                                "story_points": story_points, "key": key})
        return stories

    def _validate_stories(self, stories: list[dict]) -> list[str]:
        """Validate stories before creation. Returns list of error messages."""
        errors = []
        unplanned_count = 0
        empty_desc_count = 0
        empty_ac_count = 0
        for i, s in enumerate(stories, 1):
            title = s["title"]
            if not title or title == "New Story":
                errors.append(f"Story #{i}: title is empty or placeholder ('New Story')")
            if len(title) > 255:
                errors.append(f"Story #{i}: title too long ({len(title)} chars, max 255)")
            sprint = s.get("sprint", "")
            if not sprint or sprint == UNPLANNED_SPRINT:
                unplanned_count += 1
            if not s.get("description", "").strip():
                empty_desc_count += 1
            if not s.get("acceptance_criteria", "").strip():
                empty_ac_count += 1
        if unplanned_count:
            errors.append(f"{unplanned_count} story/stories still have sprint '{UNPLANNED_SPRINT}' — assign a real sprint")
        if empty_desc_count:
            errors.append(f"{empty_desc_count} story/stories have empty Description")
        if empty_ac_count:
            errors.append(f"{empty_ac_count} story/stories have empty Acceptance Criteria")
        return errors

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

    def _show_scheduling(self):
        """Show sprint scheduling as a proper table: columns = sprints, rows = US IDs."""
        # Collect key and sprint from tabs
        sprint_map = {}  # sprint_name -> list of IDs
        unplanned = []
        for w in self.tab_widgets:
            if w is None:
                continue
            title = w["title"].get().strip()
            if not title:
                continue
            sprint = w["sprint"].get().strip()
            key = w.get("key", "")
            label = key if key else f"(new) {title[:30]}"
            if not sprint or sprint == UNPLANNED_SPRINT:
                unplanned.append(label)
            else:
                sprint_map.setdefault(sprint, []).append(label)

        if not sprint_map and not unplanned:
            messagebox.showwarning("No Stories", "No stories to schedule.")
            return

        # Get sprint details for dates
        sprint_details = {}
        if JIRA_AVAILABLE:
            import jira_client
            try:
                for sd in jira_client.get_board_sprints_details():
                    sprint_details[sd["name"]] = sd
            except Exception:
                pass

        # All columns (sprints used + unplanned if any)
        columns = list(sprint_map.keys())
        if unplanned:
            columns.append(UNPLANNED_SPRINT)
            sprint_map[UNPLANNED_SPRINT] = unplanned

        # Determine max rows needed
        max_rows = max(len(v) for v in sprint_map.values())

        col_width = max(18, max(len(c) for c in columns) + 2)
        win_width = min(1000, 20 + len(columns) * (col_width * 8 + 20))
        win_height = min(600, 120 + max_rows * 24)

        win = self._open_popup("scheduling", "📅 Sprint Scheduling",
                               f"{win_width}x{win_height}")
        win.resizable(True, True)

        def _fmt_date(d):
            return d[:10] if d and len(d) >= 10 else ""

        # Table frame with grid
        table = tk.Frame(win, bg=BG_DARK)
        table.pack(fill="both", expand=True, padx=10, pady=10)

        # Header row
        for col_idx, sprint_name in enumerate(columns):
            hdr_frame = tk.Frame(table, bg=BTN_PRIMARY, bd=1, relief="solid")
            hdr_frame.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
            fg = "white" if sprint_name != UNPLANNED_SPRINT else "#ffcc80"
            tk.Label(hdr_frame, text=sprint_name, font=("Segoe UI", 9, "bold"),
                     fg=fg, bg=BTN_PRIMARY, anchor="center").pack(padx=4, pady=(3, 0))
            # Dates sub-line
            sd = sprint_details.get(sprint_name, {})
            start = _fmt_date(sd.get("startDate", ""))
            end = _fmt_date(sd.get("endDate", ""))
            if start or end:
                tk.Label(hdr_frame, text=f"{start} → {end}", font=("Segoe UI", 7),
                         fg="#cccccc", bg=BTN_PRIMARY, anchor="center").pack(padx=4, pady=(0, 3))
            else:
                tk.Frame(hdr_frame, bg=BTN_PRIMARY, height=3).pack()
            table.columnconfigure(col_idx, weight=1)

        # Data rows
        for row_idx in range(max_rows):
            for col_idx, sprint_name in enumerate(columns):
                stories = sprint_map[sprint_name]
                bg = "#0a1a2e" if row_idx % 2 == 0 else "#0d2240"
                cell = tk.Frame(table, bg=bg, bd=1, relief="solid",
                                highlightbackground="#1a3a5c", highlightthickness=1)
                cell.grid(row=row_idx + 1, column=col_idx, sticky="nsew", padx=1, pady=0)
                if row_idx < len(stories):
                    fg = FG_TEXT if sprint_name != UNPLANNED_SPRINT else FG_WARN
                    tk.Label(cell, text=stories[row_idx], font=(MONO_FONT, 9),
                             fg=fg, bg=bg, anchor="center").pack(pady=2, padx=4)
                table.rowconfigure(row_idx + 1, weight=0)

    def _classify_stories(self, stories: list[dict]) -> list[dict]:
        """Classify each story as 'new', 'modified', or 'unchanged'.

        Compares current tab data against cached epic stories from Jira.
        """
        epic_key = self.selected_epic["key"] if self.selected_epic else ""
        cached = self._epic_stories_cache.get(epic_key, [])
        cached_map = {s["key"]: s for s in cached if s.get("key")}

        classified = []
        tab_idx = 0
        for i, s in enumerate(stories):
            # Find the matching tab_widget (skip None entries from removed tabs)
            while tab_idx < len(self.tab_widgets) and self.tab_widgets[tab_idx] is None:
                tab_idx += 1
            w = self.tab_widgets[tab_idx] if tab_idx < len(self.tab_widgets) else None
            tab_idx += 1

            if w is None:
                continue
            key = w.get("key", "")
            if not key or not w.get("existing", False):
                # No Jira key — brand new story
                classified.append({**s, "_status": "new", "_key": ""})
            elif key in cached_map:
                # Existing story — check if modified
                orig = cached_map[key]
                changed = False
                if s["title"].strip() != orig.get("summary", "").strip():
                    changed = True
                if s["description"].strip() != orig.get("description", "").strip():
                    changed = True
                if s.get("acceptance_criteria", "").strip() != orig.get("acceptance_criteria", "").strip():
                    changed = True
                if s.get("sprint", "").strip() != orig.get("sprint", "").strip():
                    changed = True
                s_labels = sorted(s.get("labels") or [])
                o_labels = sorted(orig.get("labels") or [])
                if s_labels != o_labels:
                    changed = True
                if (s.get("assignee_key") or "") != (orig.get("assignee_key") or ""):
                    changed = True
                if sorted(s.get("components") or []) != sorted(orig.get("components") or []):
                    changed = True
                if (s.get("priority") or "") != (orig.get("priority") or ""):
                    changed = True
                status = "modified" if changed else "unchanged"
                classified.append({**s, "_status": status, "_key": key})
            else:
                # Has a key but not in cache — treat as new
                classified.append({**s, "_status": "new", "_key": key})
        return classified

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

        # Validate stories before proceeding
        validation_errors = self._validate_stories(stories)
        if validation_errors:
            messagebox.showerror("Validation Error",
                                 "Fix the following before creating:\n\n" +
                                 "\n".join(validation_errors))
            return

        # Classify stories as new/modified/unchanged
        classified = self._classify_stories(stories)
        new_count = sum(1 for s in classified if s["_status"] == "new")
        mod_count = sum(1 for s in classified if s["_status"] == "modified")
        unch_count = sum(1 for s in classified if s["_status"] == "unchanged")

        if not new_count and not mod_count:
            messagebox.showinfo("No Changes",
                                "All stories are unchanged. Nothing to create or update.")
            return

        # --- First confirmation: review list with status icons ---
        confirmed = [False]
        win = self._open_popup("confirm_create", "Confirm Create/Update", "700x520")
        win.resizable(True, True)
        win.grab_set()

        # Header
        hdr = tk.Frame(win, bg=BG_PANEL)
        hdr.pack(fill="x", padx=10, pady=(10, 5))
        tk.Label(hdr, text="🚀 Create/Update User Stories",
                 font=("Segoe UI", 13, "bold"), fg=FG_TITLE, bg=BG_PANEL).pack(side="left")

        # Epic info
        tk.Label(win, text=f"Epic: [{self.selected_epic['key']}] {self.selected_epic.get('summary', '')}",
                 font=("Segoe UI", 9), fg="#aaaaaa", bg=BG_DARK, wraplength=660, justify="left"
                 ).pack(anchor="w", padx=10, pady=(0, 5))

        # Legend
        legend = tk.Frame(win, bg=BG_DARK)
        legend.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(legend, text="🆕 New", font=("Segoe UI", 9, "bold"),
                 fg="#66bb6a", bg=BG_DARK).pack(side="left", padx=(0, 12))
        tk.Label(legend, text="✏️ Modified", font=("Segoe UI", 9, "bold"),
                 fg="#ffb74d", bg=BG_DARK).pack(side="left", padx=(0, 12))
        tk.Label(legend, text="═ Unchanged", font=("Segoe UI", 9, "bold"),
                 fg="#888888", bg=BG_DARK).pack(side="left", padx=(0, 12))
        tk.Label(legend, text=f"({new_count} new, {mod_count} modified, {unch_count} unchanged)",
                 font=("Segoe UI", 8), fg="#aaaaaa", bg=BG_DARK).pack(side="right")

        # Stories list with columns
        list_frame = tk.Frame(win, bg=BG_DARK)
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        # Header row
        col_hdr = tk.Frame(list_frame, bg=BTN_PRIMARY)
        col_hdr.pack(fill="x")
        tk.Label(col_hdr, text="St", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, width=3).pack(side="left")
        tk.Label(col_hdr, text=" # ", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, width=3).pack(side="left")
        tk.Label(col_hdr, text=" Title", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, anchor="w").pack(side="left", fill="x", expand=True)
        tk.Label(col_hdr, text="Sprint ", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, width=18).pack(side="right")
        tk.Label(col_hdr, text="Assignee ", font=("Segoe UI", 8, "bold"),
                 fg="white", bg=BTN_PRIMARY, width=10).pack(side="right")

        # Scrollable list
        canvas = tk.Canvas(list_frame, bg=BG_DARK, highlightthickness=0, height=270)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=BG_DARK)
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw", width=660)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        status_icons = {"new": "🆕", "modified": "✏️", "unchanged": "═"}
        status_colors = {"new": "#66bb6a", "modified": "#ffb74d", "unchanged": "#888888"}

        for i, s in enumerate(classified, 1):
            st = s["_status"]
            row_bg = "#0a1a2e" if i % 2 == 0 else "#0d2240"
            row = tk.Frame(inner, bg=row_bg)
            row.pack(fill="x")
            tk.Label(row, text=status_icons[st], font=("Segoe UI", 9),
                     fg=status_colors[st], bg=row_bg, width=3).pack(side="left")
            tk.Label(row, text=f" {i:2d}", font=(MONO_FONT, 9),
                     fg=FG_ACCENT, bg=row_bg, width=3).pack(side="left")
            title_fg = status_colors[st] if st != "unchanged" else "#888888"
            tk.Label(row, text=f" {s['title'][:50]}{'…' if len(s['title'])>50 else ''}",
                     font=("Segoe UI", 9), fg=title_fg, bg=row_bg,
                     anchor="w").pack(side="left", fill="x", expand=True)
            sprint_txt = s.get("sprint", "—")[:18]
            tk.Label(row, text=sprint_txt, font=("Segoe UI", 8),
                     fg="#90caf9", bg=row_bg, width=18).pack(side="right")
            assign_txt = s.get("assignee_key", "—")[:10]
            tk.Label(row, text=assign_txt, font=("Segoe UI", 8),
                     fg="#b0bec5", bg=row_bg, width=10).pack(side="right")

        # Summary footer
        footer = tk.Frame(win, bg=BG_PANEL)
        footer.pack(fill="x", padx=10, pady=(5, 5))
        tk.Label(footer, text=f"📊 Total: {len(classified)} stories  |  "
                 f"🆕 {new_count} to create  |  ✏️ {mod_count} to update  |  "
                 f"═ {unch_count} unchanged (skipped)",
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

        self._make_btn(btn_frame, "✓ Proceed", BTN_SUCCESS, do_confirm).pack(side="left", padx=5)
        self._make_btn(btn_frame, "✗ Cancel", BTN_DANGER, do_cancel).pack(side="left", padx=5)

        win.wait_window()
        if not confirmed[0]:
            return

        # --- Second confirmation: "Are you sure?" ---
        sure = messagebox.askyesno(
            "Final Confirmation",
            f"Are you sure you want to apply changes to Jira?\n\n"
            f"  • {new_count} story/stories will be CREATED\n"
            f"  • {mod_count} story/stories will be UPDATED\n"
            f"  • {unch_count} unchanged (will be skipped)\n\n"
            f"This action cannot be undone.",
            icon="warning"
        )
        if not sure:
            self._set_status("Operation cancelled by user")
            return

        # --- Execute create/update ---
        epic_key = self.selected_epic["key"]
        created = []
        updated = []
        errors = []
        tag_gen = self.tag_generated_var.get()
        log.info(f"Creating/Updating stories for epic {epic_key} "
                 f"({new_count} new, {mod_count} modified, {unch_count} unchanged, "
                 f"tag_generated={tag_gen})")
        import jira_client
        for s in classified:
            st = s["_status"]
            if st == "unchanged":
                continue
            try:
                if st == "new":
                    key = jira_client.create_story(
                        epic_key, s["title"], s["description"],
                        s.get("sprint"), s.get("labels"),
                        s.get("assignee_key"), s.get("components"),
                        s.get("priority"), s.get("acceptance_criteria", ""),
                        tag_generated=tag_gen)
                    created.append(key)
                    log.info(f"  Created {key}: {s['title']}")
                elif st == "modified":
                    issue_key = s["_key"]
                    jira_client.update_story(
                        issue_key, s["title"], s["description"],
                        s.get("sprint", ""), s.get("labels"),
                        s.get("assignee_key", ""), s.get("components"),
                        s.get("priority", ""), s.get("acceptance_criteria", ""))
                    updated.append(issue_key)
                    log.info(f"  Updated {issue_key}: {s['title']}")
            except Exception as e:
                label = s.get("_key") or s["title"]
                errors.append(f"{label}: {e}")
                log.error(f"  Failed: {label}: {e}")

        msg = ""
        if created:
            msg += f"✓ Created: {', '.join(created)}\n"
        if updated:
            msg += f"✓ Updated: {', '.join(updated)}\n"
        if errors:
            msg += f"\n✗ Errors:\n" + "\n".join(errors)
        if not msg:
            msg = "No changes applied."
        messagebox.showinfo("Results", msg)
        self._set_status(f"Created {len(created)}, Updated {len(updated)} stories")

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
        """Restore full editing context from the previous session.

        Restores: epic selection, all story tabs with every field
        (title, description, AC, sprint, labels, assignee, components,
        priority, story_points, Jira key).
        If Jira is connected and stories are already loaded from the epic,
        the user is asked whether to restore saved edits or keep fresh data.
        """
        state = load_state()
        if not state:
            return
        log.debug(f"Restoring state: epic_key={state.get('epic_key')}, "
                  f"stories={len(state.get('stories', []))}")

        # Restore epic selection (override auto-select)
        epic_idx = state.get("epic_idx", -1)
        if epic_idx >= 0 and epic_idx < len(self.epics):
            self.epic_combo.selection_clear(0, "end")
            self.epic_combo.selection_set(epic_idx)
            self._on_epic_selected()

        # Restore stories in editing
        saved_stories = state.get("stories", [])
        if not saved_stories:
            return

        # Check if we should restore saved edits over fresh data
        if JIRA_AVAILABLE and self.tab_widgets:
            # Stories were loaded from Jira — ask user
            n_saved = len(saved_stories)
            msg = (
                f"Found {n_saved} unsaved story edits from the previous session.\n\n"
                f"Restore them? (replaces the current tabs loaded from Jira)"
            )
            if LANG == "it":
                msg = (
                    f"Trovate {n_saved} storie con modifiche non salvate dalla sessione precedente.\n\n"
                    f"Ripristinare? (sostituisce i tab correnti caricati da Jira)"
                )
            title = "Restore Session" if LANG == "en" else "Ripristino Sessione"
            try:
                if not self.root.winfo_exists():
                    return
                if not messagebox.askyesno(title, msg, parent=self.root):
                    log.info("User declined session restore — keeping fresh Jira data")
                    return
            except Exception as e:
                log.warning(f"Session restore dialog interrupted: {e}")
                return

        # Restore all story tabs with full context
        log.info(f"Restoring {len(saved_stories)} stories from previous session")
        self._clear_tabs()
        for s in saved_stories:
            self._add_tab(
                title=s.get("title", "New Story"),
                description=s.get("description", ""),
                sprint=s.get("sprint", ""),
                key=s.get("key", ""),
                existing=bool(s.get("key")),
                readonly=False,
                acceptance_criteria=s.get("acceptance_criteria", ""),
                labels=s.get("labels"),
                assignee_key=s.get("assignee_key", ""),
                components=s.get("components"),
                priority=s.get("priority", ""),
                story_points=s.get("story_points", ""),
            )
        # Select first tab
        if self.tab_widgets:
            self.notebook.select(0)
        self._set_status(f"✓ Session restored ({len(saved_stories)} stories)")

    def _show_history(self):
        """Show application version history / changelog."""
        win = self._open_popup("history", "Application History", "600x400")

        text = scrolledtext.ScrolledText(win, font=(MONO_FONT, 9),
                                          bg="#0a0a1a", fg=FG_TEXT, bd=0)
        text.pack(fill="both", expand=True, padx=10, pady=10)

        changelog = (
            "═══ v1.4.0 (2026-08-25) ═══\n"
            "  • Tag-as-generated: optional label + description footer on created stories\n"
            "\n"
            "═══ v1.3.0 (2026-07-27) ═══\n"
            "  • Create/Update confirmation popup with status icons (New/Modified/Unchanged)\n"
            "  • Double confirmation step before writing to Jira\n"
            "  • Epic Description field visually marked as read-only with help button\n"
            "  • Added update_story API to modify existing stories in Jira\n"
            "  • Button label changed to 'Create/Update User Stories'\n"
            "\n"
            "═══ v1.2.0 (2026-06-17) ═══\n"
            "  • Sprint default '— Unplanned —' for new stories\n"
            "  • Creation blocked if any story has unplanned sprint\n"
            "  • Validation: empty description or acceptance criteria blocks creation\n"
            "  • Validation errors show cause and count of affected stories\n"
            "  • Scheduling button: sprint/stories mapping table with dates\n"
            "\n"
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
        text.tag_config("header", foreground=FG_TITLE, font=(MONO_FONT, 9, "bold"))

        self._make_btn(win, S["close"], BTN_DANGER, win.destroy).pack(pady=5)

    def _set_status(self, msg: str):
        self.status_lbl.config(text=f"  {msg}")
        self.root.after(5000, lambda: self.status_lbl.config(
            text=f"  Mode: {'JIRA' if JIRA_AVAILABLE else 'DEMO'}  |  Ctrl+S: Save  |  Ctrl+Q: Quit"))

    def _on_close(self):
        """Handle application close — robust against stuck callbacks on Linux."""
        # Cancel any pending after() callbacks to avoid TclError on destroy
        if self._blink_id:
            try:
                self.root.after_cancel(self._blink_id)
            except Exception:
                pass
            self._blink_id = None

        try:
            if not self.root.winfo_exists():
                sys.exit(0)
            self._save()
            # Save window geometries to app_config.json
            save_app_config({
                "window_geometry": self.root.geometry(),
                "popup_geometries": POPUP_GEOMETRIES,
            })
        except Exception as e:
            log.warning(f"Error during close cleanup: {e}")

        log.info("Application closed")
        try:
            self.root.quit()  # exit mainloop first
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        sys.exit(0)

    def run(self):
        self.root.mainloop()


def main():
    # --- Pre-flight: check Jira reachability before building the full GUI ---
    # Uses a quick TCP probe (5s timeout) to avoid the minutes-long hang
    # caused by python-jira's default unlimited timeout + retries.
    if JIRA_URL:
        if not _check_jira_reachable(JIRA_URL, timeout=5.0):
            # Show a warning popup (lightweight Tk root, destroyed after choice)
            _pre_root = tk.Tk()
            _pre_root.withdraw()  # hide the empty root window
            msg = (
                f"⚠️  Cannot reach Jira server:\n"
                f"{JIRA_URL}\n\n"
                f"Possible causes:\n"
                f"  • VPN not connected\n"
                f"  • Server down or unreachable\n"
                f"  • Network issues\n\n"
                f"Continue in DEMO mode (offline)?\n"
                f"You can connect later via the credentials panel."
            )
            if LANG == "it":
                msg = (
                    f"⚠️  Impossibile raggiungere il server Jira:\n"
                    f"{JIRA_URL}\n\n"
                    f"Possibili cause:\n"
                    f"  • VPN non connessa\n"
                    f"  • Server non raggiungibile\n"
                    f"  • Problemi di rete\n\n"
                    f"Continuare in modalità DEMO (offline)?\n"
                    f"Potrai connetterti in seguito dal pannello credenziali."
                )
            title = "Jira Connection" if LANG == "en" else "Connessione Jira"
            proceed = messagebox.askokcancel(title, msg, icon="warning",
                                             parent=_pre_root)
            _pre_root.destroy()
            if not proceed:
                log.info("User chose to exit (Jira unreachable)")
                sys.exit(0)
            log.info("User chose DEMO mode (Jira unreachable)")

    app = SecurityHeartbeatApp()
    app.run()


if __name__ == "__main__":
    main()
