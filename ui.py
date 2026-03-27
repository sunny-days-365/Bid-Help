"""
ui.py  —  Green Japan Job Finder GUI
=====================================
Modern desktop UI built with tkinter (Python standard library — no extra install).
Run: python ui.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
import json
import webbrowser
from pathlib import Path

# .env ファイルを自動読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── Colour palette ────────────────────────────────────────────────────────────
BG        = "#0f1117"       # page background
SURFACE   = "#1a1d27"       # card / panel
BORDER    = "#2a2d3a"       # border lines
ACCENT    = "#00c896"       # green accent (Green Japan brand-ish)
ACCENT_DK = "#00a578"       # darker accent for hover
TEXT      = "#e8eaf0"       # primary text
SUBTEXT   = "#8b8fa8"       # secondary text
ERROR     = "#ff5c5c"       # error / warning
TAG_BG    = "#1e3a2f"       # keyword tag background
LINK      = "#5bb8ff"       # hyperlink


class GreenJobFinderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Green Japan Job Finder")
        self.geometry("1000x760")
        self.minsize(820, 600)
        self.configure(bg=BG)

        # ── State ─────────────────────────────────────────────────────────────
        self.resume_path   = tk.StringVar()
        self.situation_var = tk.StringVar()
        self.hope_var      = tk.StringVar()
        self.pages_var      = tk.IntVar(value=3)
        self.top_var        = tk.IntVar(value=20)
        self.github_token_var = tk.StringVar(value=os.environ.get("GITHUB_TOKEN", ""))
        self.api_key_var    = tk.StringVar(value=os.environ.get("OPENAI_API_KEY", ""))
        self.keywords_var   = tk.StringVar()
        self.results: list[dict] = []

        self._build_styles()
        self._build_layout()

    # ── Styles ────────────────────────────────────────────────────────────────
    def _build_styles(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("TFrame",       background=BG)
        style.configure("Card.TFrame",  background=SURFACE)
        style.configure("TLabel",       background=BG,      foreground=TEXT,    font=("Segoe UI", 10))
        style.configure("Card.TLabel",  background=SURFACE, foreground=TEXT,    font=("Segoe UI", 10))
        style.configure("Sub.TLabel",   background=SURFACE, foreground=SUBTEXT, font=("Segoe UI", 9))
        style.configure("Title.TLabel", background=BG,      foreground=ACCENT,  font=("Segoe UI", 18, "bold"))
        style.configure("H2.TLabel",    background=SURFACE, foreground=TEXT,    font=("Segoe UI", 11, "bold"))
        style.configure("Error.TLabel", background=SURFACE, foreground=ERROR,   font=("Segoe UI", 9))

        style.configure("TEntry",
            fieldbackground=BG, background=BG,
            foreground=TEXT, insertcolor=TEXT,
            bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER,
            relief="flat", padding=6,
        )
        style.map("TEntry", bordercolor=[("focus", ACCENT)])

        style.configure("Accent.TButton",
            background=ACCENT, foreground="#000000",
            font=("Segoe UI", 11, "bold"),
            relief="flat", padding=(16, 8),
            borderwidth=0,
        )
        style.map("Accent.TButton",
            background=[("active", ACCENT_DK)],
            relief=[("active", "flat")],
        )
        style.configure("Ghost.TButton",
            background=SURFACE, foreground=SUBTEXT,
            font=("Segoe UI", 9),
            relief="flat", padding=(8, 4),
            borderwidth=1,
        )
        style.map("Ghost.TButton",
            foreground=[("active", TEXT)],
            background=[("active", BORDER)],
        )

        style.configure("TScale", background=SURFACE, troughcolor=BORDER, sliderlength=16)
        style.configure("TProgressbar",
            troughcolor=BORDER, background=ACCENT,
            thickness=4,
        )
        style.configure("TScrollbar",
            background=SURFACE, troughcolor=BG,
            arrowcolor=SUBTEXT, bordercolor=BG,
        )

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_layout(self):
        # ── Header ────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG, pady=12)
        header.pack(fill="x", padx=24)

        tk.Label(header, text="🌿 Green Japan Job Finder",
                 bg=BG, fg=ACCENT, font=("Segoe UI", 20, "bold")).pack(side="left")
        tk.Label(header, text="powered by green-japan.com",
                 bg=BG, fg=SUBTEXT, font=("Segoe UI", 9)).pack(side="left", padx=(10, 0), pady=(8, 0))

        divider = tk.Frame(self, bg=BORDER, height=1)
        divider.pack(fill="x", padx=24)

        # ── Main two-column area ───────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True, padx=24, pady=(16, 0))
        body.columnconfigure(0, weight=0, minsize=340)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self._build_left_panel(body)
        self._build_right_panel(body)

        # ── Footer / progress ─────────────────────────────────────────────────
        self._build_footer()

    def _card(self, parent, title=None, **pack_kw):
        """Create a rounded surface card frame."""
        outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        outer.pack(**pack_kw)
        inner = tk.Frame(outer, bg=SURFACE, padx=16, pady=14)
        inner.pack(fill="both", expand=True)
        if title:
            tk.Label(inner, text=title, bg=SURFACE, fg=SUBTEXT,
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 8))
        return inner

    def _field(self, parent, label: str, var, placeholder="", show=None):
        """Label + Entry with placeholder support."""
        row = tk.Frame(parent, bg=SURFACE)
        row.pack(fill="x", pady=(0, 10))
        tk.Label(row, text=label, bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        entry = tk.Entry(
            row, textvariable=var,
            bg="#12151f", fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 10),
            highlightthickness=1, highlightcolor=ACCENT,
            highlightbackground=BORDER,
            show=show or "",
        )
        entry.pack(fill="x", ipady=6, pady=(3, 0))
        if placeholder and not var.get():
            self._add_placeholder(entry, var, placeholder)
        return entry

    def _add_placeholder(self, entry, var, text):
        entry.insert(0, text)
        entry.config(fg=SUBTEXT)
        def on_focus_in(e):
            if entry.get() == text:
                entry.delete(0, "end")
                entry.config(fg=TEXT)
        def on_focus_out(e):
            if not entry.get():
                entry.insert(0, text)
                entry.config(fg=SUBTEXT)
        entry.bind("<FocusIn>",  on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)

    # ── Left panel: inputs ────────────────────────────────────────────────────
    def _build_left_panel(self, parent):
        left = tk.Frame(parent, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.rowconfigure(99, weight=1)

        # ── Resume card ───────────────────────────────────────────────────────
        resume_card = self._card(left, title="📄 RESUME FILE", fill="x", pady=(0, 12))

        path_row = tk.Frame(resume_card, bg=SURFACE)
        path_row.pack(fill="x")
        self.resume_entry = tk.Entry(
            path_row, textvariable=self.resume_path,
            bg="#12151f", fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 9),
            highlightthickness=1, highlightcolor=ACCENT,
            highlightbackground=BORDER,
        )
        self.resume_entry.pack(side="left", fill="x", expand=True, ipady=5)
        tk.Button(
            path_row, text="Browse",
            bg=BORDER, fg=TEXT, font=("Segoe UI", 9),
            activebackground=ACCENT, activeforeground="#000",
            relief="flat", padx=10, cursor="hand2",
            command=self._browse_resume,
        ).pack(side="left", padx=(6, 0))

        self.resume_info = tk.Label(resume_card, text="", bg=SURFACE, fg=SUBTEXT,
                                    font=("Segoe UI", 8))
        self.resume_info.pack(anchor="w", pady=(4, 0))

        # ── Profile card ──────────────────────────────────────────────────────
        profile_card = self._card(left, title="💬 YOUR PROFILE", fill="x", pady=(0, 12))

        tk.Label(profile_card, text="Current Situation", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.situation_text = tk.Text(
            profile_card, height=4, wrap="word",
            bg="#12151f", fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 10),
            highlightthickness=1, highlightcolor=ACCENT,
            highlightbackground=BORDER,
            padx=6, pady=6,
        )
        self.situation_text.insert("1.0", "e.g. 5 years Python backend engineer, currently job hunting")
        self.situation_text.config(fg=SUBTEXT)
        self.situation_text.pack(fill="x", pady=(3, 10))
        self._text_placeholder(self.situation_text, "e.g. 5 years Python backend engineer, currently job hunting")

        tk.Label(profile_card, text="Job Hope / Ideal Job", bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        self.hope_text = tk.Text(
            profile_card, height=4, wrap="word",
            bg="#12151f", fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 10),
            highlightthickness=1, highlightcolor=ACCENT,
            highlightbackground=BORDER,
            padx=6, pady=6,
        )
        self.hope_text.pack(fill="x", pady=(3, 0))
        self._text_placeholder(self.hope_text, "e.g. Remote Python/Go job in Tokyo, 700万円+, startup preferred")

        # ── Options card ──────────────────────────────────────────────────────
        opt_card = self._card(left, title="⚙️  OPTIONS", fill="x", pady=(0, 12))

        row1 = tk.Frame(opt_card, bg=SURFACE)
        row1.pack(fill="x", pady=(0, 8))
        self._spinbox_row(row1, "Pages per keyword:", self.pages_var, 1, 10, side="left")
        self._spinbox_row(row1, "Top results:", self.top_var, 5, 50, side="right")

        tk.Label(opt_card, text="Manual Keywords (comma-separated, optional)",
                 bg=SURFACE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        kw_entry = tk.Entry(
            opt_card, textvariable=self.keywords_var,
            bg="#12151f", fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 10),
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER,
        )
        kw_entry.pack(fill="x", ipady=5, pady=(3, 10))
        self._add_placeholder(kw_entry, self.keywords_var, "Python, バックエンド, リモート  ← leave blank for AI")

        # ── AI backend selector ───────────────────────────────────────────────
        ai_frame = tk.Frame(opt_card, bg=SURFACE)
        ai_frame.pack(fill="x", pady=(0, 0))

        # GitHub Token (優先)
        gh_row = tk.Frame(ai_frame, bg=SURFACE)
        gh_row.pack(fill="x", pady=(0, 6))
        gh_label_row = tk.Frame(gh_row, bg=SURFACE)
        gh_label_row.pack(fill="x")
        tk.Label(gh_label_row,
                 text="GitHub Token  ",
                 bg=SURFACE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(gh_label_row,
                 text="✨ GitHub Copilot ユーザーはこちら (ghp_... / github_pat_...)",
                 bg=SURFACE, fg=ACCENT, font=("Segoe UI", 8)).pack(side="left")
        tk.Entry(
            gh_row, textvariable=self.github_token_var,
            bg="#12151f", fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 10),
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER,
            show="•",
        ).pack(fill="x", ipady=5, pady=(3, 0))

        # OpenAI API Key (フォールバック)
        oai_row = tk.Frame(ai_frame, bg=SURFACE)
        oai_row.pack(fill="x")
        tk.Label(oai_row,
                 text="OpenAI API Key  ",
                 bg=SURFACE, fg=TEXT, font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Entry(
            oai_row, textvariable=self.api_key_var,
            bg="#12151f", fg=TEXT, insertbackground=TEXT,
            relief="flat", font=("Segoe UI", 10),
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER,
            show="•",
        ).pack(fill="x", ipady=5, pady=(3, 0))

        # バックエンド状態インジケーター
        self.ai_status_label = tk.Label(
            opt_card, text="", bg=SURFACE, fg=SUBTEXT, font=("Segoe UI", 8)
        )
        self.ai_status_label.pack(anchor="w", pady=(4, 0))
        self._update_ai_status()
        self.github_token_var.trace_add("write", lambda *_: self._update_ai_status())
        self.api_key_var.trace_add("write",      lambda *_: self._update_ai_status())

        # ── Run button ────────────────────────────────────────────────────────
        self.run_btn = tk.Button(
            left, text="🔍  Find Jobs",
            bg=ACCENT, fg="#000000", font=("Segoe UI", 12, "bold"),
            activebackground=ACCENT_DK, activeforeground="#000",
            relief="flat", padx=20, pady=10,
            cursor="hand2",
            command=self._run,
        )
        self.run_btn.pack(fill="x", pady=(0, 4))

        self.stop_btn = tk.Button(
            left, text="■  Stop",
            bg=BORDER, fg=SUBTEXT, font=("Segoe UI", 9),
            activebackground=ERROR, activeforeground="#fff",
            relief="flat", padx=10, pady=6,
            cursor="hand2",
            command=self._stop,
            state="disabled",
        )
        self.stop_btn.pack(fill="x")

    def _spinbox_row(self, parent, label, var, from_, to, side):
        frame = tk.Frame(parent, bg=SURFACE)
        frame.pack(side=side, fill="x", expand=True, padx=(0, 8) if side == "left" else 0)
        tk.Label(frame, text=label, bg=SURFACE, fg=TEXT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Spinbox(
            frame, from_=from_, to=to, textvariable=var, width=5,
            bg="#12151f", fg=TEXT, insertbackground=TEXT,
            buttonbackground=BORDER, relief="flat",
            font=("Segoe UI", 10),
            highlightthickness=1, highlightcolor=ACCENT, highlightbackground=BORDER,
        ).pack(anchor="w", pady=(3, 0))

    def _text_placeholder(self, widget: tk.Text, placeholder: str):
        widget.config(fg=SUBTEXT)
        def on_focus_in(e):
            if widget.get("1.0", "end-1c") == placeholder:
                widget.delete("1.0", "end")
                widget.config(fg=TEXT)
        def on_focus_out(e):
            if not widget.get("1.0", "end-1c").strip():
                widget.insert("1.0", placeholder)
                widget.config(fg=SUBTEXT)
        widget.bind("<FocusIn>",  on_focus_in)
        widget.bind("<FocusOut>", on_focus_out)

    # ── Right panel: results ──────────────────────────────────────────────────
    def _build_right_panel(self, parent):
        right = tk.Frame(parent, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        # Results header row
        hdr = tk.Frame(right, bg=BG)
        hdr.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.result_label = tk.Label(
            hdr, text="Results will appear here",
            bg=BG, fg=SUBTEXT, font=("Segoe UI", 11, "bold"),
        )
        self.result_label.pack(side="left")

        btn_row = tk.Frame(hdr, bg=BG)
        btn_row.pack(side="right")
        tk.Button(btn_row, text="💾 Save TXT",
                  bg=BORDER, fg=TEXT, font=("Segoe UI", 9),
                  activebackground=ACCENT, activeforeground="#000",
                  relief="flat", padx=8, pady=4, cursor="hand2",
                  command=self._save_txt).pack(side="left", padx=(0, 6))
        tk.Button(btn_row, text="📦 Save JSON",
                  bg=BORDER, fg=TEXT, font=("Segoe UI", 9),
                  activebackground=ACCENT, activeforeground="#000",
                  relief="flat", padx=8, pady=4, cursor="hand2",
                  command=self._save_json).pack(side="left")

        # Results list (scrollable)
        list_outer = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        list_outer.grid(row=1, column=0, sticky="nsew")
        list_outer.rowconfigure(0, weight=1)
        list_outer.columnconfigure(0, weight=1)

        canvas = tk.Canvas(list_outer, bg=SURFACE, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(list_outer, orient="vertical", command=canvas.yview,
                                  bg=SURFACE, troughcolor=BG)
        self.results_frame = tk.Frame(canvas, bg=SURFACE)
        self.results_frame.bind("<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        list_outer.rowconfigure(0, weight=1)
        list_outer.columnconfigure(0, weight=1)

        self.canvas = canvas
        # Mouse-wheel scroll
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(-int(e.delta/120), "units"))

        # Log / console area
        log_card = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        log_card.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        log_inner = tk.Frame(log_card, bg=SURFACE)
        log_inner.pack(fill="both", expand=True)
        tk.Label(log_inner, text="Console", bg=SURFACE, fg=SUBTEXT,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=8, pady=(4, 0))
        self.log_box = scrolledtext.ScrolledText(
            log_inner, height=7, bg="#0a0c14", fg=SUBTEXT,
            font=("Consolas", 8), relief="flat",
            insertbackground=TEXT,
            state="disabled",
        )
        self.log_box.pack(fill="both", expand=True, padx=4, pady=(0, 4))

    def _build_footer(self):
        footer = tk.Frame(self, bg=BG, pady=8)
        footer.pack(fill="x", padx=24)

        self.progress = ttk.Progressbar(footer, mode="indeterminate",
                                         style="TProgressbar", length=200)
        self.progress.pack(side="left")
        self.status_label = tk.Label(footer, text="Ready",
                                      bg=BG, fg=SUBTEXT, font=("Segoe UI", 9))
        self.status_label.pack(side="left", padx=(10, 0))

        tk.Label(footer, text="green-japan.com",
                 bg=BG, fg=SUBTEXT, font=("Segoe UI", 8)).pack(side="right")

    # ── Actions ───────────────────────────────────────────────────────────────
    def _browse_resume(self):
        path = filedialog.askopenfilename(
            title="Select Resume",
            filetypes=[("Supported files", "*.docx *.txt *.md"),
                       ("Word Document", "*.docx"),
                       ("Text File", "*.txt *.md"),
                       ("All Files", "*.*")],
        )
        if path:
            self.resume_path.set(path)
            size = Path(path).stat().st_size
            self.resume_info.config(
                text=f"  {Path(path).name}  ·  {size//1024} KB",
                fg=ACCENT,
            )

    def _get_text_value(self, widget: tk.Text, placeholder: str) -> str:
        val = widget.get("1.0", "end-1c").strip()
        return "" if val == placeholder else val

    def _validate(self) -> bool:
        if not self.resume_path.get() or not Path(self.resume_path.get()).exists():
            messagebox.showerror("Missing Resume", "Please select a valid resume file.")
            return False
        situation = self._get_text_value(
            self.situation_text,
            "e.g. 5 years Python backend engineer, currently job hunting")
        hope = self._get_text_value(
            self.hope_text,
            "e.g. Remote Python/Go job in Tokyo, 700万円+, startup preferred")
        if not situation or not hope:
            messagebox.showerror("Missing Input",
                "Please fill in both 'Current Situation' and 'Job Hope'.")
            return False
        return True

    def _run(self):
        if not self._validate():
            return

        self._stop_flag = False
        self.run_btn.config(state="disabled", bg=BORDER, fg=SUBTEXT)
        self.stop_btn.config(state="normal")
        self.progress.start(12)
        self._set_status("Starting…")
        self._clear_results()
        self.results = []

        api_key = self.api_key_var.get().strip()
        if api_key:
            os.environ["OPENAI_API_KEY"] = api_key

        github_token = self.github_token_var.get().strip()
        if github_token:
            os.environ["GITHUB_TOKEN"] = github_token

        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()

    def _stop(self):
        self._stop_flag = True
        self._log("⚠ Stop requested…")

    def _worker(self):
        try:
            from resume_parser import build_profile
            from keyword_extractor import extract_keywords_with_ai
            from green_scraper import scrape_green
            from job_ranker import rank_jobs_with_ai

            situation = self._get_text_value(
                self.situation_text,
                "e.g. 5 years Python backend engineer, currently job hunting")
            hope = self._get_text_value(
                self.hope_text,
                "e.g. Remote Python/Go job in Tokyo, 700万円+, startup preferred")

            self._set_status("Parsing resume…")
            self._log("📋 Parsing resume…")
            profile = build_profile(self.resume_path.get(), situation, hope)
            self._log(f"   Resume: {len(profile['resume_text'])} characters")

            if getattr(self, "_stop_flag", False):
                return self._finish_stop()

            # Keywords
            manual_kw = self.keywords_var.get().strip()
            placeholder = "Python, バックエンド, リモート  ← leave blank for AI"
            if manual_kw and manual_kw != placeholder:
                keywords = [k.strip() for k in manual_kw.split(",") if k.strip()]
                self._log(f"🔑 Using manual keywords: {keywords}")
            else:
                self._set_status("Extracting keywords…")
                self._log("🤖 Extracting keywords from profile…")
                keywords = extract_keywords_with_ai(profile)
                self._log(f"🔑 Keywords: {keywords}")

            if getattr(self, "_stop_flag", False):
                return self._finish_stop()

            # Show keyword tags in UI
            self.after(0, self._show_keyword_tags, keywords)

            # Scrape
            self._set_status(f"Scraping Green Japan…")
            self._log(f"🌐 Scraping {len(keywords)} keyword(s), {self.pages_var.get()} page(s) each…")

            jobs = scrape_green(keywords, max_pages=self.pages_var.get())
            self._log(f"✅ Found {len(jobs)} unique job listings")

            if getattr(self, "_stop_flag", False):
                return self._finish_stop()

            if not jobs:
                self._log("⚠ No jobs found. Try different keywords.")
                self._set_status("No jobs found")
                return

            # Rank
            self._set_status("Ranking results…")
            self._log("🏆 Ranking by relevance…")
            ranked = rank_jobs_with_ai(jobs, profile, top_n=self.top_var.get())
            self.results = ranked
            self._log(f"✅ Top {len(ranked)} jobs selected")

            # Render results
            self.after(0, self._render_results, ranked)
            self._set_status(f"Done — {len(ranked)} jobs found")

        except Exception as e:
            import traceback
            self._log(f"❌ Error: {e}\n{traceback.format_exc()}")
            self._set_status("Error occurred")
        finally:
            self.after(0, self._finish)

    def _finish(self):
        self.progress.stop()
        self.run_btn.config(state="normal", bg=ACCENT, fg="#000000")
        self.stop_btn.config(state="disabled")

    def _finish_stop(self):
        self._log("⏹ Stopped.")
        self._set_status("Stopped")
        self.after(0, self._finish)

    # ── Results rendering ─────────────────────────────────────────────────────
    def _clear_results(self):
        for w in self.results_frame.winfo_children():
            w.destroy()
        self.result_label.config(text="Searching…", fg=SUBTEXT)

    def _show_keyword_tags(self, keywords: list[str]):
        """Show keyword chips below the result label area."""
        pass  # Tags are shown in the log; can extend here if desired

    def _render_results(self, ranked: list[dict]):
        self._clear_results()
        self.result_label.config(text=f"Top {len(ranked)} Matching Jobs", fg=ACCENT)

        for i, job in enumerate(ranked):
            self._job_card(self.results_frame, i + 1, job)

        # Scroll to top
        self.canvas.yview_moveto(0)

    def _job_card(self, parent, rank: int, job: dict):
        # Outer card with border
        card_outer = tk.Frame(parent, bg=BORDER, padx=1, pady=1)
        card_outer.pack(fill="x", padx=10, pady=(6, 0))
        card = tk.Frame(card_outer, bg=SURFACE, padx=14, pady=10)
        card.pack(fill="both", expand=True)
        card.columnconfigure(1, weight=1)

        # Rank badge
        badge = tk.Label(card, text=f" {rank:>2} ",
                         bg=ACCENT if rank <= 3 else BORDER,
                         fg="#000" if rank <= 3 else TEXT,
                         font=("Segoe UI", 10, "bold"))
        badge.grid(row=0, column=0, rowspan=2, padx=(0, 12), sticky="n")

        # Title
        title = job.get("title", "(no title)")[:100]
        title_lbl = tk.Label(card, text=title, bg=SURFACE, fg=TEXT,
                              font=("Segoe UI", 10, "bold"),
                              wraplength=480, anchor="w", justify="left")
        title_lbl.grid(row=0, column=1, sticky="ew")

        # URL (clickable)
        url = job.get("url", "")
        url_lbl = tk.Label(card, text=url, bg=SURFACE, fg=LINK,
                            font=("Segoe UI", 8), cursor="hand2",
                            anchor="w")
        url_lbl.grid(row=1, column=1, sticky="ew")
        url_lbl.bind("<Button-1>", lambda e, u=url: webbrowser.open(u))
        url_lbl.bind("<Enter>", lambda e, w=url_lbl: w.config(fg=ACCENT))
        url_lbl.bind("<Leave>", lambda e, w=url_lbl: w.config(fg=LINK))

        # Meta row: keyword tag + reason
        meta = tk.Frame(card, bg=SURFACE)
        meta.grid(row=2, column=1, sticky="ew", pady=(4, 0))

        kw = job.get("keyword", "")
        if kw:
            tk.Label(meta, text=f" {kw} ", bg=TAG_BG, fg=ACCENT,
                     font=("Segoe UI", 8), padx=4).pack(side="left", padx=(0, 8))

        reason = job.get("reason", "")
        if reason:
            tk.Label(meta, text=reason, bg=SURFACE, fg=SUBTEXT,
                     font=("Segoe UI", 8), wraplength=400,
                     anchor="w", justify="left").pack(side="left")

        # Hover highlight
        def on_enter(e, c=card, o=card_outer):
            c.config(bg="#202435")
            o.config(bg=ACCENT)
            for ch in c.winfo_children():
                try:
                    ch.config(bg="#202435")
                except Exception:
                    pass
        def on_leave(e, c=card, o=card_outer):
            c.config(bg=SURFACE)
            o.config(bg=BORDER)
            for ch in c.winfo_children():
                try:
                    ch.config(bg=SURFACE)
                except Exception:
                    pass
        for widget in [card, title_lbl, url_lbl, meta]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

    # ── AI status indicator ───────────────────────────────────────────────────
    def _update_ai_status(self):
        gh  = self.github_token_var.get().strip()
        oai = self.api_key_var.get().strip()
        if gh:
            text  = "✅ GitHub Models (gpt-4o) — GitHub Copilot で利用可能"
            color = ACCENT
        elif oai:
            text  = "✅ OpenAI API (gpt-4o)"
            color = ACCENT
        else:
            text  = "⚠ AI キー未設定 — パターンマッチングを使用"
            color = SUBTEXT
        if hasattr(self, "ai_status_label"):
            self.ai_status_label.config(text=text, fg=color)

    # ── Logging ───────────────────────────────────────────────────────────────
    def _log(self, msg: str):
        def _append():
            self.log_box.config(state="normal")
            self.log_box.insert("end", msg + "\n")
            self.log_box.see("end")
            self.log_box.config(state="disabled")
        self.after(0, _append)

    def _set_status(self, msg: str):
        self.after(0, lambda: self.status_label.config(text=msg))

    # ── Save ──────────────────────────────────────────────────────────────────
    def _save_txt(self):
        if not self.results:
            messagebox.showinfo("No Results", "Run a search first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text File", "*.txt")],
            initialfile="results.txt",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"Top {len(self.results)} Matching Jobs — Green Japan\n")
            f.write("=" * 60 + "\n\n")
            for i, job in enumerate(self.results, 1):
                f.write(f"{i}. {job.get('title','')}\n")
                f.write(f"   {job.get('url','')}\n")
                if job.get("reason"):
                    f.write(f"   {job['reason']}\n")
                f.write("\n")
        messagebox.showinfo("Saved", f"Results saved to:\n{path}")

    def _save_json(self):
        if not self.results:
            messagebox.showinfo("No Results", "Run a search first.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON File", "*.json")],
            initialfile="results.json",
        )
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        messagebox.showinfo("Saved", f"JSON saved to:\n{path}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = GreenJobFinderApp()
    app.mainloop()
