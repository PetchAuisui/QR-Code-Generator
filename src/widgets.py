import customtkinter as ctk
from .config import BLUE, BLUE_DK, CARD_BG, BORDER, TEXT_DK, TEXT_MD, TEXT_LT

class PillSegButton(ctk.CTkFrame):
    """Custom Segmented Button styled as a Pill."""
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
                b.configure(fg_color=BLUE, text_color="#ffffff", hover_color=BLUE_DK)
            else:
                b.configure(fg_color="transparent", text_color=TEXT_MD, hover_color="#dce9ff")


class AccordionCard(ctk.CTkFrame):
    """Collapsible card with icon + title + chevron."""
    def __init__(self, master, title, icon="", icon_image=None, expanded=False, **kwargs):
        super().__init__(master, fg_color=CARD_BG, corner_radius=12,
                         border_width=1, border_color=BORDER, **kwargs)
        self._expanded = expanded

        # Header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=20)
        header.grid_columnconfigure(1, weight=1)

        if icon_image is not None:
            self.icon_lbl = ctk.CTkLabel(header, text="", image=icon_image)
        else:
            self.icon_lbl = ctk.CTkLabel(header, text=icon, text_color=BLUE, font=ctk.CTkFont(size=20))
        self.icon_lbl.grid(row=0, column=0, padx=(0, 12))

        self.title_lbl = ctk.CTkLabel(header, text=title, text_color=TEXT_DK,
                                      font=ctk.CTkFont(size=16, weight="bold"), anchor="w")
        self.title_lbl.grid(row=0, column=1, sticky="ew")

        self.chevron = ctk.CTkLabel(header, text="∨", text_color=TEXT_LT, font=ctk.CTkFont(size=14))
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
