#!/usr/bin/env python3
"""
Generate a QR Code icon for the app
"""
from PIL import Image, ImageDraw, ImageFilter
import qrcode

import os

# Check if icon.png already exists
if os.path.exists("icon.png"):
    print("✅ Found existing icon.png. Using it to generate .ico and .icns...")
    icon = Image.open("icon.png")
else:
    print("ℹ️ icon.png not found. Generating a new one...")
    # Create a QR code with "QR Gen" text
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=1,
    )
    qr.add_data("QR-Gen")
    qr.make(fit=True)

    # Create QR image with custom colors
    qr_img = qr.make_image(fill_color="#7C5CBF", back_color="#FFFFFF")
    qr_img = qr_img.convert("RGB")

    # Create a rounded square icon with gradient background
    size = 1024
    icon = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)

    # Draw rounded background (gradient-like effect)
    radius = int(size * 0.2)
    # Background gradient colors (violet theme)
    bg_color = (124, 92, 191, 255)  # Main violet

    # Create background with rounded corners
    for i in range(radius):
        alpha = int(255 * (1 - i / radius))
        color = (124, 92, 191, alpha)
        draw.arc(
            [(i, i), (size - i - 1, size - i - 1)],
            start=90, end=180, fill=color, width=1
        )

    # Draw main rounded rectangle background
    draw.rectangle([(0, 0), (size, size)], fill=(240, 240, 245, 255), outline=None)

    # Add border
    border_width = int(size * 0.05)
    draw.rectangle(
        [(border_width, border_width), (size - border_width, size - border_width)],
        outline=(124, 92, 191, 255),
        width=int(size * 0.015)
    )

    # Paste QR code in center
    qr_size = int(size * 0.7)
    qr_img_resized = qr_img.resize((qr_size, qr_size), Image.LANCZOS)
    qr_img_rgba = qr_img_resized.convert("RGBA")
    offset = int((size - qr_size) / 2)
    icon.paste(qr_img_rgba, (offset, offset), qr_img_rgba)

    # Apply slight blur and shadow effect
    icon = icon.filter(ImageFilter.GaussianBlur(radius=2))

    # Save as PNG
    icon.save("icon.png")
    print("✅ Icon created: icon.png (1024x1024)")

# Save as ICO (for Windows)
icon_ico = icon.resize((256, 256), Image.LANCZOS)
icon_ico.save("icon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print("✅ Icon converted to .ico format: icon.ico")
print("📦 Converting to .icns format...")

import subprocess
import os

# Convert PNG to ICNS using iconutil
if os.path.exists("icon.png"):
    # Create IconSet directory
    os.makedirs("icon.iconset", exist_ok=True)
    
    # Create different sizes
    sizes = [16, 32, 64, 128, 256, 512]
    
    for size in sizes:
        # Regular
        img = Image.open("icon.png")
        img_resized = img.resize((size, size), Image.LANCZOS)
        img_resized.save(f"icon.iconset/icon_{size}x{size}.png")
        
        # Retina (2x)
        img_resized_2x = img.resize((size * 2, size * 2), Image.LANCZOS)
        img_resized_2x.save(f"icon.iconset/icon_{size}x{size}@2x.png")
    
    print("✅ Created icon.iconset directory with all sizes")
    
    # Convert to ICNS
    try:
        subprocess.run(
            ["iconutil", "-c", "icns", "icon.iconset", "-o", "icon.icns"],
            check=True
        )
        print("✅ Icon converted to .icns format: icon.icns")
    except subprocess.CalledProcessError:
        print("❌ iconutil failed. Make sure you're on macOS.")
    except FileNotFoundError:
        print("❌ iconutil not found. This tool only works on macOS.")
