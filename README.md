# Project Rebearth Texture Manager

An all-in-one texture manager and modding tool for **Project Rebearth**. This tool allows you to easily browse textures with live previews, import new textures and manage your own texture packs.

![Banner](https://i.ibb.co/DTzFVZS/preview.png)

## Features

*   **ASAR Bypass (Fuses Unlock)**: Automatically patches the game `.exe` and extracts assets to allow instant modding.
*   **Live Texture Browser**: View all game textures (`.webp`) with built-in previews.
*   **Texture Replacement**: Replace any game texture with your own (`.png`, `.jpg`, `.webp`) with auto-conversion to (`.webp`).
*   **Pack Library**: Create, import, and export texture packs as ZIP files. Switch between them in one click.
*   **Safety**: Automatic backup of original game files and "Restore" button.

---

##  How to Use

1.  **Select Game Folder**: Just point to your `Project Rebearth` installation directory (usually \steamapps\common\Project Rebearth) .
2.  **Unlock Modding Mode**: Click the green button. The tool will extract game files and patch the executable (this may take a few seconds to complete).
3.  **Edit Textures**: Use the right panel to replace any image.
4.  **Manage Packs**: 
    *   Create a new pack by clicking **"Save Current to ZIP"**.
    *   Switch packs by clicking them in the **"My Texture Packs"** list and pressing **"Apply Selected Pack"**.
5.  **Play**: Press **"LAUNCH GAME"** and check the changes

---

## Installation (For Users)

1.  Go to the [Releases](https://github.com/EatherBone/project-rebearth-texturepack-manager/releases) section.
2.  Download the latest `RebearthPackManager_v1.0.exe`.
3.  Move the file to any folder on your PC.
4.  Run `RebearthPackManager_v1.0.exe`.

---

## How to Build from Source (For Developers)

If you want to compile the program yourself, follow these instructions.

### Prerequisites
*   **Python 3.10+**
*   Pip

### 1. Clone the repository

### 2. Install dependencies
```bash
pip install customtkinter Pillow pyinstaller
```

### 3. Prepare Assets
Ensure your project folder looks like this:
```text
/
├── main.py
├── config.json
├── assets/
│   ├── electron.exe ( RENAME TO - project_rebearth.exe)  <-- Clean Electron binary 
│   └── icon.ico      <-- (Oprional) Program icon
└── packs/            <-- (Optional) Default texture packs
```
* Get Electron there: https://github.com/electron/electron/releases?q=34.5.8 and DONT FORGET TO RENAME EXE TO project_rebearth.exe

### 4. Run PyInstaller
Use the following command to create a portable build:

```bash
pyinstaller --noconfirm --onefile --windowed --uac-admin --name "RebearthPackManager_v1.0" --icon="assets/icon.ico" --add-data "assets;assets" --add-data "config.json;." main.py
```

### 5. Result
The compiled program will be in the `dist/RebearthManager` folder. Zip this entire folder to share it.


---

## WARNING
This tool is intended for personal modding use only. I am not responsible for any game issues or corrupted files. Always keep your `_backups` folder safe.
