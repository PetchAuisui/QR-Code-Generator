# QR Generator Pro 🎨📱

A modern, fast, and highly customizable QR Code Generator built with Python and CustomTkinter. 

This application allows you to generate QR codes for URLs, plain text, emails, and WiFi networks, customize their colors and shapes, add a logo, and even save or copy them to your clipboard!

---

## 🚀 Installation Guide

### Prerequisites
Make sure you have **Python 3.8+** installed on your system.

### 1. Clone the repository
```bash
git clone https://github.com/your-username/QR-Gen.git
cd QR-Gen
```

### 2. Install Dependencies
Install all the required Python libraries using `pip`:
```bash
pip3 install customtkinter qrcode pillow
```
*(If you're on a Mac, `pyobjc` may also be required for clipboard support, but the app natively uses `osascript` which works out-of-the-box!)*

### 3. Run the App (Developer Mode)
You can run the app directly from the source code:
```bash
python3 main.py
```

---

## 📦 Building a Standalone App (macOS)

If you want to package this Python script into a native macOS Application (`.app`) that you can double-click to run without the terminal, follow these steps:

### 1. Install PyInstaller
```bash
pip3 install pyinstaller
```

### 2. Generate the macOS Icon (Optional)
This script will generate a custom purple icon (`icon.icns`) for the app:
```bash
python3 assets/generate_icon.py
```

### 3. Build the Application
Run the following `pyinstaller` command to bundle the app. Make sure to replace `<your_python_version>` with your actual Python version (e.g., `3.14`).

```bash
pyinstaller --noconfirm --windowed \
  --name "QR Generator Pro" \
  --icon=assets/icon.icns \
  --add-data "/Library/Frameworks/Python.framework/Versions/<your_python_version>/lib/python<your_python_version>/site-packages/customtkinter:customtkinter/" \
  main.py
```

### 4. Locate the App
Once finished, you will find the final application inside the `dist/` folder:
👉 `dist/QR Generator Pro.app`

*(You can safely drag this app into your Mac's `/Applications` folder!)*

---

## 🗂 Project Structure
The code uses a clean, modular Object-Oriented Programming (OOP) architecture.

- `main.py` — The entry point of the application.
- `src/` — Contains all core modules:
  - `ui.py` — The UI layouts (Panels and Windows).
  - `core.py` — Backend logic for QR generation and History management.
  - `widgets.py` — Reusable CustomTkinter components.
  - `config.py` — App configuration and colors.
- `assets/` — Images and icon generation scripts.
- `scripts/` — Old shell scripts for building.
