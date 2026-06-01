import os
import json
from datetime import datetime
from tkinter import colorchooser, filedialog, messagebox
import customtkinter as ctk
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer,
    GappedSquareModuleDrawer,
)
from PIL import Image

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS
HISTORY_FILE = "history.json"
HISTORY_DIR = "history_images"
os.makedirs(HISTORY_DIR, exist_ok=True)

BG       = "#f8f9ff"  # background
CARD_BG  = "#ffffff"  # surface-container-lowest
BORDER   = "#c3c6d7"  # outline-variant
BLUE     = "#004ac6"  # primary
BLUE_DK  = "#003ea8"  # on-primary-fixed-variant (for hover)
BLUE_LT  = "#eff4ff"  # surface-container-low
TEXT_DK  = "#0b1c30"  # on-surface
TEXT_MD  = "#434655"  # on-surface-variant
TEXT_LT  = "#737686"  # outline


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


# ─── Custom Pill Segmented Button ───────────────────────────────────────────
class PillSegButton(ctk.CTkFrame):
    def __init__(self, master, values, command=None, height=44, **kwargs):
        super().__init__(master, fg_color="#eff4ff", bg_color="transparent",
                         corner_radius=12, border_width=1, border_color="#e5eeff", **kwargs)
        self.command = command
        self.buttons = {}
        self._value = ctk.StringVar(value=values[0])
        for i, v in enumerate(values):
            self.grid_columnconfigure(i, weight=1)
        self.grid_rowconfigure(0, weight=1)
        for i, v in enumerate(values):
            b = ctk.CTkButton(
                self, text=v, height=height - 8,
                fg_color="transparent", text_color=TEXT_MD,
                hover_color="#dce9ff", corner_radius=8,
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda val=v: self.set(val)
            )
            b.grid(row=0, column=i, padx=4, pady=4, sticky="ew")
            self.buttons[v] = b
        self._refresh(values[0])

    def set(self, value):
        self._value.set(value)
        self._refresh(value)
        if self.command:
            self.command(value)

    def get(self):
        return self._value.get()

    def _refresh(self, selected):
        for v, b in self.buttons.items():
            if v == selected:
                b.configure(fg_color=BLUE, text_color="#ffffff",
                             hover_color=BLUE_DK)
            else:
                b.configure(fg_color="transparent", text_color=TEXT_MD,
                             hover_color="#dce9ff")


# ─── Accordion Card ──────────────────────────────────────────────────────────
class AccordionCard(ctk.CTkFrame):
    """Collapsible card with icon + title + chevron."""
    def __init__(self, master, title, icon="🎨", expanded=False, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12,
                         border_width=1, border_color=BORDER, **kwargs)
        self._expanded = expanded

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        header.grid_columnconfigure(1, weight=1)

        self.icon_lbl = ctk.CTkLabel(header, text=icon,
                                     text_color=BLUE, font=ctk.CTkFont(size=20))
        self.icon_lbl.grid(row=0, column=0, padx=(0, 12))

        self.title_lbl = ctk.CTkLabel(header, text=title,
                                      text_color=TEXT_DK,
                                      font=ctk.CTkFont(size=16, weight="bold"),
                                      anchor="w")
        self.title_lbl.grid(row=0, column=1, sticky="ew")

        self.chevron = ctk.CTkLabel(header, text="∨",
                                    text_color=TEXT_LT,
                                    font=ctk.CTkFont(size=14))
        self.chevron.grid(row=0, column=2)

        # Content frame
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        if expanded:
            self.content.pack(fill="x", padx=4, pady=(0, 4))

        # Bind click
        for w in (header, self.icon_lbl, self.title_lbl, self.chevron):
            w.bind("<Button-1>", self._toggle)

    def _toggle(self, _=None):
        self._expanded = not self._expanded
        if self._expanded:
            self.content.pack(fill="x", padx=4, pady=(0, 4))
        else:
            self.content.pack_forget()


# ─── Main App ────────────────────────────────────────────────────────────────
class QRGeneratorPro(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("QR Generator Pro")
        self.geometry("1020x700")
        self.minsize(880, 600)
        self.configure(fg_color=BG)

        self.qr_fg     = "#000000"
        self.qr_bg     = "#FFFFFF"
        self.logo_path = None
        self.qr_img    = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._build_topbar()
        self._build_body()
        self._show_page("create")
        self.after(200, self._generate_qr)

    # ── Top Navigation Bar ───────────────────────────────────────────────────
    def _build_topbar(self):
        bar = ctk.CTkFrame(self, fg_color=CARD_BG,
                           corner_radius=0, border_width=1,
                           border_color=BORDER, height=56)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_columnconfigure(1, weight=1)
        bar.grid_propagate(False)
        # Only show bottom border using a separator line
        sep = ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0)
        sep.grid(row=0, column=0, sticky="ews")

        # Logo
        ctk.CTkLabel(bar, text="QR Pro",
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=BLUE).grid(row=0, column=0, padx=28, pady=14, sticky="w")

        # Nav buttons (right side)
        nav = ctk.CTkFrame(bar, fg_color="transparent")
        nav.grid(row=0, column=2, padx=20, sticky="e")

        self.btn_create = ctk.CTkButton(
            nav, text="⊞  Create", height=34, corner_radius=8,
            fg_color=BLUE, text_color="#FFFFFF", hover_color=BLUE_DK,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=lambda: self._show_page("create"))
        self.btn_create.pack(side="left", padx=(0, 8))

        self.btn_history = ctk.CTkButton(
            nav, text="↺  History", height=34, corner_radius=8,
            fg_color="transparent", text_color=TEXT_MD,
            hover_color="#F1F5F9", border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=13),
            command=lambda: self._show_page("history"))
        self.btn_history.pack(side="left")

    def _show_page(self, name):
        if name == "create":
            self.btn_create.configure(fg_color=BLUE, text_color="#FFFFFF",
                                      font=ctk.CTkFont(size=13, weight="bold"))
            self.btn_history.configure(fg_color="transparent", text_color=TEXT_MD,
                                       font=ctk.CTkFont(size=13))
            if hasattr(self, "history_body"):
                self.history_body.grid_forget()
            self.create_body.grid(row=1, column=0, sticky="nsew",
                                  padx=28, pady=20)
        else:
            self.btn_history.configure(fg_color=BLUE, text_color="#FFFFFF",
                                       font=ctk.CTkFont(size=13, weight="bold"))
            self.btn_create.configure(fg_color="transparent", text_color=TEXT_MD,
                                      font=ctk.CTkFont(size=13))
            self.create_body.grid_forget()
            self.history_body.grid(row=1, column=0, sticky="nsew",
                                   padx=28, pady=20)
            self._load_history()

    # ── Body ─────────────────────────────────────────────────────────────────
    def _build_body(self):
        # ── CREATE PAGE
        self.create_body = ctk.CTkFrame(self, fg_color="transparent")
        self.create_body.grid_columnconfigure(0, weight=5)
        self.create_body.grid_columnconfigure(1, weight=4)
        self.create_body.grid_rowconfigure(0, weight=1)

        self._build_left(self.create_body)
        self._build_right(self.create_body)
        # Initialize after all widgets are created
        self._on_type_change("URL")

        # ── HISTORY PAGE
        self.history_body = ctk.CTkFrame(self, fg_color="transparent")
        self.history_body.grid_columnconfigure(0, weight=1)
        self.history_body.grid_rowconfigure(1, weight=1)

        h_top = ctk.CTkFrame(self.history_body, fg_color="transparent")
        h_top.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ctk.CTkLabel(h_top, text="Generation History",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=TEXT_DK).pack(side="left")
        ctk.CTkLabel(h_top, text="Review and manage your recently generated QR codes.",
                     font=ctk.CTkFont(size=13), text_color=TEXT_LT).pack(
                         side="left", padx=12, pady=(4, 0))

        self.hist_scroll = ctk.CTkScrollableFrame(self.history_body,
                                                   fg_color="transparent")
        self.hist_scroll.grid(row=1, column=0, sticky="nsew")

    # ── Left Panel ───────────────────────────────────────────────────────────
    def _build_left(self, parent):
        left = ctk.CTkScrollableFrame(parent, fg_color="transparent",
                                      scrollbar_button_color=BG,
                                      scrollbar_button_hover_color=BORDER)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        left.grid_columnconfigure(0, weight=1)

        # ── Type Tabs ──────────────────────────────────────────────────────
        self.type_seg = PillSegButton(left,
                                      values=["URL", "Text", "Email", "WiFi"],
                                      command=self._on_type_change, height=46)
        self.type_seg.grid(row=0, column=0, sticky="ew", padx=2, pady=(0, 12))

        # ── Enter URL Card ─────────────────────────────────────────────────
        self.input_card = ctk.CTkFrame(left, fg_color=CARD_BG,
                                       corner_radius=12, border_width=1,
                                       border_color=BORDER)
        self.input_card.grid(row=1, column=0, sticky="ew", padx=2, pady=(0, 16))
        self.input_card.grid_columnconfigure(0, weight=1)

        self.input_widgets = {}
        self._build_input_fields(self.input_card)

        # ── Colors Accordion ───────────────────────────────────────────────
        self.acc_colors = AccordionCard(left, title="Colors",
                                        icon="🎨", expanded=False)
        self.acc_colors.grid(row=2, column=0, sticky="ew", padx=2, pady=(0, 16))
        self._build_colors_content(self.acc_colors.content)

        # ── Design Accordion ───────────────────────────────────────────────
        self.acc_design = AccordionCard(left, title="Design",
                                        icon="⊞", expanded=False)
        self.acc_design.grid(row=3, column=0, sticky="ew", padx=2, pady=(0, 16))
        self._build_design_content(self.acc_design.content)

        # ── Logo Accordion ─────────────────────────────────────────────────
        self.acc_logo = AccordionCard(left, title="Logo",
                                      icon="🖼️", expanded=False)
        self.acc_logo.grid(row=4, column=0, sticky="ew", padx=2, pady=(0, 16))
        self._build_logo_content(self.acc_logo.content)

        # Show default tab - called after right panel is built
        # self._on_type_change("URL")  # moved to _build_body

    def _build_input_fields(self, parent):
        pad = dict(padx=16, pady=(0, 16))

        # ── URL ──────────────────────────────────────────────────────────
        f_url = ctk.CTkFrame(parent, fg_color="transparent")
        f_url.grid(row=0, column=0, sticky="ew")
        f_url.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_url, text="Enter URL", text_color=TEXT_MD,
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w",
                                                      padx=16, pady=(14, 4))
        self.entry_url = ctk.CTkEntry(
            f_url, placeholder_text="https://example.com",
            height=48, corner_radius=8,
            border_width=1, border_color="#000000",
            fg_color="#eff4ff",
            text_color=TEXT_DK,
            font=ctk.CTkFont(size=14))
        self.entry_url.insert(0, "https://qrpro.io/workspace")
        self.entry_url.grid(row=1, column=0, sticky="ew", **pad)
        self.entry_url.bind("<KeyRelease>", self._generate_qr)
        self.input_widgets["URL"] = f_url

        # ── Text ──────────────────────────────────────────────────────────
        f_txt = ctk.CTkFrame(parent, fg_color="transparent")
        f_txt.grid(row=0, column=0, sticky="ew")
        f_txt.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_txt, text="Enter Text", text_color=TEXT_MD,
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w",
                                                      padx=16, pady=(14, 4))
        self.entry_txt = ctk.CTkTextbox(
            f_txt, height=80, corner_radius=10,
            border_width=1, border_color="#000000",
            fg_color="#eff4ff",
            text_color=TEXT_DK,
            font=ctk.CTkFont(size=13))
        self.entry_txt.grid(row=1, column=0, sticky="ew", **pad)
        self.entry_txt.bind("<KeyRelease>", self._generate_qr)
        self.input_widgets["Text"] = f_txt

        # ── Email ─────────────────────────────────────────────────────────
        f_eml = ctk.CTkFrame(parent, fg_color="transparent")
        f_eml.grid(row=0, column=0, sticky="ew")
        f_eml.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_eml, text="Email Address", text_color=TEXT_MD,
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w",
                                                      padx=16, pady=(14, 4))
        self.entry_eml = ctk.CTkEntry(
            f_eml, placeholder_text="hello@example.com",
            height=42, corner_radius=10,
            border_width=1, border_color="#000000",
            fg_color="#eff4ff", text_color=TEXT_DK,
            font=ctk.CTkFont(size=13))
        self.entry_eml.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.entry_eml.bind("<KeyRelease>", self._generate_qr)
        ctk.CTkLabel(f_eml, text="Subject", text_color=TEXT_MD,
                     font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w",
                                                      padx=16, pady=(0, 4))
        self.entry_sub = ctk.CTkEntry(
            f_eml, placeholder_text="Subject line...",
            height=42, corner_radius=10,
            border_width=1, border_color="#000000",
            fg_color="#eff4ff", text_color=TEXT_DK,
            font=ctk.CTkFont(size=13))
        self.entry_sub.grid(row=3, column=0, sticky="ew", **pad)
        self.entry_sub.bind("<KeyRelease>", self._generate_qr)
        self.input_widgets["Email"] = f_eml

        # ── WiFi ──────────────────────────────────────────────────────────
        f_wifi = ctk.CTkFrame(parent, fg_color="transparent")
        f_wifi.grid(row=0, column=0, sticky="ew")
        f_wifi.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_wifi, text="Network Name (SSID)", text_color=TEXT_MD,
                     font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w",
                                                      padx=16, pady=(14, 4))
        self.entry_ssid = ctk.CTkEntry(
            f_wifi, placeholder_text="MyNetwork",
            height=42, corner_radius=10,
            border_width=1, border_color="#000000",
            fg_color="#eff4ff", text_color=TEXT_DK,
            font=ctk.CTkFont(size=13))
        self.entry_ssid.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.entry_ssid.bind("<KeyRelease>", self._generate_qr)
        ctk.CTkLabel(f_wifi, text="Password", text_color=TEXT_MD,
                     font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w",
                                                      padx=16, pady=(0, 4))
        self.entry_pass = ctk.CTkEntry(
            f_wifi, show="*",
            placeholder_text="Password",
            height=42, corner_radius=10,
            border_width=1, border_color="#000000",
            fg_color="#eff4ff", text_color=TEXT_DK,
            font=ctk.CTkFont(size=13))
        self.entry_pass.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.entry_pass.bind("<KeyRelease>", self._generate_qr)
        ctk.CTkLabel(f_wifi, text="Security", text_color=TEXT_MD,
                     font=ctk.CTkFont(size=12)).grid(row=4, column=0, sticky="w",
                                                      padx=16, pady=(0, 4))
        self.sec_seg = PillSegButton(f_wifi, values=["WPA/WPA2", "WEP", "None"],
                                     command=self._generate_qr, height=38)
        self.sec_seg.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.input_widgets["WiFi"] = f_wifi

    def _build_colors_content(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(parent, text="Foreground", text_color=TEXT_LT,
                     font=ctk.CTkFont(size=11)).grid(
                         row=0, column=0, sticky="w", padx=12, pady=(4, 4))
        ctk.CTkLabel(parent, text="Background", text_color=TEXT_LT,
                     font=ctk.CTkFont(size=11)).grid(
                         row=0, column=1, sticky="w", padx=12, pady=(4, 4))

        self.btn_fg = ctk.CTkButton(
            parent, text="#000000", fg_color="#000000",
            text_color="#FFFFFF", hover_color="#222222",
            height=40, corner_radius=8,
            command=lambda: self._pick_color("fg"))
        self.btn_fg.grid(row=1, column=0, padx=(12, 6), pady=(0, 12), sticky="ew")

        self.btn_bg = ctk.CTkButton(
            parent, text="#FFFFFF", fg_color="#FFFFFF",
            text_color=TEXT_DK, hover_color="#F8FAFC",
            border_width=1, border_color=BORDER,
            height=40, corner_radius=8,
            command=lambda: self._pick_color("bg"))
        self.btn_bg.grid(row=1, column=1, padx=(6, 12), pady=(0, 12), sticky="ew")

    def _build_design_content(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(parent, text="Pattern Style", text_color=TEXT_LT,
                     font=ctk.CTkFont(size=11)).grid(
                         row=0, column=0, sticky="w", padx=12, pady=(4, 4))
        self.shape_seg = PillSegButton(parent,
                                       values=["Square", "Rounded", "Circle", "Gapped"],
                                       command=self._generate_qr, height=38)
        self.shape_seg.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    def _build_logo_content(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        self.logo_btn = ctk.CTkButton(
            parent, text="⬆  Drop logo here or click to browse\nPNG · SVG · JPG",
            fg_color="#F8FAFF", text_color=TEXT_LT,
            hover_color="#EEF2FF", border_width=1, border_color=BORDER,
            height=80, corner_radius=10,
            command=self._upload_logo)
        self.logo_btn.grid(row=0, column=0, sticky="ew", padx=12, pady=(4, 4))
        self.logo_clear = ctk.CTkButton(
            parent, text="Remove Logo", fg_color="transparent",
            text_color="#EF4444", hover_color="#FEE2E2",
            height=28, font=ctk.CTkFont(size=11),
            command=self._clear_logo)

    # ── Right Panel ──────────────────────────────────────────────────────────
    def _build_right(self, parent):
        right = ctk.CTkFrame(parent, fg_color=CARD_BG,
                             corner_radius=16, border_width=1, border_color=BORDER)
        right.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        # Header
        h = ctk.CTkFrame(right, fg_color="transparent")
        h.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 16))
        ctk.CTkLabel(h, text="Live Preview",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color=TEXT_DK).pack(side="left")
        ctk.CTkLabel(h, text="● Synced",
                     fg_color="#dcfce7", text_color="#15803d",
                     corner_radius=12, padx=12, pady=4,
                     font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")

        # QR Display Area
        # Outer white container
        disp_outer = ctk.CTkFrame(right, fg_color=CARD_BG, corner_radius=16,
                                  border_width=1, border_color=BORDER)
        disp_outer.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        disp_outer.grid_rowconfigure(0, weight=1)
        disp_outer.grid_columnconfigure(0, weight=1)

        # Inner container (now transparent to show white)
        disp_inner = ctk.CTkFrame(disp_outer, fg_color="transparent")
        disp_inner.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        disp_inner.grid_rowconfigure(0, weight=1)
        disp_inner.grid_columnconfigure(0, weight=1)

        self.qr_display = ctk.CTkLabel(
            disp_inner, text="",
            font=ctk.CTkFont(size=14), text_color=TEXT_LT)
        self.qr_display.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        # Download Buttons
        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row, text="⬇  PNG Image",
                      fg_color=BLUE, hover_color=BLUE_DK,
                      text_color="#ffffff", height=48, corner_radius=12,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save_png).grid(row=0, column=0,
                                                    padx=(0, 8), sticky="ew")

        ctk.CTkButton(btn_row, text="⬇  SVG Vector",
                      fg_color="#dae2fd", hover_color="#d3e4fe",
                      text_color="#5c647a", height=48, corner_radius=12,
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save_svg).grid(row=0, column=1,
                                                    padx=(8, 0), sticky="ew")

        # Secondary Buttons
        btn_row2 = ctk.CTkFrame(right, fg_color="transparent")
        btn_row2.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 20))
        btn_row2.grid_columnconfigure(0, weight=1)
        btn_row2.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row2, text="📋  Copy Image",
                      fg_color="transparent", hover_color="#eff4ff",
                      text_color=TEXT_MD, border_width=1, border_color=BORDER,
                      height=44, corner_radius=12,
                      font=ctk.CTkFont(size=14),
                      command=self._copy_image).grid(row=0, column=0,
                                                     padx=(0, 8), sticky="ew")

        ctk.CTkButton(btn_row2, text="⎙  Print Directly",
                      fg_color="transparent", hover_color="#eff4ff",
                      text_color=TEXT_MD, border_width=1, border_color=BORDER,
                      height=44, corner_radius=12,
                      font=ctk.CTkFont(size=14),
                      command=self._print).grid(row=0, column=1,
                                                 padx=(8, 0), sticky="ew")

        # Accuracy badge (Moved to bottom)
        acc = ctk.CTkFrame(right, fg_color="transparent")
        acc.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 20))
        ctk.CTkLabel(acc, text="Scan Accuracy",
                     font=ctk.CTkFont(size=12), text_color=TEXT_LT).pack(anchor="w")
        self.status_lbl = ctk.CTkLabel(acc, text="High (Level H)",
                                        font=ctk.CTkFont(size=14, weight="bold"),
                                        text_color="#16A34A")
        self.status_lbl.pack(anchor="w")

    # ── Callbacks ────────────────────────────────────────────────────────────
    def _on_type_change(self, value):
        for f in self.input_widgets.values():
            f.grid_remove()
        self.input_widgets[value].grid(row=0, column=0, sticky="ew")
        self._generate_qr()

    def _pick_color(self, target):
        init = self.qr_fg if target == "fg" else self.qr_bg
        res = colorchooser.askcolor(color=init, title="Select color")
        if res[1]:
            if target == "fg":
                self.qr_fg = res[1]
                r = int(res[1][1:3], 16)
                tc = "#FFFFFF" if r < 128 else TEXT_DK
                self.btn_fg.configure(fg_color=res[1], text=res[1].upper(),
                                      text_color=tc)
            else:
                self.qr_bg = res[1]
                r = int(res[1][1:3], 16)
                tc = "#FFFFFF" if r < 128 else TEXT_DK
                self.btn_bg.configure(fg_color=res[1], text=res[1].upper(),
                                      text_color=tc)
            self._generate_qr()

    def _upload_logo(self):
        p = filedialog.askopenfilename(
            filetypes=[("Images", "*.png *.jpg *.jpeg *.svg")])
        if p:
            self.logo_path = p
            name = os.path.basename(p)
            self.logo_btn.configure(text=f"✓  {name}")
            self.logo_clear.grid(row=1, column=0, sticky="ew",
                                  padx=12, pady=(0, 12))
            self._generate_qr()

    def _clear_logo(self):
        self.logo_path = None
        self.logo_btn.configure(
            text="⬆  Drop logo here or click to browse\nPNG · SVG · JPG")
        self.logo_clear.grid_remove()
        self._generate_qr()

    def _get_data(self):
        t = self.type_seg.get()
        if t == "URL":
            return self.entry_url.get().strip()
        if t == "Text":
            return self.entry_txt.get("1.0", "end-1c").strip()
        if t == "Email":
            e = self.entry_eml.get().strip()
            s = self.entry_sub.get().strip()
            return f"mailto:{e}?subject={s}" if e else ""
        if t == "WiFi":
            ssid = self.entry_ssid.get().strip()
            pw   = self.entry_pass.get().strip()
            sec  = {"WPA/WPA2": "WPA", "WEP": "WEP", "None": "nopass"}.get(
                self.sec_seg.get(), "WPA")
            return f"WIFI:S:{ssid};T:{sec};P:{pw};;" if ssid else ""
        return ""

    def _drawer(self):
        s = self.shape_seg.get()
        if s == "Circle":  return CircleModuleDrawer()
        if s == "Rounded": return RoundedModuleDrawer()
        if s == "Gapped":  return GappedSquareModuleDrawer()
        return SquareModuleDrawer()

    def _generate_qr(self, *_):
        data = self._get_data()
        if not data:
            self.qr_display.configure(image="", text="No data — type something above",
                                       font=ctk.CTkFont(size=12),
                                       text_color=TEXT_LT)
            self.status_lbl.configure(text="Waiting for input...",
                                       text_color=TEXT_LT)
            self.qr_img = None
            return
        try:
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                               box_size=10, border=2)
            qr.add_data(data)
            qr.make(fit=True)
            img = qr.make_image(image_factory=StyledPilImage,
                                module_drawer=self._drawer()).convert("RGBA")
            # Colorise
            fg, bg = hex_rgb(self.qr_fg), hex_rgb(self.qr_bg)
            px = img.load()
            for x in range(img.width):
                for y in range(img.height):
                    r, *_ = px[x, y]
                    px[x, y] = (*fg, 255) if r < 128 else (*bg, 255)
            # Logo overlay
            if self.logo_path and os.path.exists(self.logo_path):
                try:
                    logo = Image.open(self.logo_path).convert("RGBA")
                    bw = int(img.width * 0.22)
                    logo = logo.resize(
                        (bw, int(logo.height * bw / logo.width)), RESAMPLE)
                    pos = ((img.width - logo.width) // 2,
                           (img.height - logo.height) // 2)
                    patch = Image.new("RGBA",
                                      (logo.width + 12, logo.height + 12),
                                      (*bg, 255))
                    img.paste(patch, (pos[0] - 6, pos[1] - 6))
                    img.paste(logo, pos, logo)
                except Exception:
                    pass
            self.qr_img = img
            thumb = img.copy()
            thumb.thumbnail((250, 250), RESAMPLE)
            ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb,
                                   size=(thumb.width, thumb.height))
            self.qr_display.configure(image=ctk_img, text="")
            self.status_lbl.configure(
                text=f"High (Level H)  ·  {img.width}×{img.height} px",
                text_color="#16A34A")
        except Exception as e:
            self.status_lbl.configure(text=f"Error: {e}", text_color="#EF4444")

    # ── Save / Print ──────────────────────────────────────────────────────────
    def _save_png(self):
        if not self.qr_img:
            return
        path = filedialog.asksaveasfilename(defaultextension=".png",
                                            filetypes=[("PNG files", "*.png")])
        if path:
            self.qr_img.save(path, "PNG")
            self.status_lbl.configure(text=f"Saved: {os.path.basename(path)}", text_color="#16A34A")
            self._save_history()

    def _copy_image(self):
        if not self.qr_img: return
        import tempfile, subprocess
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                self.qr_img.save(f.name, "PNG")
                tmp_path = f.name
            script = f'set the clipboard to (read (POSIX file "{tmp_path}") as TIFF picture)'
            subprocess.run(["osascript", "-e", script], check=True)
            self.status_lbl.configure(text="Copied to clipboard!", text_color="#16A34A")
        except Exception as e:
            self.status_lbl.configure(text=f"Copy failed: {e}", text_color="#EF4444")

    def _save_svg(self):
        data = self._get_data()
        if not data:
            messagebox.showwarning("No data", "Enter data first.")
            return
        p = filedialog.asksaveasfilename(defaultextension=".svg",
                                         filetypes=[("SVG", "*.svg")],
                                         initialfile="QR_Code.svg")
        if p:
            import qrcode.image.svg
            factory = qrcode.image.svg.SvgPathImage
            qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                               box_size=10, border=4, image_factory=factory)
            qr.add_data(data)
            qr.make(fit=True)
            qr.make_image().save(p)
            self._save_history()

    def _print(self):
        messagebox.showinfo("Print", "Printing via system dialog.")

    def _save_history(self):
        data = self._get_data()
        if not data or not self.qr_img:
            return
        ts = int(datetime.now().timestamp())
        fn = f"qr_{ts}.png"
        fp = os.path.join(HISTORY_DIR, fn)
        self.qr_img.save(fp)
        entry = {"id": ts, "type": self.type_seg.get(), "data": data,
                 "image": fn, "date": datetime.now().strftime("%b %d, %Y %H:%M")}
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE) as f:
                    history = json.load(f)
            except Exception:
                pass
        if history and history[0].get("data") == data:
            return
        history.insert(0, entry)
        with open(HISTORY_FILE, "w") as f:
            json.dump(history[:50], f, indent=2)

    def _load_history(self):
        for w in self.hist_scroll.winfo_children():
            w.destroy()
        history = []
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE) as f:
                    history = json.load(f)
            except Exception:
                pass
        if not history:
            ctk.CTkLabel(self.hist_scroll, text="No history yet.",
                         text_color=TEXT_LT,
                         font=ctk.CTkFont(size=14)).pack(pady=60)
            return
        for i in range(3):
            self.hist_scroll.grid_columnconfigure(i, weight=1)
        for idx, item in enumerate(history):
            self._make_history_card(item, idx // 3, idx % 3)

    def _make_history_card(self, item, row, col):
        card = ctk.CTkFrame(self.hist_scroll, fg_color=CARD_BG,
                            corner_radius=12, border_width=1, border_color=BORDER)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        img_path = os.path.join(HISTORY_DIR, item.get("image", ""))
        if os.path.exists(img_path):
            try:
                thumb = Image.open(img_path)
                ci = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(56, 56))
                ctk.CTkLabel(card, image=ci, text="").grid(
                    row=0, column=0, rowspan=2, padx=14, pady=14, sticky="w")
            except Exception:
                pass

        meta = ctk.CTkFrame(card, fg_color="transparent")
        meta.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=(14, 4))
        ctk.CTkLabel(meta, text=item.get("type", "QR"),
                     fg_color=BLUE_LT, text_color=BLUE,
                     corner_radius=4, padx=6,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkLabel(meta, text=item.get("date", ""),
                     text_color=TEXT_LT,
                     font=ctk.CTkFont(size=10)).pack(side="right")

        short = item.get("data", "")
        if len(short) > 26:
            short = short[:23] + "..."
        ctk.CTkLabel(card, text=short, text_color=TEXT_DK,
                     font=ctk.CTkFont(size=12, weight="bold"),
                     anchor="w").grid(row=1, column=1, sticky="w",
                                      padx=(0, 12), pady=(0, 14))

        af = ctk.CTkFrame(card, fg_color="transparent")
        af.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        af.grid_columnconfigure(0, weight=1)

        def _export():
            p = filedialog.asksaveasfilename(defaultextension=".png",
                                              filetypes=[("PNG", "*.png")])
            if p and os.path.exists(img_path):
                import shutil
                shutil.copy(img_path, p)

        def _delete():
            hist = []
            if os.path.exists(HISTORY_FILE):
                with open(HISTORY_FILE) as f:
                    hist = json.load(f)
            hist = [h for h in hist if h.get("id") != item.get("id")]
            with open(HISTORY_FILE, "w") as f:
                json.dump(hist, f, indent=2)
            if os.path.exists(img_path):
                os.remove(img_path)
            self._load_history()

        ctk.CTkButton(af, text="⬇", width=32, height=28, corner_radius=6,
                      fg_color="#F1F5F9", text_color=TEXT_MD,
                      hover_color=BORDER, command=_export).pack(side="left", padx=(0, 4))
        ctk.CTkButton(af, text="🗑", width=32, height=28, corner_radius=6,
                      fg_color="transparent", text_color="#EF4444",
                      hover_color="#FEE2E2", command=_delete).pack(side="right")


if __name__ == "__main__":
    app = QRGeneratorPro()
    app.mainloop()