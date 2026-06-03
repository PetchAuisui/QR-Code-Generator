import os
import sys
from tkinter import colorchooser, filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import shutil

from .config import *
from .core import QRManager, HistoryManager, ClipboardManager
from .widgets import PillSegButton, AccordionCard

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

class TopNavBar(ctk.CTkFrame):
    def __init__(self, master, on_create_click, on_history_click, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=0, border_width=1, border_color=BORDER, height=56, **kwargs)
        self.grid_columnconfigure(1, weight=1)
        self.grid_propagate(False)
        
        sep = ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0)
        sep.grid(row=0, column=0, sticky="ews")

        ctk.CTkLabel(self, text="QR Pro", font=ctk.CTkFont(size=18, weight="bold"), text_color=BLUE)\
            .grid(row=0, column=0, padx=28, pady=14, sticky="w")

        nav = ctk.CTkFrame(self, fg_color="transparent")
        nav.grid(row=0, column=2, padx=20, sticky="e")

        self.btn_create = ctk.CTkButton(
            nav, text="⊞  Create", height=34, corner_radius=8,
            fg_color=BLUE, text_color="#FFFFFF", hover_color=BLUE_DK,
            font=ctk.CTkFont(size=13, weight="bold"),
            command=on_create_click)
        self.btn_create.pack(side="left", padx=(0, 8))

        self.btn_history = ctk.CTkButton(
            nav, text="↺  History", height=34, corner_radius=8,
            fg_color="transparent", text_color=TEXT_MD,
            hover_color="#F1F5F9", border_width=1, border_color=BORDER,
            font=ctk.CTkFont(size=13),
            command=on_history_click)
        self.btn_history.pack(side="left")

    def set_active(self, page_name):
        if page_name == "create":
            self.btn_create.configure(fg_color=BLUE, text_color="#FFFFFF", font=ctk.CTkFont(size=13, weight="bold"))
            self.btn_history.configure(fg_color="transparent", text_color=TEXT_MD, font=ctk.CTkFont(size=13))
        else:
            self.btn_history.configure(fg_color=BLUE, text_color="#FFFFFF", font=ctk.CTkFont(size=13, weight="bold"))
            self.btn_create.configure(fg_color="transparent", text_color=TEXT_MD, font=ctk.CTkFont(size=13))


class WorkspacePanel(ctk.CTkScrollableFrame):
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, fg_color=BG, scrollbar_button_color=BG, scrollbar_button_hover_color=BORDER, **kwargs)
        # Force canvas bg color — CTkScrollableFrame's internal canvas can default
        # to the OS system color (white/grey) on Windows if not set explicitly.
        if hasattr(self, "_canvas"):
            self._canvas.configure(bg=BG)
        self.app = app_controller
        self.grid_columnconfigure(0, weight=1)

        self.type_seg = PillSegButton(self, values=["URL", "Text", "Email", "WiFi"], command=self._on_type_change, height=46)
        self.type_seg.grid(row=0, column=0, sticky="ew", padx=2, pady=(0, 12))

        self.input_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
        self.input_card.grid(row=1, column=0, sticky="ew", padx=2, pady=(0, 16))
        self.input_card.grid_columnconfigure(0, weight=1)

        self.input_widgets = {}
        self._build_input_fields()

        self.acc_colors = AccordionCard(self, title="Colors", icon="🎨", expanded=False)
        self.acc_colors.grid(row=2, column=0, sticky="ew", padx=2, pady=(0, 16))
        self._build_colors_content()

        self.acc_design = AccordionCard(self, title="Design", icon="⊞", expanded=False)
        self.acc_design.grid(row=3, column=0, sticky="ew", padx=2, pady=(0, 16))
        self._build_design_content()

        self.acc_logo = AccordionCard(self, title="Logo", icon="🖼️", expanded=False)
        self.acc_logo.grid(row=4, column=0, sticky="ew", padx=2, pady=(0, 16))
        self._build_logo_content()

    def _build_input_fields(self):
        pad = dict(padx=16, pady=(0, 16))
        parent = self.input_card

        # URL
        f_url = ctk.CTkFrame(parent, fg_color="transparent")
        f_url.grid(row=0, column=0, sticky="ew")
        f_url.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_url, text="Enter URL", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.entry_url = ctk.CTkEntry(f_url, placeholder_text="https://example.com", height=48, corner_radius=8, border_width=1, border_color="#000000", fg_color="#eff4ff", text_color=TEXT_DK, font=ctk.CTkFont(size=14))
        self.entry_url.insert(0, "https://qrpro.io/workspace")
        self.entry_url.grid(row=1, column=0, sticky="ew", **pad)
        self.entry_url.bind("<KeyRelease>", lambda e: self.app.request_generate())
        self.input_widgets["URL"] = f_url

        # Text
        f_txt = ctk.CTkFrame(parent, fg_color="transparent")
        f_txt.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_txt, text="Enter Text", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.entry_txt = ctk.CTkTextbox(f_txt, height=80, corner_radius=10, border_width=1, border_color="#000000", fg_color="#eff4ff", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        self.entry_txt.grid(row=1, column=0, sticky="ew", **pad)
        self.entry_txt.bind("<KeyRelease>", lambda e: self.app.request_generate())
        self.input_widgets["Text"] = f_txt

        # Email
        f_eml = ctk.CTkFrame(parent, fg_color="transparent")
        f_eml.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_eml, text="Email Address", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.entry_eml = ctk.CTkEntry(f_eml, placeholder_text="hello@example.com", height=42, corner_radius=10, border_width=1, border_color="#000000", fg_color="#eff4ff", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        self.entry_eml.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.entry_eml.bind("<KeyRelease>", lambda e: self.app.request_generate())
        ctk.CTkLabel(f_eml, text="Subject", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 4))
        self.entry_sub = ctk.CTkEntry(f_eml, placeholder_text="Subject line...", height=42, corner_radius=10, border_width=1, border_color="#000000", fg_color="#eff4ff", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        self.entry_sub.grid(row=3, column=0, sticky="ew", **pad)
        self.entry_sub.bind("<KeyRelease>", lambda e: self.app.request_generate())
        self.input_widgets["Email"] = f_eml

        # WiFi
        f_wifi = ctk.CTkFrame(parent, fg_color="transparent")
        f_wifi.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_wifi, text="Network Name (SSID)", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.entry_ssid = ctk.CTkEntry(f_wifi, placeholder_text="MyNetwork", height=42, corner_radius=10, border_width=1, border_color="#000000", fg_color="#eff4ff", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        self.entry_ssid.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.entry_ssid.bind("<KeyRelease>", lambda e: self.app.request_generate())
        ctk.CTkLabel(f_wifi, text="Password", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 4))
        self.entry_pass = ctk.CTkEntry(f_wifi, show="*", placeholder_text="Password", height=42, corner_radius=10, border_width=1, border_color="#000000", fg_color="#eff4ff", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        self.entry_pass.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.entry_pass.bind("<KeyRelease>", lambda e: self.app.request_generate())
        ctk.CTkLabel(f_wifi, text="Security", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=4, column=0, sticky="w", padx=16, pady=(0, 4))
        self.sec_seg = PillSegButton(f_wifi, values=["WPA/WPA2", "WEP", "None"], command=lambda e: self.app.request_generate(debounce=False), height=38)
        self.sec_seg.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.input_widgets["WiFi"] = f_wifi

    def _build_colors_content(self):
        parent = self.acc_colors.content
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(parent, text="Foreground", text_color=TEXT_LT, font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=12, pady=(4, 4))
        ctk.CTkLabel(parent, text="Background", text_color=TEXT_LT, font=ctk.CTkFont(size=11)).grid(row=0, column=1, sticky="w", padx=12, pady=(4, 4))

        self.btn_fg = ctk.CTkButton(parent, text="#000000", fg_color="#000000", text_color="#FFFFFF", hover_color="#222222", height=40, corner_radius=8, command=lambda: self._pick_color("fg"))
        self.btn_fg.grid(row=1, column=0, padx=(12, 6), pady=(0, 12), sticky="ew")

        self.btn_bg = ctk.CTkButton(parent, text="#FFFFFF", fg_color="#FFFFFF", text_color=TEXT_DK, hover_color="#F8FAFC", border_width=1, border_color=BORDER, height=40, corner_radius=8, command=lambda: self._pick_color("bg"))
        self.btn_bg.grid(row=1, column=1, padx=(6, 12), pady=(0, 12), sticky="ew")

    def _build_design_content(self):
        parent = self.acc_design.content
        parent.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(parent, text="Pattern Style", text_color=TEXT_LT, font=ctk.CTkFont(size=11)).grid(row=0, column=0, sticky="w", padx=12, pady=(4, 4))
        self.shape_seg = PillSegButton(parent, values=["Square", "Rounded", "Circle", "Gapped"], command=lambda e: self.app.request_generate(debounce=False), height=38)
        self.shape_seg.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))

    def _build_logo_content(self):
        parent = self.acc_logo.content
        parent.grid_columnconfigure(0, weight=1)
        self.logo_btn = ctk.CTkButton(parent, text="⬆  Drop logo here or click to browse\nPNG · SVG · JPG", fg_color="#F8FAFF", text_color=TEXT_LT, hover_color="#EEF2FF", border_width=1, border_color=BORDER, height=80, corner_radius=10, command=self._upload_logo)
        self.logo_btn.grid(row=0, column=0, sticky="ew", padx=12, pady=(4, 4))
        self.logo_clear = ctk.CTkButton(parent, text="Remove Logo", fg_color="transparent", text_color="#EF4444", hover_color="#FEE2E2", height=28, font=ctk.CTkFont(size=11), command=self._clear_logo)

    def _on_type_change(self, value):
        for f in self.input_widgets.values():
            f.grid_remove()
        if value in self.input_widgets:
            self.input_widgets[value].grid(row=0, column=0, sticky="ew")
        self.app.request_generate(debounce=False)

    def _pick_color(self, target):
        init = self.app.qr_fg if target == "fg" else self.app.qr_bg
        res = colorchooser.askcolor(color=init, title="Select color")
        if res[1]:
            if target == "fg":
                self.app.qr_fg = res[1]
                r = int(res[1][1:3], 16)
                self.btn_fg.configure(fg_color=res[1], text=res[1].upper(), text_color="#FFFFFF" if r < 128 else TEXT_DK)
            else:
                self.app.qr_bg = res[1]
                r = int(res[1][1:3], 16)
                self.btn_bg.configure(fg_color=res[1], text=res[1].upper(), text_color="#FFFFFF" if r < 128 else TEXT_DK)
            self.app.request_generate(debounce=False)

    def _upload_logo(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.png *.jpg *.jpeg *.svg")])
        if p:
            self.app.logo_path = p
            name = os.path.basename(p)
            self.logo_btn.configure(text=f"✓  {name}")
            self.logo_clear.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 12))
            self.app.request_generate(debounce=False)

    def _clear_logo(self):
        self.app.logo_path = None
        self.logo_btn.configure(text="⬆  Drop logo here or click to browse\nPNG · SVG · JPG")
        self.logo_clear.grid_remove()
        self.app.request_generate(debounce=False)

    def get_data(self):
        t = self.type_seg.get()
        if t == "URL": return self.entry_url.get().strip()
        if t == "Text": return self.entry_txt.get("1.0", "end-1c").strip()
        if t == "Email":
            e = self.entry_eml.get().strip()
            s = self.entry_sub.get().strip()
            return f"mailto:{e}?subject={s}" if e else ""
        if t == "WiFi":
            ssid = self.entry_ssid.get().strip()
            pw   = self.entry_pass.get().strip()
            sec  = {"WPA/WPA2": "WPA", "WEP": "WEP", "None": "nopass"}.get(self.sec_seg.get(), "WPA")
            return f"WIFI:S:{ssid};T:{sec};P:{pw};;" if ssid else ""
        return ""


class PreviewPanel(ctk.CTkFrame):
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER, **kwargs)
        self.app = app_controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color="transparent")
        h.grid(row=0, column=0, sticky="ew", padx=24, pady=(20, 16))
        ctk.CTkLabel(h, text="Live Preview", font=ctk.CTkFont(size=20, weight="bold"), text_color=TEXT_DK).pack(side="left")
        ctk.CTkLabel(h, text="● Synced", fg_color="#dcfce7", text_color="#15803d", corner_radius=12, padx=12, pady=4, font=ctk.CTkFont(size=12, weight="bold")).pack(side="right")

        disp_outer = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=16, border_width=1, border_color=BORDER)
        disp_outer.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 20))
        disp_outer.grid_rowconfigure(0, weight=1)
        disp_outer.grid_columnconfigure(0, weight=1)

        disp_inner = ctk.CTkFrame(disp_outer, fg_color="transparent")
        disp_inner.grid(row=0, column=0, padx=16, pady=16, sticky="nsew")
        disp_inner.grid_rowconfigure(0, weight=1)
        disp_inner.grid_columnconfigure(0, weight=1)

        self.qr_display = ctk.CTkLabel(disp_inner, text="No Data", font=ctk.CTkFont(size=14), text_color=TEXT_LT)
        self.qr_display.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row, text="⬇  PNG Image", fg_color=BLUE, hover_color=BLUE_DK, text_color="#ffffff", height=48, corner_radius=12, font=ctk.CTkFont(size=14, weight="bold"), command=self.app.save_png).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(btn_row, text="⬇  SVG Vector", fg_color="#dae2fd", hover_color="#d3e4fe", text_color="#5c647a", height=48, corner_radius=12, font=ctk.CTkFont(size=14, weight="bold"), command=self.app.save_svg).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        btn_row2 = ctk.CTkFrame(self, fg_color="transparent")
        btn_row2.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 20))
        btn_row2.grid_columnconfigure(0, weight=1)
        btn_row2.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row2, text="📋  Copy Image", fg_color="transparent", hover_color="#eff4ff", text_color=TEXT_MD, border_width=1, border_color=BORDER, height=44, corner_radius=12, font=ctk.CTkFont(size=14), command=self.app.copy_image).grid(row=0, column=0, padx=(0, 8), sticky="ew")
        ctk.CTkButton(btn_row2, text="⎙  Print Directly", fg_color="transparent", hover_color="#eff4ff", text_color=TEXT_MD, border_width=1, border_color=BORDER, height=44, corner_radius=12, font=ctk.CTkFont(size=14), command=self.app.print_image).grid(row=0, column=1, padx=(8, 0), sticky="ew")

        acc = ctk.CTkFrame(self, fg_color="transparent")
        acc.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 20))
        ctk.CTkLabel(acc, text="Scan Accuracy", font=ctk.CTkFont(size=12), text_color=TEXT_LT).pack(anchor="w")
        self.status_lbl = ctk.CTkLabel(acc, text="High (Level H)", font=ctk.CTkFont(size=14, weight="bold"), text_color="#16A34A")
        self.status_lbl.pack(anchor="w")

    def update_image(self, img):
        if not img:
            self.qr_display.configure(image="", text="No data — type something above")
            self.status_lbl.configure(text="Waiting for input...", text_color=TEXT_LT)
            return

        thumb = img.copy()
        thumb.thumbnail((250, 250), RESAMPLE)
        ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(thumb.width, thumb.height))
        self.qr_display.configure(image=ctk_img, text="")
        self.status_lbl.configure(text=f"High (Level H)  ·  {img.width}×{img.height} px", text_color="#16A34A")

    def set_error(self, err_msg):
        self.status_lbl.configure(text=f"Error: {err_msg}", text_color="#EF4444")
        self.qr_display.configure(image="", text="Error generating QR code")


class HistoryPanel(ctk.CTkFrame):
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, fg_color=BG, **kwargs)
        self.app = app_controller
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        h_top = ctk.CTkFrame(self, fg_color="transparent")
        h_top.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        ctk.CTkLabel(h_top, text="Generation History", font=ctk.CTkFont(size=22, weight="bold"), text_color=TEXT_DK).pack(side="left")
        ctk.CTkLabel(h_top, text="Review and manage your recently generated QR codes.", font=ctk.CTkFont(size=13), text_color=TEXT_LT).pack(side="left", padx=12, pady=(4, 0))

        self.hist_scroll = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.hist_scroll.grid(row=1, column=0, sticky="nsew")
        # Force canvas bg color on Windows
        if hasattr(self.hist_scroll, "_canvas"):
            self.hist_scroll._canvas.configure(bg=BG)

    def refresh(self):
        for w in self.hist_scroll.winfo_children():
            w.destroy()
        
        history = HistoryManager.load_history()
        if not history:
            ctk.CTkLabel(self.hist_scroll, text="No history yet.", text_color=TEXT_LT, font=ctk.CTkFont(size=14)).pack(pady=60)
            return

        for i in range(3):
            self.hist_scroll.grid_columnconfigure(i, weight=1)
        
        for idx, item in enumerate(history):
            self._make_card(item, idx // 3, idx % 3)

    def _make_card(self, item, row, col):
        card = ctk.CTkFrame(self.hist_scroll, fg_color=CARD_BG, corner_radius=12, border_width=1, border_color=BORDER)
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        img_path = os.path.join(HISTORY_DIR, item.get("image", ""))
        if os.path.exists(img_path):
            try:
                thumb = Image.open(img_path)
                ci = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(56, 56))
                ctk.CTkLabel(card, image=ci, text="").grid(row=0, column=0, rowspan=2, padx=14, pady=14, sticky="w")
            except Exception:
                pass

        meta = ctk.CTkFrame(card, fg_color="transparent")
        meta.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=(14, 4))
        ctk.CTkLabel(meta, text=item.get("type", "QR"), fg_color=BLUE_LT, text_color=BLUE, corner_radius=4, padx=6, font=ctk.CTkFont(size=10, weight="bold")).pack(side="left")
        ctk.CTkLabel(meta, text=item.get("date", ""), text_color=TEXT_LT, font=ctk.CTkFont(size=10)).pack(side="right")

        short = item.get("data", "")
        if len(short) > 26: short = short[:23] + "..."
        ctk.CTkLabel(card, text=short, text_color=TEXT_DK, font=ctk.CTkFont(size=12, weight="bold"), anchor="w").grid(row=1, column=1, sticky="w", padx=(0, 12), pady=(0, 14))

        af = ctk.CTkFrame(card, fg_color="transparent")
        af.grid(row=2, column=0, columnspan=2, sticky="ew", padx=12, pady=(0, 12))
        af.grid_columnconfigure(0, weight=1)

        def _export():
            p = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")])
            if p and os.path.exists(img_path): shutil.copy(img_path, p)

        def _delete():
            HistoryManager.delete_entry(item.get("id"), item.get("image", ""))
            self.refresh()

        ctk.CTkButton(af, text="⬇", width=32, height=28, corner_radius=6, fg_color="#F1F5F9", text_color=TEXT_MD, hover_color=BORDER, command=_export).pack(side="left", padx=(0, 4))
        ctk.CTkButton(af, text="🗑", width=32, height=28, corner_radius=6, fg_color="transparent", text_color="#EF4444", hover_color="#FEE2E2", command=_delete).pack(side="right")


def setup_macos_shortcuts(root):
    if sys.platform == "darwin":
        from tkinter import Menu

        class DummyEvent:
            def __init__(self, widget):
                self.widget = widget

        def select_all(event):
            if not event or not event.widget: return "break"
            widget = event.widget
            if hasattr(widget, "select_range"):
                widget.select_range(0, "end")
                widget.icursor("end")
            elif hasattr(widget, "tag_add"):
                widget.tag_add("sel", "1.0", "end-1c")
            return "break"

        def copy_text(event):
            if not event or not event.widget: return "break"
            widget = event.widget
            try:
                text = ""
                if hasattr(widget, "index") and hasattr(widget, "get"):
                    # Entry widget
                    try:
                        first = widget.index("sel.first")
                        last = widget.index("sel.last")
                        text = widget.get()[first:last]
                    except Exception:
                        pass
                elif hasattr(widget, "get"):
                    # Text widget
                    try:
                        text = widget.get("sel.first", "sel.last")
                    except Exception:
                        pass
                if text:
                    widget.clipboard_clear()
                    widget.clipboard_append(text)
            except Exception:
                widget.event_generate("<<Copy>>")
            return "break"

        def cut_text(event):
            if not event or not event.widget: return "break"
            widget = event.widget
            try:
                copy_text(event)
                try:
                    widget.delete("sel.first", "sel.last")
                except Exception:
                    pass
            except Exception:
                widget.event_generate("<<Cut>>")
            return "break"

        def paste_text(event):
            if not event or not event.widget: return "break"
            widget = event.widget
            try:
                text = widget.clipboard_get()
                if text:
                    try:
                        widget.delete("sel.first", "sel.last")
                    except Exception:
                        pass
                    widget.insert("insert", text)
            except Exception:
                widget.event_generate("<<Paste>>")
            return "break"

        # Bind to Entry and Text classes globally (English Layout)
        root.bind_class("Entry", "<Command-c>", copy_text)
        root.bind_class("Entry", "<Command-v>", paste_text)
        root.bind_class("Entry", "<Command-x>", cut_text)
        root.bind_class("Entry", "<Command-a>", select_all)
        
        root.bind_class("Text", "<Command-c>", copy_text)
        root.bind_class("Text", "<Command-v>", paste_text)
        root.bind_class("Text", "<Command-x>", cut_text)
        root.bind_class("Text", "<Command-a>", select_all)

        # Bind to Entry and Text classes globally (Thai Layout)
        root.bind_class("Entry", "<Command-Thai_saraae>", copy_text)
        root.bind_class("Entry", "<Command-Thai_oang>", paste_text)
        root.bind_class("Entry", "<Command-Thai_popla>", cut_text)
        root.bind_class("Entry", "<Command-Thai_fofan>", select_all)
        
        root.bind_class("Text", "<Command-Thai_saraae>", copy_text)
        root.bind_class("Text", "<Command-Thai_oang>", paste_text)
        root.bind_class("Text", "<Command-Thai_popla>", cut_text)
        root.bind_class("Text", "<Command-Thai_fofan>", select_all)

        # Create macOS Application Menu
        try:
            menubar = Menu(root)
            edit_menu = Menu(menubar, tearoff=0)
            
            edit_menu.add_command(label="Cut", accelerator="Cmd+X", command=lambda: cut_text(DummyEvent(root.focus_get())))
            edit_menu.add_command(label="Copy", accelerator="Cmd+C", command=lambda: copy_text(DummyEvent(root.focus_get())))
            edit_menu.add_command(label="Paste", accelerator="Cmd+V", command=lambda: paste_text(DummyEvent(root.focus_get())))
            edit_menu.add_command(label="Select All", accelerator="Cmd+A", command=lambda: select_all(DummyEvent(root.focus_get())))
            
            menubar.add_cascade(label="Edit", menu=edit_menu)
            root.config(menu=menubar)
        except Exception:
            pass


class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        setup_macos_shortcuts(self)
        self.set_window_icon()
        self.title("QR Generator Pro")
        self.geometry("1020x700")
        self.minsize(880, 600)
        self.configure(fg_color=BG)

    def set_window_icon(self):
        icon_paths = [
            # dev path
            os.path.join(os.path.dirname(__file__), "..", "icon.ico"),
            os.path.join(os.path.dirname(__file__), "..", "icon.png"),
            # PyInstaller bundled path
            os.path.join(getattr(sys, "_MEIPASS", ""), "icon.ico"),
            os.path.join(getattr(sys, "_MEIPASS", ""), "icon.png"),
        ]
        for p in icon_paths:
            if p and os.path.exists(p):
                try:
                    if p.endswith(".ico") and sys.platform == "win32":
                        self.iconbitmap(p)
                    else:
                        img = Image.open(p)
                        photo = ImageTk.PhotoImage(img)
                        self.iconphoto(True, photo)
                        self._icon_photo = photo  # Keep a reference!
                    break
                except Exception as e:
                    print(f"Failed to load icon from {p}: {e}")

        self.qr_fg = "#000000"
        self.qr_bg = "#FFFFFF"
        self.logo_path = None
        self.qr_img = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.topbar = TopNavBar(self, on_create_click=lambda: self._show_page("create"), on_history_click=lambda: self._show_page("history"))
        self.topbar.grid(row=0, column=0, sticky="ew")

        # Create Layout
        self.create_body = ctk.CTkFrame(self, fg_color=BG)
        self.create_body.grid_columnconfigure(0, weight=5)
        self.create_body.grid_columnconfigure(1, weight=4)
        self.create_body.grid_rowconfigure(0, weight=1)

        self.workspace = WorkspacePanel(self.create_body, app_controller=self)
        self.workspace.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        self.preview = PreviewPanel(self.create_body, app_controller=self)
        self.preview.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        # History Layout
        self.history_body = HistoryPanel(self, app_controller=self)

        self._show_page("create")
        self.after(200, lambda: self.request_generate(debounce=False))

    def _show_page(self, name):
        self.topbar.set_active(name)
        if name == "create":
            self.history_body.grid_forget()
            self.create_body.grid(row=1, column=0, sticky="nsew", padx=28, pady=20)
        else:
            self.create_body.grid_forget()
            self.history_body.grid(row=1, column=0, sticky="nsew", padx=28, pady=20)
            self.history_body.refresh()

    def request_generate(self, *args, debounce=True):
        if hasattr(self, "_generate_job") and self._generate_job is not None:
            self.after_cancel(self._generate_job)
            self._generate_job = None
            
        if debounce:
            self._generate_job = self.after(150, self._do_generate)
        else:
            self._do_generate()

    def _do_generate(self):
        self._generate_job = None
        data = self.workspace.get_data()
        shape = self.workspace.shape_seg.get()
        try:
            self.qr_img = QRManager.generate(data, shape, self.qr_fg, self.qr_bg, self.logo_path)
            self.preview.update_image(self.qr_img)
        except Exception as e:
            self.preview.set_error(str(e))

    def save_png(self):
        if not self.qr_img: return
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if path:
            self.qr_img.save(path, "PNG")
            self.preview.status_lbl.configure(text=f"Saved: {os.path.basename(path)}", text_color="#16A34A")
            HistoryManager.save_history(self.workspace.type_seg.get(), self.workspace.get_data(), self.qr_img)

    def save_svg(self):
        data = self.workspace.get_data()
        if not data:
            messagebox.showwarning("No data", "Enter data first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG", "*.svg")], initialfile="QR_Code.svg")
        if path:
            QRManager.generate_svg(data, path)
            HistoryManager.save_history(self.workspace.type_seg.get(), data, self.qr_img)

    def copy_image(self):
        success, msg = ClipboardManager.copy_image(self.qr_img)
        color = "#16A34A" if success else "#EF4444"
        self.preview.status_lbl.configure(text=msg, text_color=color)

    def print_image(self):
        messagebox.showinfo("Print", "Printing via system dialog.")
