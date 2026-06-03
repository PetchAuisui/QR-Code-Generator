#!/bin/bash
# Build script for macOS

echo "🍎 Building QR Generator Pro for macOS..."

# Find customtkinter path
CTK_PATH=$(python3 -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))")

python3 -m PyInstaller --noconfirm --windowed \
  --name "QR Generator Pro" \
  --icon=icon.icns \
  --add-data "$CTK_PATH:customtkinter/" \
  --add-data "icon.png:." \
  --add-data "icon.icns:." \
  main.py

echo "✅ Build complete! App is in: dist/QR Generator Pro.app"
echo "📦 To distribute, create a DMG file or zip the app from the dist/ folder"
