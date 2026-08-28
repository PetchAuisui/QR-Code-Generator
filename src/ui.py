import os
import sys
import subprocess
import tempfile
import atexit
from tkinter import colorchooser, filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import shutil

from .config import *
from .core import QRManager, ClipboardManager
from .widgets import PillSegButton, AccordionCard

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS


class TopNavBar(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=0, border_width=0, height=76, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.grid_propagate(False)

        brand = ctk.CTkFrame(self, fg_color="transparent")
        brand.grid(row=0, column=0, padx=32, pady=14, sticky="w")
        logo = ctk.CTkLabel(brand, text="QR", width=42, height=42, corner_radius=12,
                            fg_color=BLUE, text_color="#ffffff",
                            font=ctk.CTkFont(size=14, weight="bold"))
        logo.grid(row=0, column=0, rowspan=2, padx=(0, 12))
        ctk.CTkLabel(brand, text="QR Studio", text_color=TEXT_DK,
                     font=ctk.CTkFont(size=18, weight="bold"), anchor="w").grid(row=0, column=1, sticky="sw")
        ctk.CTkLabel(brand, text="Create, customize and export", text_color=TEXT_LT,
                     font=ctk.CTkFont(size=11), anchor="w").grid(row=1, column=1, sticky="nw")

        ctk.CTkLabel(self, text="Live generator", text_color=TEXT_MD, fg_color="#f1f5f9",
                     corner_radius=16, padx=14, pady=7,
                     font=ctk.CTkFont(size=11, weight="bold")).grid(row=0, column=1, padx=32, sticky="e")

        ctk.CTkFrame(self, fg_color=BORDER, height=1, corner_radius=0).grid(
            row=1, column=0, columnspan=2, sticky="ew"
        )

    def set_active(self, page_name):
        pass


class WorkspacePanel(ctk.CTkScrollableFrame):
    def __init__(self, master, app_controller, **kwargs):
        super().__init__(master, fg_color=BG, scrollbar_button_color=BG, scrollbar_button_hover_color=BORDER, **kwargs)
        # Force canvas bg color — CTkScrollableFrame's internal canvas can default
        # to the OS system color (white/grey) on Windows if not set explicitly.
        if hasattr(self, "_canvas"):
            self._canvas.configure(bg=BG)
        self.app = app_controller
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(self, text="Create your QR code", text_color=TEXT_DK,
                     font=ctk.CTkFont(size=24, weight="bold"), anchor="w").grid(
            row=0, column=0, sticky="ew", padx=2
        )
        ctk.CTkLabel(self, text="Choose a content type, then make it yours.", text_color=TEXT_MD,
                     font=ctk.CTkFont(size=12), anchor="w").grid(
            row=1, column=0, sticky="ew", padx=2, pady=(3, 18)
        )

        self.type_seg = PillSegButton(self, values=["URL", "Text", "Email", "WiFi"], command=self._on_type_change, height=46)
        self.type_seg.grid(row=2, column=0, sticky="ew", padx=2, pady=(0, 12))

        self.input_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=14, border_width=1, border_color=BORDER)
        self.input_card.grid(row=3, column=0, sticky="ew", padx=2, pady=(0, 20))
        self.input_card.grid_columnconfigure(0, weight=1)

        self.input_widgets = {}
        self._build_input_fields()

        self.acc_colors = AccordionCard(self, title="Colors", icon="colors", expanded=False)
        ctk.CTkLabel(self, text="CUSTOMIZE", text_color=TEXT_LT,
                     font=ctk.CTkFont(size=10, weight="bold"), anchor="w").grid(
            row=4, column=0, sticky="ew", padx=4, pady=(0, 8)
        )

        self.acc_colors.grid(row=5, column=0, sticky="ew", padx=2, pady=(0, 10))
        self._build_colors_content()

        self.acc_design = AccordionCard(self, title="Design", icon="design", expanded=False)
        self.acc_design.grid(row=6, column=0, sticky="ew", padx=2, pady=(0, 10))
        self._build_design_content()

        self.acc_logo = AccordionCard(self, title="Logo", icon="logo", expanded=False)
        self.acc_logo.grid(row=7, column=0, sticky="ew", padx=2, pady=(0, 16))
        self._build_logo_content()

    def _mouse_wheel_all(self, event):
        """Scroll whenever the pointer is anywhere over this workspace."""
        try:
            pointer_x, pointer_y = self.winfo_pointerxy()
            left = self._parent_canvas.winfo_rootx()
            top = self._parent_canvas.winfo_rooty()
            right = left + self._parent_canvas.winfo_width()
            bottom = top + self._parent_canvas.winfo_height()
            if not (left <= pointer_x < right and top <= pointer_y < bottom):
                return

            if self._parent_canvas.yview() == (0.0, 1.0):
                return "break"

            if sys.platform == "darwin":
                amount = -int(event.delta)
            elif sys.platform.startswith("win"):
                amount = -int(event.delta / 120)
            else:
                amount = -int(event.delta)

            if amount == 0 and event.delta:
                amount = -1 if event.delta > 0 else 1
            self._parent_canvas.yview_scroll(amount, "units")
            return "break"
        except Exception:
            return

    def _build_input_fields(self):
        pad = dict(padx=16, pady=(0, 16))
        parent = self.input_card

        # URL
        f_url = ctk.CTkFrame(parent, fg_color="transparent")
        f_url.grid(row=0, column=0, sticky="ew")
        f_url.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_url, text="Enter URL", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.entry_url = ctk.CTkEntry(f_url, placeholder_text="https://example.com", height=48, corner_radius=10, border_width=1, border_color=BORDER, fg_color="#f8fafc", text_color=TEXT_DK, font=ctk.CTkFont(size=14))
        self.entry_url.insert(0, "https://qrpro.io/workspace")
        self.entry_url.grid(row=1, column=0, sticky="ew", **pad)
        self.entry_url.bind("<KeyRelease>", lambda e: self.app.request_generate())
        self.input_widgets["URL"] = f_url

        # Text
        f_txt = ctk.CTkFrame(parent, fg_color="transparent")
        f_txt.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_txt, text="Enter Text", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.entry_txt = ctk.CTkTextbox(f_txt, height=92, corner_radius=10, border_width=1, border_color=BORDER, fg_color="#f8fafc", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        # Enable Tk's native undo stack; macOS shortcuts are installed below.
        self.entry_txt._textbox.configure(undo=True, autoseparators=True, maxundo=-1)
        self.entry_txt.grid(row=1, column=0, sticky="ew", **pad)
        self.entry_txt.bind("<KeyRelease>", lambda e: self.app.request_generate())
        self.input_widgets["Text"] = f_txt

        # Email
        f_eml = ctk.CTkFrame(parent, fg_color="transparent")
        f_eml.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_eml, text="Email Address", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.entry_eml = ctk.CTkEntry(f_eml, placeholder_text="hello@example.com", height=44, corner_radius=10, border_width=1, border_color=BORDER, fg_color="#f8fafc", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        self.entry_eml.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.entry_eml.bind("<KeyRelease>", lambda e: self.app.request_generate())
        ctk.CTkLabel(f_eml, text="Subject", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 4))
        self.entry_sub = ctk.CTkEntry(f_eml, placeholder_text="Subject line...", height=44, corner_radius=10, border_width=1, border_color=BORDER, fg_color="#f8fafc", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        self.entry_sub.grid(row=3, column=0, sticky="ew", **pad)
        self.entry_sub.bind("<KeyRelease>", lambda e: self.app.request_generate())
        self.input_widgets["Email"] = f_eml

        # WiFi
        f_wifi = ctk.CTkFrame(parent, fg_color="transparent")
        f_wifi.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(f_wifi, text="Network Name (SSID)", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))
        self.entry_ssid = ctk.CTkEntry(f_wifi, placeholder_text="MyNetwork", height=44, corner_radius=10, border_width=1, border_color=BORDER, fg_color="#f8fafc", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
        self.entry_ssid.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 8))
        self.entry_ssid.bind("<KeyRelease>", lambda e: self.app.request_generate())
        ctk.CTkLabel(f_wifi, text="Password", text_color=TEXT_MD, font=ctk.CTkFont(size=12)).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 4))
        self.entry_pass = ctk.CTkEntry(f_wifi, show="*", placeholder_text="Password", height=44, corner_radius=10, border_width=1, border_color=BORDER, fg_color="#f8fafc", text_color=TEXT_DK, font=ctk.CTkFont(size=13))
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
        self.logo_btn = ctk.CTkButton(parent, text="Upload Logo\nPNG  SVG  JPG", fg_color="#F8FAFF", text_color=TEXT_LT, hover_color="#EEF2FF", border_width=1, border_color=BORDER, height=80, corner_radius=10, command=self._upload_logo)
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
        super().__init__(master, fg_color="#0f172a", corner_radius=20, border_width=0, **kwargs)
        self.app = app_controller
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        h = ctk.CTkFrame(self, fg_color="transparent")
        h.grid(row=0, column=0, sticky="ew", padx=28, pady=(24, 18))
        title_wrap = ctk.CTkFrame(h, fg_color="transparent")
        title_wrap.pack(side="left")
        ctk.CTkLabel(title_wrap, text="Your QR code", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="#ffffff", anchor="w").pack(anchor="w")
        ctk.CTkLabel(title_wrap, text="Updates instantly as you type", font=ctk.CTkFont(size=11),
                     text_color="#94a3b8", anchor="w").pack(anchor="w", pady=(2, 0))
        ctk.CTkLabel(h, text="●  LIVE", fg_color="#153b35", text_color="#86efac",
                     corner_radius=14, padx=12, pady=6,
                     font=ctk.CTkFont(size=10, weight="bold")).pack(side="right")

        disp_outer = ctk.CTkFrame(self, fg_color="#ffffff", corner_radius=18, border_width=0)
        disp_outer.grid(row=1, column=0, sticky="nsew", padx=28, pady=(0, 22))
        disp_outer.grid_rowconfigure(0, weight=1)
        disp_outer.grid_columnconfigure(0, weight=1)

        disp_inner = ctk.CTkFrame(disp_outer, fg_color="transparent")
        disp_inner.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        disp_inner.grid_rowconfigure(0, weight=1)
        disp_inner.grid_columnconfigure(0, weight=1)

        self.qr_display = ctk.CTkLabel(disp_inner, text="No Data", font=ctk.CTkFont(size=14), text_color=TEXT_LT)
        self.qr_display.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=2, column=0, sticky="ew", padx=28, pady=(0, 12))
        btn_row.grid_columnconfigure(0, weight=1)
        btn_row.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row, text="↓  Save PNG", fg_color=BLUE, hover_color=BLUE_DK, text_color="#ffffff", height=50, corner_radius=12, font=ctk.CTkFont(size=14, weight="bold"), command=self.app.save_png).grid(row=0, column=0, padx=(0, 7), sticky="ew")
        ctk.CTkButton(btn_row, text="Save SVG", fg_color="#1e293b", hover_color="#334155", text_color="#e2e8f0", border_width=1, border_color="#334155", height=50, corner_radius=12, font=ctk.CTkFont(size=14, weight="bold"), command=self.app.save_svg).grid(row=0, column=1, padx=(7, 0), sticky="ew")

        btn_row2 = ctk.CTkFrame(self, fg_color="transparent")
        btn_row2.grid(row=3, column=0, sticky="ew", padx=28, pady=(0, 24))
        btn_row2.grid_columnconfigure(0, weight=1)
        btn_row2.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(btn_row2, text="▣  Copy image", fg_color="transparent", hover_color="#1e293b", text_color="#cbd5e1", border_width=0, height=40, corner_radius=10, font=ctk.CTkFont(size=12), command=self.app.copy_image).grid(row=0, column=0, padx=(0, 7), sticky="ew")
        ctk.CTkButton(btn_row2, text="Print", fg_color="transparent", hover_color="#1e293b", text_color="#cbd5e1", border_width=0, height=40, corner_radius=10, font=ctk.CTkFont(size=12), command=self.app.print_image).grid(row=0, column=1, padx=(7, 0), sticky="ew")
        # End of PreviewPanel layout

    def update_image(self, img):
        if not img:
            self.qr_display.configure(image="", text="Waiting for input...")
            return

        thumb = img.copy()
        thumb.thumbnail((250, 250), RESAMPLE)
        ctk_img = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=(thumb.width, thumb.height))
        self.qr_display.configure(image=ctk_img, text="")

    def set_error(self, err_msg):
        from tkinter import messagebox
        messagebox.showerror("Error", err_msg)
        self.qr_display.configure(image="", text="Error generating QR code")

def setup_macos_shortcuts(root):
    if sys.platform == "darwin":
        from tkinter import Menu

        class DummyEvent:
            def __init__(self, widget):
                self.widget = widget

        def _is_text(widget):
            return widget.winfo_class() == "Text"

        def _remember_entry(widget):
            if _is_text(widget):
                return
            value = widget.get()
            history = getattr(widget, "_qr_undo_history", None)
            if history is None:
                history = []
                widget._qr_undo_history = history
            if not history or history[-1] != value:
                history.append(value)
                if len(history) > 200:
                    del history[0]

        def remember_entry_after_key(event):
            widget = event.widget
            root.after_idle(lambda: _remember_entry(widget))

        def undo_text(event):
            if not event or not event.widget:
                return "break"
            widget = event.widget
            try:
                if _is_text(widget):
                    widget.edit_undo()
                else:
                    _remember_entry(widget)
                    history = getattr(widget, "_qr_undo_history", [])
                    if len(history) > 1:
                        history.pop()
                        previous = history[-1]
                        widget.delete(0, "end")
                        widget.insert(0, previous)
                        widget.icursor("end")
            except Exception:
                pass
            return "break"

        def select_all(event):
            if not event or not event.widget:
                return "break"
            widget = event.widget
            if _is_text(widget):
                widget.tag_add("sel", "1.0", "end-1c")
                widget.mark_set("insert", "end-1c")
            else:
                widget.selection_range(0, "end")
                widget.icursor("end")
            return "break"

        def select_all_on_double_click(event):
            # Run after Tk's built-in double-click handler so its word selection
            # cannot replace our full-field selection.
            root.after_idle(lambda: select_all(DummyEvent(event.widget)))
            return "break"

        def copy_text(event):
            if not event or not event.widget: return "break"
            widget = event.widget
            try:
                if _is_text(widget):
                    text = widget.get("sel.first", "sel.last")
                else:
                    first = widget.index("sel.first")
                    last = widget.index("sel.last")
                    text = widget.get()[first:last]
                widget.clipboard_clear()
                widget.clipboard_append(text)
            except Exception:
                pass
            return "break"

        def cut_text(event):
            if not event or not event.widget: return "break"
            widget = event.widget
            _remember_entry(widget)
            copy_text(event)
            try:
                widget.delete("sel.first", "sel.last")
            except Exception:
                pass
            return "break"

        def paste_text(event):
            if not event or not event.widget: return "break"
            widget = event.widget
            _remember_entry(widget)
            try:
                text = widget.clipboard_get()
                try:
                    widget.delete("sel.first", "sel.last")
                except Exception:
                    pass
                widget.insert("insert", text)
            except Exception:
                pass
            return "break"

        # macOS virtual key codes identify the physical A/X/C/V keys and do not
        # change when the active keyboard language/layout changes.
        command_keycodes = {
            0: select_all,   # A
            6: undo_text,    # Z
            7: cut_text,     # X
            8: copy_text,    # C
            9: paste_text,   # V
        }
        command_keysyms = {
            "a": select_all,
            "z": undo_text,
            "x": cut_text,
            "c": copy_text,
            "v": paste_text,
            "Thai_fofan": select_all,
            "Thai_phophung": undo_text,
            "Thai_popla": cut_text,
            "Thai_saraae": copy_text,
            "Thai_oang": paste_text,
        }

        def command_by_physical_key(event):
            handler = command_keycodes.get(event.keycode)
            if handler is None:
                handler = command_keysyms.get(event.keysym)
            if handler:
                return handler(event)

        for widget_class in ("Entry", "Text"):
            root.bind_class(widget_class, "<Command-KeyPress>", command_by_physical_key)
            root.bind_class(widget_class, "<Double-Button-1>", select_all_on_double_click)
        root.bind_class("Entry", "<KeyPress>", remember_entry_after_key, add="+")
        root.bind_class("Entry", "<FocusIn>", lambda event: _remember_entry(event.widget), add="+")

        # Tk on some macOS/input-method combinations reports the translated
        # Thai keysym but does not preserve the usual macOS virtual keycode.
        # Bind those physical Kedmanee keys at the application level as well.
        # Using bind_all also covers CustomTkinter's internal Entry/Text widgets.
        layout_shortcuts = {
            "<Command-KeyPress-Thai_fofan>": select_all,   # Cmd+A
            "<Command-KeyPress-Thai_phophung>": undo_text, # Cmd+Z
            "<Command-KeyPress-Thai_popla>": cut_text,     # Cmd+X
            "<Command-KeyPress-Thai_saraae>": copy_text,   # Cmd+C
            "<Command-KeyPress-Thai_oang>": paste_text,    # Cmd+V
        }
        for sequence, handler in layout_shortcuts.items():
            root.bind_all(sequence, handler, add="+")

        # Create macOS Application Menu
        try:
            menubar = Menu(root)
            edit_menu = Menu(menubar, tearoff=0)

            edit_menu.add_command(label="Undo", accelerator="Cmd+Z", command=lambda: undo_text(DummyEvent(root.focus_get())))
            edit_menu.add_separator()
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
        self.title("QR Studio")
        self.geometry("1120x760")
        self.minsize(960, 680)
        self.configure(fg_color=BG)

    def set_window_icon(self):
        # ── Windows: tell the shell this is a standalone app (not python.exe) ──
        # Without this, the Taskbar always shows the Python icon even when
        # iconbitmap() succeeds for the window chrome.
        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                    "QRGeneratorPro.App.1"
                )
            except Exception:
                pass

        icon_paths = [
            # macOS-specific source uses the standard transparent safe area
            *([os.path.join(os.path.dirname(__file__), "..", "icon_macos.png")]
              if sys.platform == "darwin" else []),
            # dev path — prefer .ico on Windows, .png elsewhere
            os.path.join(os.path.dirname(__file__), "..", "icon.ico"),
            os.path.join(os.path.dirname(__file__), "..", "icon.png"),
            # PyInstaller bundled path
            *([os.path.join(getattr(sys, "_MEIPASS", ""), "icon_macos.png")]
              if sys.platform == "darwin" else []),
            os.path.join(getattr(sys, "_MEIPASS", ""), "icon.ico"),
            os.path.join(getattr(sys, "_MEIPASS", ""), "icon.png"),
        ]
        for p in icon_paths:
            p = os.path.normpath(p)
            if os.path.exists(p):
                try:
                    if sys.platform == "win32":
                        # iconbitmap works for both window chrome AND taskbar on Windows
                        if p.endswith(".ico"):
                            self.iconbitmap(p)
                        else:
                            # Convert PNG → ICO on the fly then set
                            from PIL import Image as _Img
                            import tempfile, atexit
                            tmp = tempfile.NamedTemporaryFile(suffix=".ico", delete=False)
                            tmp.close()
                            _Img.open(p).save(tmp.name, format="ICO",
                                              sizes=[(256,256),(128,128),(64,64),(48,48),(32,32),(16,16)])
                            self.iconbitmap(tmp.name)
                            atexit.register(lambda f=tmp.name: os.path.exists(f) and os.remove(f))
                    else:
                        img = Image.open(p)
                        photo = ImageTk.PhotoImage(img)
                        self.iconphoto(True, photo)
                        self._icon_photo = photo  # Keep a reference to prevent GC!
                    break
                except Exception as e:
                    print(f"Failed to load icon from {p}: {e}")

        self.qr_fg = "#000000"
        self.qr_bg = "#FFFFFF"
        self.logo_path = None
        self.qr_img = None

        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.topbar = TopNavBar(self)
        self.topbar.grid(row=0, column=0, sticky="ew")

        # Create Layout
        self.create_body = ctk.CTkFrame(self, fg_color=BG)
        self.create_body.grid_columnconfigure(0, weight=4, minsize=390)
        self.create_body.grid_columnconfigure(1, weight=6, minsize=490)
        self.create_body.grid_rowconfigure(0, weight=1)

        self.workspace = WorkspacePanel(self.create_body, app_controller=self)
        self.workspace.grid(row=0, column=0, sticky="nsew", padx=(0, 14))

        self.preview = PreviewPanel(self.create_body, app_controller=self)
        self.preview.grid(row=0, column=1, sticky="nsew", padx=(14, 0))

        self._do_initial_generate()
        self.after(200, lambda: self.request_generate(debounce=False))

    def _do_initial_generate(self):
        """Show the create body on startup."""
        self.create_body.grid(row=1, column=0, sticky="nsew", padx=32, pady=(24, 28))

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
            messagebox.showinfo("Saved", f"QR code saved successfully:\n{os.path.basename(path)}")

    def save_svg(self):
        data = self.workspace.get_data()
        if not data:
            messagebox.showwarning("No data", "Enter data first.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG", "*.svg")], initialfile="QR_Code.svg")
        if path:
            QRManager.generate_svg(data, path)

    def copy_image(self):
        success, msg = ClipboardManager.copy_image(self.qr_img)
        if success:
            messagebox.showinfo("Copied", msg)
        else:
            messagebox.showerror("Clipboard Error", msg)

    def print_image(self):
        if not self.qr_img:
            messagebox.showwarning("No image", "Generate a QR code first.")
            return
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            tmp.close()
            self.qr_img.save(tmp.name, "PNG")
            atexit.register(lambda f=tmp.name: os.path.exists(f) and os.remove(f))

            if sys.platform == "win32":
                # Opens Windows print dialog via the default image viewer
                os.startfile(tmp.name, "print")
            elif sys.platform == "darwin":
                # Opens in Preview — user can Cmd+P to print
                subprocess.Popen(["open", "-a", "Preview", tmp.name])
            else:
                # Linux: send directly to default printer
                subprocess.Popen(["lp", tmp.name])
        except Exception as e:
            messagebox.showerror("Print Error", str(e))
