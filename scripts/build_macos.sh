#!/bin/bash
# Build script for macOS

echo "🍎 Building QR Studio for macOS..."

# Find customtkinter path
CTK_PATH=$(python3 -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))")

python3 -m PyInstaller --noconfirm --windowed \
  --name "QR Studio" \
  --icon=icon.icns \
  --add-data "$CTK_PATH:customtkinter/" \
  --add-data "icon_macos.png:." \
  main.py

echo "✅ Build complete! App is in: dist/QR Studio.app"
echo "📦 To distribute, create a DMG file or zip the app from the dist/ folder"
