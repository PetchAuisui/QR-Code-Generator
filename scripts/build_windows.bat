@echo off
REM Build script for Windows

echo. Building QR Code Generator for Windows...

pyinstaller --onefile ^
  --windowed ^
  --name "QR Code Generator" ^
  --icon=icon.ico ^
  --add-data ".;." ^
  qr_generator.py

echo. Build complete! Executable is in: dist\QR Code Generator.exe
echo. Ready to distribute!
