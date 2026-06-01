import os

# ── Paths ──
BASE_DIR = os.path.expanduser("~/Library/Application Support/QRGeneratorPro")
HISTORY_FILE = os.path.join(BASE_DIR, "history.json")
HISTORY_DIR = os.path.join(BASE_DIR, "history_images")
os.makedirs(HISTORY_DIR, exist_ok=True)

# ── Colors ──
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
