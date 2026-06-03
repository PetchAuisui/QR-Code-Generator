import os
import json
import subprocess
import tempfile
from datetime import datetime
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer, CircleModuleDrawer, SquareModuleDrawer, GappedSquareModuleDrawer
)
from PIL import Image, ImageOps

from .config import hex_rgb

RESAMPLE = getattr(Image, "Resampling", Image).LANCZOS

class QRManager:
    """Handles QR code generation and image styling."""
    
    @staticmethod
    def generate(data, shape="Square", fg_color="#000000", bg_color="#FFFFFF", logo_path=None):
        if not data: 
            return None
            
        drawers = {
            "Circle": CircleModuleDrawer(),
            "Rounded": RoundedModuleDrawer(),
            "Gapped": GappedSquareModuleDrawer(),
            "Square": SquareModuleDrawer()
        }
        drawer = drawers.get(shape, SquareModuleDrawer())
        
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H, box_size=10, border=2)
        qr.add_data(data)
        qr.make(fit=True)
        img = qr.make_image(image_factory=StyledPilImage, module_drawer=drawer)
        
        fg, bg = hex_rgb(fg_color), hex_rgb(bg_color)
        img = ImageOps.colorize(img.convert("L"), black=fg, white=bg).convert("RGBA")
                
        if logo_path and os.path.exists(logo_path):
            try:
                logo = Image.open(logo_path).convert("RGBA")
                bw = int(img.width * 0.22)
                logo = logo.resize((bw, int(logo.height * bw / logo.width)), RESAMPLE)
                pos = ((img.width - logo.width) // 2, (img.height - logo.height) // 2)
                patch = Image.new("RGBA", (logo.width + 12, logo.height + 12), (*bg, 255))
                img.paste(patch, (pos[0] - 6, pos[1] - 6))
                img.paste(logo, pos, logo)
            except Exception:
                pass
                
        return img
        
    @staticmethod
    def generate_svg(data, filepath):
        import qrcode.image.svg
        factory = qrcode.image.svg.SvgPathImage
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H,
                           box_size=10, border=4, image_factory=factory)
        qr.add_data(data)
        qr.make(fit=True)
        qr.make_image().save(filepath)


class ClipboardManager:
    """Handles OS-level clipboard operations."""
    
    @staticmethod
    def copy_image(qr_img):
        if not qr_img: 
            return False, "No image"
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                qr_img.save(f.name, "PNG")
                tmp_path = f.name
            script = f'set the clipboard to (read (POSIX file "{tmp_path}") as TIFF picture)'
            subprocess.run(["osascript", "-e", script], check=True)
            return True, "Copied to clipboard!"
        except Exception as e:
            return False, f"Copy failed: {e}"
