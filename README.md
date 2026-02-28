# 📦 Project Bundler

> Archive, compress, and restore project folders with SHA-256 verified integrity.  
> A self-contained desktop app for Linux — no manual dependency juggling.

![Python](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-Linux-orange)
![License](https://img.shields.io/badge/license-MIT-green)

---

## ✨ Features

- **Drag & drop** folders onto the Archive tab to compress them
- **SHA-256 verification** — archive is checked byte-for-byte before saving
- **Restore** to any destination with full directory structure preserved
- **Library tab** — browse, restore, or delete all your saved bundles
- Optional **delete original** after verified archive
- Works with **Zenity** native dialogs (falls back to tkinter dialogs if unavailable)

---

## 🐧 Supported Linux Distributions

| Distro Family | Tested On |
|---|---|
| Debian / Ubuntu | Ubuntu 20.04, 22.04, 24.04 · Linux Mint |
| Fedora / RHEL | Fedora 38+ · RHEL 9 · Rocky Linux |
| Arch Linux | Arch · Manjaro · EndeavourOS |
| openSUSE | Leap 15 · Tumbleweed |

---

## 🚀 Installation

### Option A — One-line installer (recommended)

Downloads the latest release and runs the installer:

```bash
curl -fsSL https://github.com/YOUR_USERNAME/project-bundler/releases/latest/download/project-bundler-linux-x86_64.tar.gz \
  | tar -xz && bash install.sh
```

### Option B — Clone and install from source

```bash
git clone https://github.com/YOUR_USERNAME/project-bundler.git
cd project-bundler
bash install.sh
```

The installer will:
1. Detect your distro and install system packages (`python3-tk`, `zenity`, etc.)
2. Create a virtualenv at `~/.local/share/project-bundler/venv`
3. Install `customtkinter` and `tkinterdnd2` inside that venv
4. Add a launcher to `~/.local/bin/project-bundler`
5. Add a `.desktop` entry so it appears in your application menu

### Option C — Run without installing

```bash
pip install customtkinter tkinterdnd2
python3 project_bundler_v3.py
```

---

## 🗑️ Uninstall

```bash
bash uninstall.sh
```

Your bundles in `~/MyProjectBundles/` are **never deleted** by the uninstaller.

---

## 🛠️ Building a standalone binary yourself

Requires Python 3.9+ and PyInstaller:

```bash
pip install pyinstaller customtkinter tkinterdnd2

pyinstaller \
  --name project-bundler \
  --onefile \
  --windowed \
  --clean \
  --collect-all customtkinter \
  --collect-all tkinterdnd2 \
  project_bundler_v3.py
```

Binary lands at `dist/project-bundler`.

---

## 🔄 CI / CD — Auto-builds via GitHub Actions

Every time you push a version tag, GitHub automatically builds a release binary:

```bash
git tag v1.2
git push origin v1.2
```

The workflow (`.github/workflows/build.yml`) will:
- Build on Ubuntu 20.04 (maximises glibc compatibility across distros)
- Produce a `.tar.gz` containing the binary + install/uninstall scripts
- Attach it to the GitHub Release automatically

---

## 📁 Bundle Format

Bundles are stored as `.bundle.txt` files in `~/MyProjectBundles/`.

Internally each file is:
```
base64( gzip( tar( project_folder/ ) ) )
```

Plain text format means bundles survive being emailed, pasted into notes, or stored in any cloud service.

---

## 🗂️ Repository Structure

```
project-bundler/
├── project_bundler_v3.py        # Main application
├── install.sh                   # Cross-distro installer
├── uninstall.sh                 # Uninstaller
├── .github/
│   └── workflows/
│       └── build.yml            # Auto-build on tag push
└── README.md
```

---

## 📜 License

MIT — do whatever you like with it.
