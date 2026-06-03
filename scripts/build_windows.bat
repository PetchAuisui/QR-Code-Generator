@echo off
REM Build script for Windows

echo Building QR Generator Pro for Windows...

for /f "tokens=*" %%i in ('python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i

python -m PyInstaller --noconfirm --windowed ^
  --name "QR Generator Pro" ^
  --icon="icon.ico" ^
  --add-data "%CTK_PATH%;customtkinter/" ^
  --add-data "icon.png;." ^
  --add-data "icon.ico;." ^
  main.py

echo Build complete! Executable is in: dist\QR Generator Pro
echo Ready to distribute!
