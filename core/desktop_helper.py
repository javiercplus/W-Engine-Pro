import os
import shutil
import subprocess
import logging
import sys
from PySide6.QtCore import QStandardPaths


class Metrics:
    def __init__(self):
        self.restarts = 0
        self.safe_mode_activations = 0
        self.ipc_failures = 0
        self.backend_switches = 0

    def to_dict(self):
        return self.__dict__


class EnvironmentProfile:
    def __init__(
        self, compositor, desktop, protocol, capabilities, gpu_vendor="Unknown"
    ):
        self.compositor = compositor
        self.desktop = desktop
        self.protocol = protocol
        self.capabilities = capabilities
        self.gpu_vendor = gpu_vendor  # Nvidia, AMD, Intel, Mesa, etc.
        self.metrics = Metrics()

    def is_nvidia(self):
        return "nvidia" in self.gpu_vendor.lower()

    def get_best_backend(self):
        """Returns the recommended backend based on scoring."""
        scores = {
            "x11": 100 if self.protocol == "x11" else 0,
            "mpvpaper": (
                90
                if self.protocol == "wayland" and self.capabilities["layer_shell"]
                else 0
            ),
            "gnome_fake": (
                150 if self.compositor == "GNOME" else 0
            ),
            "mpv_floating": 30 if self.protocol == "wayland" else 0,
        }

        # Sort by score descending and return the name of the highest
        best = max(scores, key=scores.get)
        logging.info(f"[Detector] Backend Scores: {scores} -> Best: {best}")
        return best

    def get_features(self):
        """Returns feature flags for the UI."""
        return {
            "ipc_control": True,
            "multi_monitor": self.protocol == "x11" or self.capabilities["layer_shell"],
            "alpha_transparency": self.protocol == "x11",
            "layer_shell": self.capabilities["layer_shell"],
            "restart_required_on_resize": self.compositor == "GNOME"
            and self.protocol == "wayland",
        }

    def __repr__(self):
        return f"EnvironmentProfile(compositor={self.compositor}, protocol={self.protocol}, best_backend={self.get_best_backend()})"


class DesktopHelper:
    """
    Universal helper for desktop-specific operations and environment detection.
    """
    EXTENSION_UUID = "w-engine-helper@gamingofdemon.com"
    _cached_profile = None

    @staticmethod
    def get_profile() -> EnvironmentProfile:
        """Advanced detection of the current windowing system and compositor."""
        if DesktopHelper._cached_profile:
            return DesktopHelper._cached_profile

        protocol = DesktopHelper._get_protocol()
        compositor = DesktopHelper._get_compositor()
        gpu_vendor = DesktopHelper._get_gpu_vendor()
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "Unknown").lower()

        # Initial capabilities
        capabilities = {
            "real_wallpaper": False,
            "layer_shell": False,
            "root_window": False,
            "wayland_safe": False,
            "needs_xwinwrap": False,
        }

        if protocol == "wayland":
            if compositor in ["Hyprland", "Sway", "River", "KDE"]:
                capabilities["layer_shell"] = True
                capabilities["wayland_safe"] = True
        else:  # X11
            capabilities["root_window"] = True
            if compositor in ["XFCE", "KDE", "MATE", "i3", "Openbox"]:
                capabilities["needs_xwinwrap"] = True

        DesktopHelper._cached_profile = EnvironmentProfile(
            compositor, desktop, protocol, capabilities, gpu_vendor
        )
        return DesktopHelper._cached_profile

    @staticmethod
    def setup_autostart(enabled=True):
        """Crea o elimina el archivo de autostart en ~/.config/autostart."""
        autostart_dir = os.path.expanduser("~/.config/autostart")
        desktop_file = os.path.join(autostart_dir, "wengine-pro.desktop")

        if not enabled:
            if os.path.exists(desktop_file):
                os.remove(desktop_file)
            return

        os.makedirs(autostart_dir, exist_ok=True)

        appimage_path = os.environ.get("APPIMAGE")
        if not appimage_path:
            main_script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
            appimage_path = f"{sys.executable} {main_script}"

        content = f"""[Desktop Entry]
Type=Application
Name=W-Engine Pro
Exec={appimage_path} --autostart
Icon=wengine
Comment=Start W-Engine Pro on login
Categories=Utility;
Terminal=false
"""
        try:
            with open(desktop_file, "w") as f:
                f.write(content)
            logging.info(f"Autostart configurado en: {desktop_file}")
        except Exception as e:
            logging.error(f"Error al configurar autostart: {e}")

    @staticmethod
    def is_gnome():
        return "gnome" in os.environ.get("XDG_CURRENT_DESKTOP", "").lower()

    @staticmethod
    def is_wayland():
        return DesktopHelper._get_protocol() == "wayland"

    @staticmethod
    def is_extension_installed():
        dest = os.path.expanduser(
            f"~/.local/share/gnome-shell/extensions/{DesktopHelper.EXTENSION_UUID}"
        )
        return os.path.exists(dest)

    @staticmethod
    def install_extension():
        """Installs the GNOME extension to the user's local directory."""
        try:
            appdir = os.environ.get("APPDIR")
            if appdir:
                src = os.path.join(appdir, "usr/share/wengine/data/gnome_extension")
                if not os.path.exists(src):
                    src = os.path.join(appdir, "data/gnome_extension")
            else:
                base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                src = os.path.join(base_dir, "data", "gnome_extension")

            if not os.path.exists(src):
                src = os.path.join(os.getcwd(), "data", "gnome_extension")

            if not os.path.exists(src):
                return False, f"No se encontró la fuente de la extensión en: {src}"

            dest = os.path.expanduser(
                f"~/.local/share/gnome-shell/extensions/{DesktopHelper.EXTENSION_UUID}"
            )

            if os.path.exists(dest):
                shutil.rmtree(dest)

            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copytree(src, dest)
            logging.info(f"GNOME Extension installed from {src} to {dest}")

            cmd = DesktopHelper._get_host_cmd_prefix() + [
                "gnome-extensions",
                "enable",
                DesktopHelper.EXTENSION_UUID,
            ]
            subprocess.run(cmd, capture_output=True)

            return (
                True,
                "Extensión instalada. Por favor, reinicia sesión (o pulsa Alt+F2 y escribe 'r' en X11) para activar.",
            )
        except Exception as e:
            logging.error(f"Error installing GNOME extension: {e}")
            return False, str(e)

    @staticmethod
    def open_extensions_app():
        cmd = DesktopHelper._get_host_cmd_prefix() + ["gnome-extensions-app"]
        subprocess.run(cmd, start_new_session=True)

    @staticmethod
    def get_current_background():
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in desktop:
            return DesktopHelper.get_gnome_background()
        elif "xfce" in desktop:
            return DesktopHelper.get_xfce_background()
        return None, None

    @staticmethod
    def get_gnome_background():
        prefix = DesktopHelper._get_host_cmd_prefix()
        try:
            uri = subprocess.check_output(prefix + ["gsettings", "get", "org.gnome.desktop.background", "picture-uri"]).decode().strip().strip("'")
            uri_dark = subprocess.check_output(prefix + ["gsettings", "get", "org.gnome.desktop.background", "picture-uri-dark"]).decode().strip().strip("'")
            return uri, uri_dark
        except: return None, None

    @staticmethod
    def get_xfce_background():
        prefix = DesktopHelper._get_host_cmd_prefix()
        try:
            all_props = subprocess.check_output(prefix + ["xfconf-query", "-c", "xfce4-desktop", "-l"]).decode().splitlines()
            target = next((p for p in all_props if "last-image" in p), "/backdrop/screen0/monitor0/workspace0/last-image")
            path = subprocess.check_output(prefix + ["xfconf-query", "-c", "xfce4-desktop", "-p", target]).decode().strip()
            return path, None
        except: return None, None

    @staticmethod
    def set_background(path_or_uri):
        if not path_or_uri: return
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "gnome" in desktop:
            DesktopHelper.set_gnome_background(path_or_uri)
        elif "xfce" in desktop:
            DesktopHelper.set_xfce_background(path_or_uri)
        elif "kde" in desktop or "plasma" in desktop:
            DesktopHelper.set_kde_background(path_or_uri)

    @staticmethod
    def set_gnome_background(path_or_uri):
        prefix = DesktopHelper._get_host_cmd_prefix()
        uri = path_or_uri if path_or_uri.startswith("file://") else f"file://{path_or_uri}"
        try:
            subprocess.run(prefix + ["gsettings", "set", "org.gnome.desktop.background", "picture-uri", f"'{uri}'"])
            subprocess.run(prefix + ["gsettings", "set", "org.gnome.desktop.background", "picture-uri-dark", f"'{uri}'"])
        except Exception as e:
            logging.error(f"Error setting GNOME background: {e}")

    @staticmethod
    def set_xfce_background(path_or_uri):
        prefix = DesktopHelper._get_host_cmd_prefix()
        try:
            all_props = subprocess.check_output(prefix + ["xfconf-query", "-c", "xfce4-desktop", "-l"]).decode().splitlines()
            targets = [p for p in all_props if "last-image" in p] or ["/backdrop/screen0/monitor0/workspace0/last-image"]
            for target in targets:
                subprocess.run(prefix + ["xfconf-query", "-c", "xfce4-desktop", "-p", target, "-s", path_or_uri])
        except Exception as e:
            logging.error(f"Error setting XFCE background: {e}")

    @staticmethod
    def set_kde_background(path_or_uri):
        """
        Sets the background for KDE Plasma using the specialized plugin.
        Note: We don't use blurred static images here as they might interfere with the plugin.
        """
        prefix = DesktopHelper._get_host_cmd_prefix()
        try:
            DesktopHelper._ensure_kde_plugin_installed()
            qdbus_bin = next((b for b in ["qdbus-qt5", "qdbus6", "qdbus"] if shutil.which(b)), None)
            if not qdbus_bin: return
            
            plugin_id = "org.wengine.pro.wallpaper"
            video_url = f"file://{os.path.abspath(path_or_uri)}"
            script = f'var allDesktops = desktops(); for (var i = 0; i < allDesktops.length; i++) {{ var d = allDesktops[i]; d.wallpaperPlugin = "{plugin_id}"; d.currentConfigGroup = Array("Wallpaper", "{plugin_id}", "General"); d.writeConfig("VideoUrls", "{video_url}"); d.writeConfig("FillMode", "1"); }}'
            subprocess.run(prefix + [qdbus_bin, "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", script])
        except Exception as e:
            logging.error(f"Error setting KDE background: {e}")

    @staticmethod
    def set_static_blur_background(video_path):
        """
        Creates a blurred frame from the video and sets it as the background.
        Optimized to SKIP for KDE to avoid interference with the native plugin.
        """
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "kde" in desktop or "plasma" in desktop:
            logging.debug("Skipping static blur for KDE (handled by native plugin)")
            return

        import threading
        def _worker():
            try:
                from PIL import Image, ImageFilter
                ffmpeg_bin = "ffmpeg"
                appdir = os.environ.get("APPDIR")
                if appdir and os.path.exists(os.path.join(appdir, "usr/bin/ffmpeg")):
                    ffmpeg_bin = os.path.join(appdir, "usr/bin/ffmpeg")
                tmp_dir = QStandardPaths.writableLocation(QStandardPaths.TempLocation)
                file_hash = str(abs(hash(video_path)))
                bg_path = os.path.join(tmp_dir, f"w_bg_blur_{file_hash}.png")
                if not os.path.exists(bg_path):
                    subprocess.run([ffmpeg_bin, "-y", "-ss", "00:00:00.500", "-i", video_path, "-vframes", "1", "-f", "image2", "-loglevel", "quiet", bg_path], timeout=2)
                if os.path.exists(bg_path):
                    with Image.open(bg_path) as img:
                        blurred = img.filter(ImageFilter.GaussianBlur(radius=15))
                        blurred.save(bg_path)
                    DesktopHelper.set_background(bg_path)
            except: pass
        threading.Thread(target=_worker, daemon=True).start()

    @staticmethod
    def _get_protocol():
        # GNOME Xorg a veces deja variables de Wayland. Priorizamos X11 si DISPLAY está presente.
        if os.environ.get("DISPLAY"):
            return "x11"
        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"
        
        # Fallback a loginctl
        try:
            res = subprocess.check_output(["loginctl", "show-session", "self", "-p", "Type"], text=True)
            if "Type=x11" in res: return "x11"
            if "Type=wayland" in res: return "wayland"
        except: pass
        
        return "x11"

    @staticmethod
    def _get_compositor():
        xdg = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "hyprland" in xdg: return "Hyprland"
        if "sway" in xdg: return "Sway"
        if "gnome" in xdg: return "GNOME"
        if "kde" in xdg or "plasma" in xdg: return "KDE"
        if "xfce" in xdg: return "XFCE"
        try:
            pgrep = subprocess.check_output(["pgrep", "-l", "gnome-session|ksmserver|xfce4-session|hyprland|sway"], encoding="utf-8")
            if "gnome-session" in pgrep: return "GNOME"
            if "ksmserver" in pgrep: return "KDE"
            if "xfce4-session" in pgrep: return "XFCE"
            if "hyprland" in pgrep: return "Hyprland"
            if "sway" in pgrep: return "Sway"
        except: pass
        return xdg.capitalize() or "Unknown"

    @staticmethod
    def _get_gpu_vendor():
        try:
            if os.path.exists("/proc/driver/nvidia/version"): return "Nvidia"
            output = subprocess.check_output("glxinfo | grep -i renderer", shell=True, stderr=subprocess.DEVNULL).decode()
            for v in ["NVIDIA", "AMD", "Radeon", "Intel", "Mesa"]:
                if v.upper() in output.upper(): return v
        except: pass
        return "Unknown"

    @staticmethod
    def _is_flatpak():
        return os.path.exists("/.flatpak-info")

    @staticmethod
    def _get_host_cmd_prefix():
        return ["flatpak-spawn", "--host"] if DesktopHelper._is_flatpak() else []

    @staticmethod
    def _ensure_kde_plugin_installed():
        dest = os.path.expanduser("~/.local/share/plasma/wallpapers/org.wengine.pro.wallpaper")
        if os.path.exists(dest): return
        appdir = os.environ.get("APPDIR", os.path.dirname(os.path.dirname(__file__)))
        src = os.path.join(appdir, "usr/share/wengine/Clonar kde/plasma-smart-video-wallpaper-reborn-main/package")
        if not os.path.exists(src):
            src = os.path.join(os.path.dirname(os.path.dirname(__file__)), "Clonar kde/plasma-smart-video-wallpaper-reborn-main/package")
        if os.path.exists(src):
            try:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copytree(src, dest)
            except: pass
