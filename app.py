#!/usr/bin/env python3
"""Security Heartbeat User Story Generator - GUI Application (tkinter)."""
import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from datetime import datetime

from config import load_state, save_state, load_history, VERSION, APP_TITLE, APP_DESC
from config import JIRA_URL, JIRA_TOKEN, TEAM_NAME
from i18n import get_strings
from translator import translate_to_english


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
        lbl = tk.Label(self.tip, text=self.text, font=("Segoe UI", 8),
                       bg="#333333", fg="#ffffff", padx=6, pady=3, wraplength=300)
        lbl.pack()

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
            # Test connection with a simple request
            client = jira_client.get_client()
            client.myself()
            JIRA_AVAILABLE = True
            return True
        except Exception as e:
            err = str(e)[:200]
            print(f"Jira init error: {err}")
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
        ToolTip(self.cred_token, "Jira Personal Access Token (Profile → Personal Access Tokens). No username needed.")

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
        self.status_lbl = tk.Label(bar, text=f"  Mode: {mode}  |  Ctrl+S: Save  |  Ctrl+Q: Quit",
                                    font=("Segoe UI", 8), fg="#888888", bg=BG_PANEL)
        self.status_lbl.pack(side="left", padx=5)
        self.status_right = tk.Label(bar, text=f"v{VERSION}",
                                      font=("Segoe UI", 8), fg="#888888", bg=BG_PANEL)
        self.status_right.pack(side="right", padx=5)

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

    # --- Data Loading ---

    def _load_sprints(self):
        """Load sprint names from the configured board."""
        if JIRA_AVAILABLE:
            try:
                import jira_client
                self.sprints = jira_client.get_board_sprints()
            except Exception:
                self.sprints = []
        else:
            self.sprints = []

    def _load_epics(self):
        global JIRA_AVAILABLE
        if JIRA_AVAILABLE:
            try:
                import jira_client
                self.epics = jira_client.get_open_epics()
            except Exception as e:
                self._set_status(f"Jira error: {e}")
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

    def _load_stories_for_epic(self):
        """Load stories from selected epic and populate checkboxes + tabs."""
        if not self.selected_epic:
            return
        stories = []
        from_template = False
        if JIRA_AVAILABLE:
            try:
                import jira_client
                stories = jira_client.get_epic_stories(self.selected_epic["key"])
            except Exception:
                pass
            if not stories:
                from_template = True
                try:
                    import jira_client
                    stories = jira_client.get_historical_stories()
                except Exception:
                    pass
        else:
            self._set_status("⚠ Jira not available — cannot load stories")

        # Update stories count
        self.stories_count_lbl.config(text=f"({len(stories)})")

        # Populate checkboxes with click-to-select-tab behavior
        for w in self.stories_inner.winfo_children():
            w.destroy()
        self.story_checkboxes = []

        for i, s in enumerate(stories):
            var = tk.BooleanVar(value=True)
            cb = tk.Checkbutton(self.stories_inner, text=f"[{s['key']}] {s['summary']}",
                                variable=var, bg=BG_PANEL, fg=FG_TEXT,
                                selectcolor=BG_CARD, activebackground=BG_PANEL,
                                activeforeground=FG_ACCENT, font=("Segoe UI", 8),
                                anchor="w", wraplength=320,
                                command=lambda idx=i: self._select_tab_by_index(idx))
            cb.pack(fill="x", anchor="w", pady=1)
            self.story_checkboxes.append((var, s))

        # Create tabs from stories
        is_resolved = self.selected_epic.get("resolution", "Unresolved").lower() != "unresolved"
        self._clear_tabs()
        for s in stories:
            if from_template:
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
                self._add_tab(s["summary"], s.get("description", ""),
                              key=s.get("key", ""), existing=True, readonly=is_resolved,
                              status=s.get("status", ""),
                              resolution=s.get("resolution", ""),
                              assignee=s.get("assignee", ""),
                              acceptance_criteria=s.get("acceptance_criteria", ""),
                              sprint=s.get("sprint", ""),
                              labels=s.get("labels"),
                              assignee_key=s.get("assignee_key", ""),
                              components=s.get("components"),
                              priority=s.get("priority", ""))

    def _select_tab_by_index(self, idx):
        """Select the notebook tab corresponding to the clicked story."""
        tabs = self.notebook.tabs()
        if idx < len(tabs):
            self.notebook.select(tabs[idx])

    def _load_from_epic(self):
        """Reload stories from the selected epic."""
        self._load_stories_for_epic()
        self._set_status("Stories loaded from epic")

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
        if labels is not None:
            default_labels = ",".join(labels)
        else:
            sprint_num = ""
            sprint_val = sprint or (sprint_combo.get() if not sprint else "")
            if sprint_val and TEAM_NAME and TEAM_NAME.lower() in sprint_val.lower():
                sprint_num = sprint_val.replace(TEAM_NAME, "").strip()
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

        win = tk.Toplevel(self.root)
        win.title("Translation Preview")
        win.geometry("600x350")
        win.configure(bg=BG_DARK)
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
        win = tk.Toplevel(self.root)
        win.title("Jira Markup Syntax")
        win.geometry("440x520")
        win.configure(bg=BG_DARK)
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
                full_desc = desc
                if ac:
                    full_desc += "\n\n*Acceptance Criteria:*\n" + ac
                stories.append({"title": title, "description": full_desc,
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

        # Confirmation dialog
        msg = S["confirm_dialog"].format(len(stories)) + "\n\n"
        for i, s in enumerate(stories, 1):
            msg += f"  {i}. {s['title']}\n"

        if not messagebox.askyesno("Confirm", msg):
            return

        if not self.selected_epic:
            messagebox.showerror("Error", "No epic selected!")
            return

        if not JIRA_AVAILABLE:
            messagebox.showerror("Error",
                                 "Jira not configured.\nEnter credentials and click Connect, or set environment variables.")
            return

        epic_key = self.selected_epic["key"]
        created = []
        errors = []
        import jira_client
        for s in stories:
            try:
                key = jira_client.create_story(epic_key, s["title"], s["description"],
                                               s.get("sprint"), s.get("labels"),
                                               s.get("assignee_key"), s.get("components"),
                                               s.get("priority"))
                created.append(key)
            except Exception as e:
                errors.append(f"{s['title']}: {e}")

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
        win = tk.Toplevel(self.root)
        win.title("Application History")
        win.geometry("600x400")
        win.configure(bg=BG_DARK)

        text = scrolledtext.ScrolledText(win, font=("Consolas", 9),
                                          bg="#0a0a1a", fg=FG_TEXT, bd=0)
        text.pack(fill="both", expand=True, padx=10, pady=10)

        changelog = (
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
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    app = SecurityHeartbeatApp()
    app.run()


if __name__ == "__main__":
    main()
