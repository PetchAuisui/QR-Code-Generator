import customtkinter as ctk
import tkinter as tk
from .config import BLUE, BLUE_DK, CARD_BG, BORDER, TEXT_DK, TEXT_MD, TEXT_LT


class VectorIcon(tk.Canvas):
    """Small semantic icon drawn with native Tk vector primitives."""

    def __init__(self, master, kind, size=28):
        super().__init__(
            master,
            width=size,
            height=size,
            bg=CARD_BG,
            highlightthickness=0,
            borderwidth=0,
            relief="flat",
        )
        self._draw(kind)

    def _draw(self, kind):
        if kind == "colors":
            self.create_oval(2, 10, 16, 24, fill="#3B82F6", outline="")
            self.create_oval(10, 2, 24, 16, fill="#F04438", outline="")
            self.create_oval(10, 12, 24, 26, fill="#22B573", outline="")
        elif kind == "design":
            for x, y in ((3, 3), (15, 3), (3, 15), (15, 15)):
                self.create_rectangle(x, y, x + 9, y + 9, fill=BLUE, outline="")
        elif kind == "logo":
            self.create_rectangle(2, 4, 26, 24, outline=BLUE, width=2)
            self.create_oval(6, 7, 11, 12, fill=BLUE, outline="")
            self.create_line(4, 21, 11, 14, 16, 19, 20, 15, 25, 21,
                             fill=BLUE, width=2, joinstyle="round")

class PillSegButton(ctk.CTkFrame):
    """Custom Segmented Button styled as a Pill."""
    def __init__(self, master, values, command=None, height=44, **kwargs):
        super().__init__(master, fg_color="#eef2f7", bg_color="transparent",
                         corner_radius=12, border_width=0, **kwargs)
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
                hover_color="#e2e8f0", corner_radius=9,
                font=ctk.CTkFont(size=13, weight="bold"),
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
                b.configure(fg_color=BLUE, text_color="#ffffff", hover_color=BLUE_DK)
            else:
                b.configure(fg_color="transparent", text_color=TEXT_MD, hover_color="#e2e8f0")


class AccordionCard(ctk.CTkFrame):
    """Collapsible card with icon + title + chevron."""
    def __init__(self, master, title, icon="", icon_image=None, expanded=False, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=14,
                         border_width=1, border_color=BORDER, **kwargs)
        self._expanded = expanded

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=15)
        header.grid_columnconfigure(1, weight=1)

        if icon_image is not None:
            self.icon_lbl = ctk.CTkLabel(header, text="", image=icon_image)
        elif icon in {"colors", "design", "logo"}:
            self.icon_lbl = VectorIcon(header, icon)
        else:
            self.icon_lbl = ctk.CTkLabel(
                header,
                text=icon,
                width=28,
                text_color=BLUE,
                font=ctk.CTkFont(size=22, weight="bold"),
            )
        self.icon_lbl.grid(row=0, column=0, padx=(0, 12))

        self.title_lbl = ctk.CTkLabel(header, text=title, text_color=TEXT_DK,
                                      font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
        self.title_lbl.grid(row=0, column=1, sticky="ew")

        self.chevron = ctk.CTkLabel(header, text="⌄" if expanded else "›", text_color=TEXT_LT,
                                    font=ctk.CTkFont(size=18, weight="bold"))
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
            self.chevron.configure(text="⌄")
        else:
            self.content.pack_forget()
            self.chevron.configure(text="›")
