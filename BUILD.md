# QR Code Generator - Build Guide

## Building Standalone Applications

### Prerequisites
- PyInstaller installed: `pip3 install pyinstaller`

---

## macOS Build

### Option 1: Quick Build (without custom icon)
```bash
bash build_macos.sh
```

### Option 2: Custom Build
```bash
pyinstaller --onefile \
  --windowed \
  --name "QR Code Generator" \
  qr_generator.py
```

**Output:** `dist/QR Code Generator.app`

### Create a DMG for Distribution
```bash
# Create DMG from dist folder
hdiutil create -volname "QR Code Generator" \
  -srcfolder dist \
  -ov -format UDZO QRCodeGenerator.dmg
```

---

## Windows Build

### Option 1: Quick Build (without custom icon)
On Windows Command Prompt:
```cmd
build_windows.bat
```

### Option 2: Manual Build
```cmd
pyinstaller --onefile --windowed --name "QR Code Generator" qr_generator.py
```

**Output:** `dist\QR Code Generator.exe`

### Create Installer (Optional)
Use NSIS or another installer tool to create a `.exe` installer:
```cmd
pip install pyinstaller-nsis
```

---

## Advanced Options

### Add Custom Icon (Optional)
1. **macOS icon** (.icns format):
   - Use [iconutil](https://developer.apple.com/library/archive/documentation/GraphicsAnimation/Conceptual/HighResolutionOSX/Optimizing/Optimizing.html) or online converters
   - Place as `icon.icns` in the project folder

2. **Windows icon** (.ico format):
   - Use Paint or online converters
   - Place as `icon.ico` in the project folder

Then modify build commands:
```bash
# macOS
pyinstaller --onefile --windowed --name "QR Code Generator" \
  --icon=icon.icns qr_generator.py

# Windows
pyinstaller --onefile --windowed --name "QR Code Generator" \
  --icon=icon.ico qr_generator.py
```

---

## Output Files

- **macOS**: `dist/QR Code Generator.app` (Double-click to run)
- **Windows**: `dist/QR Code Generator.exe` (Double-click to run)

Both can be distributed to users who don't have Python installed!

---

## Troubleshooting

**"Command not found" error:**
```bash
python3 -m PyInstaller --onefile --windowed qr_generator.py
```

**Large file size:**
Use `--onedir` instead of `--onefile` for smaller initial build (creates a folder instead of single file)

**Need to clean build:**
```bash
rm -rf build dist *.spec  # macOS/Linux
rmdir build dist *.spec   # Windows
```
