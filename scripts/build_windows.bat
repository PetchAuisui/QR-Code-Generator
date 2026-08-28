@echo off
REM Build script for Windows

echo Building QR Studio for Windows...

for /f "tokens=*" %%i in ('python -c "import customtkinter; import os; print(os.path.dirname(customtkinter.__file__))"') do set CTK_PATH=%%i

python -m PyInstaller --noconfirm --windowed ^
  --name "QR Studio" ^
  --icon="icon.ico" ^
  --add-data "%CTK_PATH%;customtkinter/" ^
  --add-data "icon.ico;." ^
  main.py

echo Build complete! Executable is in: dist\QR Studio
echo Ready to distribute!
