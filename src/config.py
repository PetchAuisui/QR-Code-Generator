import os

# ── Paths ──
BASE_DIR = os.path.expanduser("~/Library/Application Support/QRGeneratorPro")

# ── Colors ──
BG       = "#f3f6fb"  # app background
CARD_BG  = "#ffffff"  # primary surface
BORDER   = "#e2e8f0"  # subtle outline
BLUE     = "#2563eb"  # primary
BLUE_DK  = "#1d4ed8"  # primary hover
BLUE_LT  = "#eff6ff"  # primary tint
TEXT_DK  = "#0f172a"  # primary text
TEXT_MD  = "#475569"  # secondary text
TEXT_LT  = "#94a3b8"  # muted text

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
