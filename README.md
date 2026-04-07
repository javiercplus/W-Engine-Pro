# W-Engine Pro

Native animated wallpaper engine for Linux. High performance (Python 3 + Qt6), low resource consumption and portable AppImage package. Automatic pause during games/fullscreen.

![Screenshot 1](https://github.com/user-attachments/assets/6fa054fb-7709-4970-980a-38535e39e4d8)
![Screenshot 2](https://github.com/user-attachments/assets/29d0edb9-62ac-42a5-b904-aac108a557c3)
![Screenshot 3](https://github.com/user-attachments/assets/aa990bf3-2a93-4177-b9c2-eb86596b8492)

## Features

- Video wallpaper support (local files)
- Wallpaper by URL (YouTube, Vimeo, direct video links)
- YouTube support with automatic thumbnail generation
- Real-time changes (no restart needed)
- Dynamic UI with Qt6
- Reactive engine (event-driven)
- Smart auto-save
- Multi-monitor support
- CPU/GPU optimization
- Automatic pause on activity
- Start minimized to system tray
- Autostart on system login

## Installation

### AppImage (Recommended)

Download the AppImage from releases:
```bash
chmod +x W-Engine-Pro-1.0.0-x86_64.AppImage
./W-Engine-Pro-1.0.0-x86_64.AppImage
```

### Flatpak

Download and install the bundle:
```bash
flatpak install --user W-Engine-Pro-1.0.0-x86_64.flatpak
flatpak run org.wengine.Pro
```

### Build from source

```bash
# Install dependencies
pip install PySide6 psutil Pillow

# Install system dependencies
# Arch Linux
sudo pacman -S mpv mpvpaper xorg-xwininfo xorg-xrandr yt-dlp

# Debian/Ubuntu
sudo apt install mpv mpvpaper x11-utils yt-dlp

# Fedora
sudo dnf install mpv mpvpaper xorg-x11-utils yt-dlp
```

## Building Packages

A unified build script handles both AppImage and Flatpak:

```bash
cd packaging

# Build AppImage
./build.sh appimage
# Output: dist/W-Engine-Pro-1.0.0-x86_64.AppImage

# Build Flatpak (creates .flatpak bundle automatically)
./build.sh flatpak
# Output: packaging/flatpak/W-Engine-Pro-1.0.0-x86_64.flatpak

# Build both
./build.sh

# Clean all build artifacts
./build.sh clean
```

### Flatpak standalone

You can also build Flatpak independently:
```bash
cd packaging/flatpak
./build-flatpak.sh
# Output: W-Engine-Pro-1.0.0-x86_64.flatpak
```

Requirements: `flatpak-builder`

## Usage

```bash
python main.py                    # Normal mode
python main.py --debug            # Debug mode with logs
python main.py --minimized        # Start minimized to system tray
```

### Autostart Configuration

1. Open W-Engine Pro
2. Go to Settings -> Engine
3. Check "Start with system"
4. Check "Start minimized" (optional)

This creates ~/.config/autostart/wengine-pro.desktop

## Compatibility

| Environment | Status |
|-------------|--------|
| KDE Plasma (X11) | Stable |
| XFCE | Stable |
| GNOME (X11) | Partial |
| GNOME (Wayland) | Experimental |
| Cinnamon | Stable |
| Other Wayland | Experimental |

## Architecture

```
core/                   # Core engine
  engine_controller.py  # Main controller
  renderer_manager.py   # Backend manager
  process_manager.py    # Child process management
  health_monitor.py     # IPC health monitor
  activity_monitor.py   # Activity detector
  resource_manager.py   # Wallpaper & thumbnail management
  config_manager.py     # Configuration management
  desktop_helper.py     # Desktop environment detection

engines/                # Rendering backends
  x11_backend.py        # X11 + mpv direct
  wayland_backend.py    # Wayland + mpvpaper
  gnome_mpv_backend/    # GNOME integrated
  mpv_engine/           # libmpv engine

ui/                     # Qt6 Interface
  main_window.py        # Main window
  sidebar.py            # Sidebar
  pages.py              # Menu pages
  wallpaper_grid.py     # Wallpaper grid view
  url_dialog.py         # URL input dialog
  settings_panel.py     # Settings panel

threads/                # Worker threads

packaging/              # Build scripts
  build.sh              # Unified build script (AppImage + Flatpak)
  appimage/             # AppImage-specific files
    appimagetool        # AppImage creation tool
    linuxdeploy         # Linux deployment tool
  flatpak/              # Flatpak-specific files
    build-flatpak.sh    # Standalone Flatpak build script
    org.wengine.Pro.json # Flatpak manifest
    wengine.spec        # PyInstaller spec file
```

## License

GPLv3