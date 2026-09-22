import os
import sys
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
    """Handles OS-level clipboard operations cross-platform."""

    @staticmethod
    def _copy_windows(qr_img):
        import io
        import ctypes
        from ctypes import wintypes

        output = io.BytesIO()
        qr_img.convert("RGB").save(output, "BMP")
        data = output.getvalue()[14:]  # Remove 14-byte BMP header for DIB
        output.close()

        kernel32 = ctypes.windll.kernel32
        user32 = ctypes.windll.user32

        kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
        kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
        kernel32.GlobalLock.restype = wintypes.LPVOID
        kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
        kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]

        user32.OpenClipboard.restype = wintypes.BOOL
        user32.OpenClipboard.argtypes = [wintypes.HWND]
        user32.EmptyClipboard.restype = wintypes.BOOL
        user32.SetClipboardData.restype = wintypes.HANDLE
        user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
        user32.CloseClipboard.restype = wintypes.BOOL

        GMEM_MOVEABLE = 0x0002
        CF_DIB = 8

        hCd = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not hCd:
            raise RuntimeError("GlobalAlloc failed")

        pchData = kernel32.GlobalLock(hCd)
        if not pchData:
            raise RuntimeError("GlobalLock failed")

        ctypes.memmove(pchData, data, len(data))
        kernel32.GlobalUnlock(hCd)

        if not user32.OpenClipboard(None):
            raise RuntimeError("OpenClipboard failed")

        try:
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_DIB, hCd)
        finally:
            user32.CloseClipboard()

    @staticmethod
    def _copy_macos(qr_img):
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                qr_img.save(f.name, "PNG")
                tmp_path = f.name
            script = f'set the clipboard to (read (POSIX file "{tmp_path}") as TIFF picture)'
            subprocess.run(["osascript", "-e", script], check=True)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    @staticmethod
    def _copy_linux(qr_img):
        import shutil
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                qr_img.save(f.name, "PNG")
                tmp_path = f.name

            if shutil.which("xclip"):
                with open(tmp_path, "rb") as f_in:
                    subprocess.run(["xclip", "-selection", "clipboard", "-t", "image/png"], stdin=f_in, check=True)
            elif shutil.which("wl-copy"):
                with open(tmp_path, "rb") as f_in:
                    subprocess.run(["wl-copy", "--type", "image/png"], stdin=f_in, check=True)
            else:
                raise RuntimeError("Neither 'xclip' nor 'wl-copy' utility found")
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    @staticmethod
    def copy_image(qr_img):
        if not qr_img:
            return False, "No image"
        try:
            if sys.platform == "win32":
                ClipboardManager._copy_windows(qr_img)
            elif sys.platform == "darwin":
                ClipboardManager._copy_macos(qr_img)
            else:
                ClipboardManager._copy_linux(qr_img)
            return True, "Copied to clipboard!"
        except Exception as e:
            return False, f"Copy failed: {e}"
