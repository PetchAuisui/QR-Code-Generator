"""
QR CODE GENERATOR — LUXE EDITION
pip install qrcode[pil] pillow
"""

import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer,
    GappedSquareModuleDrawer, VerticalBarsDrawer, HorizontalBarsDrawer,
)
from PIL import Image, ImageTk
import os, subprocess, tempfile

# ── Palette ─────────────────────────────────────────────────────────
BG       = "#0D0D12"
PANEL    = "#13131A"
CARD     = "#1C1C27"
CARD2    = "#232330"
ACCENT   = "#8B5CF6"
ACCENT_H = "#A78BFA"
ACCENT_D = "#6D28D9"
TEAL     = "#2DD4BF"
TEAL_D   = "#0F766E"
TEXT     = "#F1EEF9"
TEXT2    = "#7C78A0"
TEXT3    = "#4A4868"
BORDER   = "#2A2A3D"
SUCCESS  = "#22C55E"
WARN     = "#F59E0B"
ERR      = "#EF4444"

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def pill(canvas, x1, y1, x2, y2, r, fill):
    canvas.create_arc(x1, y1, x1+2*r, y1+2*r, start=90,  extent=90, fill=fill, outline=fill)
    canvas.create_arc(x2-2*r, y1, x2, y1+2*r, start=0,   extent=90, fill=fill, outline=fill)
    canvas.create_arc(x1, y2-2*r, x1+2*r, y2, start=180, extent=90, fill=fill, outline=fill)
    canvas.create_arc(x2-2*r, y2-2*r, x2, y2, start=270, extent=90, fill=fill, outline=fill)
    canvas.create_rectangle(x1+r, y1, x2-r, y2, fill=fill, outline=fill)
    canvas.create_rectangle(x1, y1+r, x2, y2-r, fill=fill, outline=fill)


class PillButton(tk.Canvas):
    def __init__(self, parent, text, cmd=None,
                 w=200, h=48, r=12,
                 bg=ACCENT, hover=ACCENT_H, fg=TEXT, fs=11, **kw):
        super().__init__(parent, width=w, height=h,
                         bg=BG, highlightthickness=0, cursor="hand2")
        self.text, self.cmd, self.r = text, cmd, r
        self.fg, self.n, self.hv, self.fs = fg, bg, hover, fs
        self._draw(bg)
        self.bind("<Enter>",    lambda e: self._draw(hover))
        self.bind("<Leave>",    lambda e: self._draw(bg))
        self.bind("<Button-1>", lambda e: cmd and cmd())

    def _draw(self, bg):
        self.delete("all")
        w, h = int(self["width"]), int(self["height"])
        pill(self, 0, 0, w, h, self.r, bg)
        self.create_text(w//2, h//2, text=self.text,
                         fill=self.fg, font=("Helvetica", self.fs, "bold"))


class Swatch(tk.Canvas):
    def __init__(self, parent, color, on_pick, size=38):
        super().__init__(parent, width=size, height=size,
                         bg=CARD, highlightthickness=0, cursor="hand2")
        self.color, self.on_pick, self.s = color, on_pick, size
        self._draw()
        self.bind("<Button-1>", self._pick)

    def _draw(self):
        self.delete("all")
        s = self.s
        pill(self, 3, 3, s-3, s-3, 9, self.color)
        self.create_text(s//2, s//2, text="✎", fill="#888888", font=("Helvetica", 10))

    def set_color(self, c):
        self.color = c
        self._draw()

    def _pick(self, _):
        res = colorchooser.askcolor(color=self.color, title="เลือกสี")
        if res[1]:
            self.set_color(res[1])
            self.on_pick(res[1])


class QRApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("QR Code Generator")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.qr_fg, self.qr_bg = "#1C1C27", "#FFFFFF"
        self.qr_img = self.qr_photo = None
        self.shape_var = tk.StringVar(value="rounded")
        self.ec_var    = tk.StringVar(value="M")
        self.box_v     = tk.IntVar(value=18)
        self.brd_v     = tk.IntVar(value=4)
        self._build()
        self.after(150, self._gen)

    # ────────────────────────────────────────────────────────────────
    def _build(self):
        # TOP BAR
        top = tk.Frame(self, bg=PANEL, height=54)
        top.pack(fill="x")
        top.pack_propagate(False)
        tk.Label(top, text=" ◼ QR", bg=PANEL, fg=ACCENT_H,
                 font=("Helvetica", 15, "bold")).pack(side="left", padx=(20, 0))
        tk.Label(top, text=" Code Generator", bg=PANEL, fg=TEXT,
                 font=("Helvetica", 15, "bold")).pack(side="left")

        # Status chip (top-right)
        self.status_var = tk.StringVar(value="⏳ พร้อมใช้งาน")
        self.status_lbl = tk.Label(top, textvariable=self.status_var,
                                   bg=CARD2, fg=TEXT2,
                                   font=("Helvetica", 10),
                                   padx=14, pady=3)
        self.status_lbl.pack(side="right", padx=20, pady=10)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        # BODY
        body = tk.Frame(self, bg=BG)
        body.pack(padx=22, pady=18)

        self._col_left(body)
        tk.Frame(body, bg=BORDER, width=1).pack(side="left", fill="y", padx=18)
        self._col_right(body)

    # ── LEFT ──────────────────────────────────────────────────────
    def _col_left(self, parent):
        col = tk.Frame(parent, bg=BG, width=360)
        col.pack(side="left", fill="y")
        col.pack_propagate(False)

        # Input
        self._hdr(col, "📝  ข้อความ / URL")
        wrap = tk.Frame(col, bg=CARD2, highlightbackground=ACCENT, highlightthickness=1)
        wrap.pack(fill="x", pady=(0, 18))
        self.txt = tk.StringVar(value="https://example.com")
        entry = tk.Entry(wrap, textvariable=self.txt,
                 bg=CARD2, fg=TEXT, font=("Helvetica", 13),
                 insertbackground=ACCENT_H,
                 relief="flat", bd=12)
        entry.pack(fill="x")
        entry.bind("<KeyRelease>", lambda e: self._gen())

        # Shape
        self._hdr(col, "◈  รูปทรงโมดูล")
        sg = tk.Frame(col, bg=BG)
        sg.pack(fill="x", pady=(0, 18))
        shapes = [("◼","square"),("◉","rounded"),("●","circle"),
                  ("⬜","gapped"),("❙","vertical"),("═","horizontal")]
        self._shape_cells = {}
        for i, (icon, val) in enumerate(shapes):
            self._make_shape_cell(sg, icon, val, i)

        # Colors
        self._hdr(col, "🎨  สี")
        clr_card = tk.Frame(col, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        clr_card.pack(fill="x", pady=(0, 18), ipadx=10, ipady=10)

        clr_inner = tk.Frame(clr_card, bg=CARD)
        clr_inner.pack(fill="x", padx=10)

        # FG
        fg_f = tk.Frame(clr_inner, bg=CARD)
        fg_f.pack(side="left", padx=(0, 20))
        tk.Label(fg_f, text="สี QR", bg=CARD, fg=TEXT2, font=("Helvetica", 10)).pack(anchor="w", pady=(0,5))
        self.fg_sw  = Swatch(fg_f, self.qr_fg, self._set_fg)
        self.fg_sw.pack()
        self.fg_lbl = tk.Label(fg_f, text=self.qr_fg, bg=CARD, fg=TEXT3, font=("Helvetica", 8))
        self.fg_lbl.pack(pady=(3,0))

        # BG
        bg_f = tk.Frame(clr_inner, bg=CARD)
        bg_f.pack(side="left", padx=(0, 20))
        tk.Label(bg_f, text="พื้นหลัง", bg=CARD, fg=TEXT2, font=("Helvetica", 10)).pack(anchor="w", pady=(0,5))
        self.bg_sw  = Swatch(bg_f, self.qr_bg, self._set_bg)
        self.bg_sw.pack()
        self.bg_lbl = tk.Label(bg_f, text=self.qr_bg, bg=CARD, fg=TEXT3, font=("Helvetica", 8))
        self.bg_lbl.pack(pady=(3,0))

        # Presets
        pre_f = tk.Frame(clr_inner, bg=CARD)
        pre_f.pack(side="left")
        tk.Label(pre_f, text="Presets", bg=CARD, fg=TEXT2, font=("Helvetica", 10)).pack(anchor="w", pady=(0,5))
        pg = tk.Frame(pre_f, bg=CARD)
        pg.pack()
        for i, (f, b) in enumerate([
            ("#1C1C27","#FFFFFF"), ("#7C3AED","#EDE9FE"),
            ("#0F766E","#CCFBF1"), ("#1D4ED8","#EFF6FF"),
            ("#9D174D","#FCE7F3"), ("#111827","#F9FAFB"),
        ]):
            c = tk.Canvas(pg, width=22, height=22, bg=CARD,
                          highlightthickness=0, cursor="hand2")
            c.grid(row=i//3, column=i%3, padx=2, pady=2)
            pill(c, 2, 2, 20, 20, 6, f)
            c.bind("<Button-1>", lambda e, ff=f, bb=b: self._preset(ff, bb))

        # Sliders
        self._hdr(col, "⚙  ขนาด")
        sl = tk.Frame(col, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        sl.pack(fill="x", pady=(0, 18), ipadx=10, ipady=6)
        self._slider(sl, "Box size", self.box_v,  5, 30)
        self._slider(sl, "Border",   self.brd_v,  0, 10)

        # Error correction
        self._hdr(col, "🔧  Error Correction")
        ec = tk.Frame(col, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        ec.pack(fill="x", pady=(0, 4), ipadx=10, ipady=10)
        ec_row = tk.Frame(ec, bg=CARD)
        ec_row.pack(padx=10)
        for val, pct in [("L","7%"),("M","15%"),("Q","25%"),("H","30%")]:
            f = tk.Frame(ec_row, bg=CARD)
            f.pack(side="left", padx=8)
            tk.Radiobutton(f, variable=self.ec_var, value=val,
                           bg=CARD, activebackground=CARD,
                           selectcolor=CARD2, command=self._gen).pack()
            tk.Label(f, text=val, bg=CARD, fg=TEXT,
                     font=("Helvetica", 11, "bold")).pack()
            tk.Label(f, text=pct, bg=CARD, fg=TEXT3,
                     font=("Helvetica", 8)).pack()

    # ── RIGHT ─────────────────────────────────────────────────────
    def _col_right(self, parent):
        col = tk.Frame(parent, bg=BG)
        col.pack(side="left")

        self.canvas = tk.Canvas(col, width=460, height=460,
                                bg=CARD, highlightbackground=BORDER,
                                highlightthickness=1)
        self.canvas.pack()
        self.canvas.create_text(230, 230, text="QR Preview",
                                fill=TEXT3, font=("Helvetica", 14))

        self.size_lbl = tk.Label(col, text="", bg=BG, fg=TEXT3,
                                 font=("Helvetica", 9))
        self.size_lbl.pack(pady=(6, 0))

        btn_row = tk.Frame(col, bg=BG)
        btn_row.pack(fill="x", pady=(14, 0))
        PillButton(btn_row, "⟳  สร้างใหม่", self._gen,
                   w=138, h=46, bg=ACCENT, hover=ACCENT_H).pack(side="left", padx=(0,10))
        PillButton(btn_row, "💾  บันทึก PNG", self._save,
                   w=152, h=46, bg=TEAL_D, hover=TEAL).pack(side="left", padx=(0,10))
        PillButton(btn_row, "📋  Copy", self._copy,
                   w=100, h=46, bg=CARD2, hover=CARD, fg=TEXT2).pack(side="left")

    # ── Widget helpers ────────────────────────────────────────────
    def _hdr(self, parent, text):
        tk.Label(parent, text=text, bg=BG, fg=ACCENT_H,
                 font=("Helvetica", 10, "bold")).pack(anchor="w", pady=(0, 6))

    def _slider(self, parent, label, var, lo, hi):
        row = tk.Frame(parent, bg=CARD)
        row.pack(fill="x", padx=10, pady=3)
        tk.Label(row, text=label, bg=CARD, fg=TEXT2,
                 font=("Helvetica", 10), width=9, anchor="w").pack(side="left")
        tk.Label(row, textvariable=var, bg=CARD, fg=ACCENT_H,
                 font=("Helvetica", 10, "bold"), width=3).pack(side="right")
        tk.Scale(row, variable=var, from_=lo, to=hi,
                 orient="horizontal", showvalue=False,
                 bg=CARD, troughcolor=CARD2,
                 activebackground=ACCENT,
                 highlightthickness=0,
                 command=lambda e: self._gen()).pack(side="left", fill="x", expand=True)

    def _make_shape_cell(self, parent, icon, val, i):
        c = tk.Canvas(parent, width=54, height=54,
                      bg=BG, highlightthickness=0, cursor="hand2")
        c.grid(row=i//3, column=i%3, padx=4, pady=4)
        c._val, c._icon = val, icon
        self._shape_cells[val] = c

        def draw(active):
            c.delete("all")
            pill(c, 1, 1, 53, 53, 12, ACCENT if active else CARD)
            c.create_text(27, 22, text=icon,
                          fill=TEXT if active else TEXT2, font=("Helvetica", 13))
            c.create_text(27, 40, text=val[:3],
                          fill=TEXT if active else TEXT3, font=("Helvetica", 8))

        def click(_):
            self.shape_var.set(val)
            for v, cv in self._shape_cells.items():
                cv._draw_fn(v == val)
            self._gen()

        def enter(_):
            if val != self.shape_var.get():
                c.delete("all")
                pill(c, 1, 1, 53, 53, 12, CARD2)
                c.create_text(27, 22, text=icon, fill=TEXT2, font=("Helvetica", 13))
                c.create_text(27, 40, text=val[:3], fill=TEXT3, font=("Helvetica", 8))

        def leave(_):
            draw(val == self.shape_var.get())

        c._draw_fn = draw
        draw(val == self.shape_var.get())
        c.bind("<Button-1>", click)
        c.bind("<Enter>", enter)
        c.bind("<Leave>", leave)

    # ── Color callbacks ───────────────────────────────────────────
    def _set_fg(self, c):
        self.qr_fg = c; self.fg_lbl.config(text=c); self._gen()

    def _set_bg(self, c):
        self.qr_bg = c; self.bg_lbl.config(text=c); self._gen()

    def _preset(self, fg, bg):
        self.qr_fg, self.qr_bg = fg, bg
        self.fg_sw.set_color(fg); self.bg_sw.set_color(bg)
        self.fg_lbl.config(text=fg); self.bg_lbl.config(text=bg)
        self._gen()

    # ── Generate ──────────────────────────────────────────────────
    def _drawer(self):
        return {"square": SquareModuleDrawer(), "rounded": RoundedModuleDrawer(),
                "circle": CircleModuleDrawer(), "gapped": GappedSquareModuleDrawer(),
                "vertical": VerticalBarsDrawer(), "horizontal": HorizontalBarsDrawer(),
                }.get(self.shape_var.get(), RoundedModuleDrawer())

    def _ec(self):
        return {"L": qrcode.constants.ERROR_CORRECT_L, "M": qrcode.constants.ERROR_CORRECT_M,
                "Q": qrcode.constants.ERROR_CORRECT_Q, "H": qrcode.constants.ERROR_CORRECT_H,
                }[self.ec_var.get()]

    def _gen(self, *_):
        data = self.txt.get().strip()
        if not data:
            return self._status("⚠  กรุณาใส่ข้อความ", WARN)
        try:
            qr = qrcode.QRCode(error_correction=self._ec(),
                               box_size=self.box_v.get(),
                               border=self.brd_v.get())
            qr.add_data(data); qr.make(fit=True)
            img = qr.make_image(image_factory=StyledPilImage,
                                module_drawer=self._drawer()).convert("RGBA")
            fg, bg = hex_rgb(self.qr_fg), hex_rgb(self.qr_bg)
            px = img.load()
            for x in range(img.width):
                for y in range(img.height):
                    r, *_ = px[x, y]
                    px[x, y] = (*fg, 255) if r < 128 else (*bg, 255)
            self.qr_img = img
            disp = img.copy(); disp.thumbnail((458, 458), RESAMPLE)
            self.qr_photo = ImageTk.PhotoImage(disp)
            self.canvas.delete("all")
            self.canvas.create_image(230, 230, image=self.qr_photo)
            self.size_lbl.config(text=f"{img.width} × {img.height} px  ·  version {qr.version}")
            self._status(f"✅  สร้างสำเร็จ  ·  {len(data)} ตัวอักษร  ·  version {qr.version}", SUCCESS)
        except Exception as ex:
            self._status(f"❌  {ex}", ERR)

    def _status(self, msg, color=TEXT2):
        self.status_var.set(msg); self.status_lbl.config(fg=color)

    def _save(self):
        if not self.qr_img:
            return messagebox.showwarning("ยังไม่มีรูป", "กรุณาสร้าง QR ก่อน")
        path = filedialog.asksaveasfilename(defaultextension=".png",
            filetypes=[("PNG","*.png"),("All","*.*")],
            initialfile="qrcode.png", title="บันทึก QR Code")
        if path:
            self.qr_img.save(path)
            self._status(f"💾  บันทึก: {os.path.basename(path)}", TEAL)

    def _copy(self):
        if not self.qr_img:
            return messagebox.showwarning("ยังไม่มีรูป", "กรุณาสร้าง QR ก่อน")
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
            self.qr_img.save(tmp.name); tmp.close()
            if os.name == "nt":
                subprocess.run(["clip"], stdin=open(tmp.name,"rb"), check=True)
            else:
                subprocess.run(["osascript", "-e",
                    f'set the clipboard to (read POSIX file "{tmp.name}" as «class PNGf»)'],
                    check=True)
            self._status("📋  คัดลอกแล้ว", TEAL)
        except Exception:
            self._status("⚠  Copy ไม่สำเร็จ — ลองบันทึกแทน", WARN)


if __name__ == "__main__":
    app = QRApp()
    app.update_idletasks()
    sw, sh = app.winfo_screenwidth(), app.winfo_screenheight()
    w,  h  = app.winfo_reqwidth(),    app.winfo_reqheight()
    app.geometry(f"+{(sw-w)//2}+{(sh-h)//2}")
    app.mainloop()