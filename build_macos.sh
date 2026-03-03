#!/bin/bash
# Build script for macOS

echo "🍎 Building QR Code Generator for macOS..."

pyinstaller --onedir \
  --windowed \
  --name "QR Code Generator" \
  --icon=icon.icns \
  --add-data ".:." \
  --osx-bundle-identifier=com.qrgenerator.app \
  qr_generator.py

echo "✅ Build complete! App is in: dist/QR Code Generator.app"
echo "📦 To distribute, create a DMG file from the dist/ folder"
