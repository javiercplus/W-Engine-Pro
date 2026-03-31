# W-Engine Pro

Native animated wallpaper engine for Linux. High performance (Python 3 + Qt6), low resource consumption and universal AppImage package. Automatic pause during games/fullscreen.

![Screenshot 1](https://github.com/user-attachments/assets/6fa054fb-7709-4970-980a-38535e39e4d8)
![Screenshot 2](https://github.com/user-attachments/assets/29d0edb9-62ac-42a5-b904-aac108a557c3)
![Screenshot 3](https://github.com/user-attachments/assets/aa990bf3-2a93-4177-b9c2-eb86596b8492)

## Features

- Video wallpaper support
- URL wallpapers (streaming)
- Real-time changes (no restart needed)
- Dynamic UI with Qt6
- Reactive engine (event-driven)
- Smart auto-save
- Multi-monitor support
- CPU/GPU optimization
- Automatic pause on activity

## Compatibility

| Environment | Status |
|-------------|--------|
| KDE Plasma (X11) | Stable |
| XFCE | Stable |
| GNOME (X11) | Partial |
| GNOME (Wayland) | Experimental |
| Cinnamon | Stable |
| Other Wayland | Experimental |

## Requirements

### Python
```bash
pip install PySide6 psutil python-xlib Pillow
```

### System
```bash
# Arch Linux
sudo pacman -S mpv xorg-xwininfo xorg-xrandr

# Debian/Ubuntu
sudo apt install mpv x11-utils xrandr

# Fedora
sudo dnf install mpv xorg-x11-utils xrandr
```

> **Note:** `Pillow` is optional (only for static blur effect).

## Usage

```bash
python main.py           # Normal mode
python main.py --debug   # Debug mode with logs
```

## Architecture

```
core/                   # Core engine
  engine_controller.py  # Main controller
  renderer_manager.py   # Backend manager
  process_manager.py   # Child process management
  health_monitor.py     # IPC health monitor
  activity_monitor.py   # Activity detector

engines/                # Rendering backends
  x11_backend.py        # X11 + mpv direct
  wayland_backend.py    # Wayland + mpvpaper
  gnome_mpv_backend/    # GNOME integrated

ui/                     # Qt6 Interface
  main_window.py        # Main window
  sidebar.py            # Sidebar
  pages.py              # Menu pages

threads/                # Worker threads
```

## License

GPLv3
