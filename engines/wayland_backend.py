import os
import time
import socket
import json
import logging
import shutil
from engines.base_backend import BaseBackend
from core.process_manager import ProcessManager
from core.logger import log_event


class WaylandBackend(BaseBackend):
    def __init__(self):
        self.proc_manager = ProcessManager()
        self.base_socket_path = "/tmp/mpv-bg-socket-wayland"
        self.active_sockets = []
        self.mpvpaper_bin = shutil.which("mpvpaper")

    def start(self, config, video_path):
        self.stop()
        time.sleep(0.3)

        # Detectar compositor
        compositor = config.get_volatile("compositor", "").lower()
        is_kde = "kde" in compositor or "plasma" in compositor

        # 1. OPTIMIZACIÓN: Solo para Wayland genérico (Sway, Hyprland, etc.)
        # NO KDE por solicitud de usuario
        if not is_kde:
            from core.desktop_helper import DesktopHelper
            DesktopHelper.set_static_blur_background(video_path)

        # SI ES KDE: USAR MÉTODO NATIVO (PLUGIN)
        if is_kde:
            from core.desktop_helper import DesktopHelper
            logging.info("[WaylandBackend] Usando método nativo de KDE Plasma para el wallpaper.")
            # El método set_background ahora instala y configura el plugin nativo
            DesktopHelper.set_background(video_path)
            # Retornar True ya que Plasma se encarga de la reproducción
            return True

        # Preparar entornos para otros compositores (Sway, Hyprland, etc.)
        app_env = os.environ.copy()
        clean_env = app_env.copy()
        for var in [
            "LD_LIBRARY_PATH",
            "PYTHONPATH",
            "PYTHONHOME",
            "QT_PLUGIN_PATH",
            "LD_PRELOAD",
        ]:
            if var in clean_env:
                del clean_env[var]

        if not self.mpvpaper_bin:
            logging.warning(
                "[WaylandBackend] mpvpaper not found. Falling back to floating mpv."
            )
            socket_path = f"{self.base_socket_path}-0"
            if os.path.exists(socket_path):
                try:
                    os.remove(socket_path)
                except OSError:
                    pass

            # Intentar usar el mpv del bundle si estamos en un AppImage
            appdir = os.environ.get("APPDIR")
            mpv_bin = None
            use_env = clean_env

            if appdir and os.path.exists(os.path.join(appdir, "usr/bin/mpv")):
                mpv_bin = os.path.join(appdir, "usr/bin/mpv")
                use_env = app_env  # Usar entorno del app para mpv del bundle
            
            if not mpv_bin:
                mpv_bin = shutil.which("mpv")
                use_env = clean_env # Usar entorno limpio para mpv del sistema
            
            if not mpv_bin:
                logging.error("[WaylandBackend] mpv not found on system. Cannot fallback.")
                return False

            cmd = [mpv_bin] + self._build_mpv_args(
                config, socket_path, wid_needed=False
            )
            
            app_id = "W-Engine-Wallpaper"
            
            cmd += [
                "--gpu-context=wayland",
                "--force-window=yes",
                "--no-border",
                f"--wayland-app-id={app_id}",
                f"--title={app_id}",
                video_path,
            ]
            
            self.proc_manager.start("wayland-fallback", cmd, env=use_env)
            self.active_sockets = [socket_path]
            
            if is_kde:
                self._apply_kde_window_rules(app_id)
            else:
                self._apply_wayland_window_rules(app_id)
            
            return self._wait_for_ipc()

        # Camino normal con mpvpaper (usa clean_env por ser binario externo)
        target_monitor = config.get_setting("target_monitor", "Auto")
        outputs = ["*"] if target_monitor == "Auto" else [target_monitor]

        self.active_sockets = []
        for i, out in enumerate(outputs):
            socket_path = f"{self.base_socket_path}-{i}"
            if os.path.exists(socket_path):
                try:
                    os.remove(socket_path)
                except OSError:
                    pass

            mpv_opts = self._build_mpv_args(config, socket_path, wid_needed=False)
            base_cmd = [self.mpvpaper_bin]
            for opt in mpv_opts:
                if opt:
                    base_cmd.extend(["-o", opt])

            cmd = base_cmd + [out, video_path]
            self.proc_manager.start(f"wayland-wallpaper-{i}", cmd, env=clean_env)
            self.active_sockets.append(socket_path)

        return self._wait_for_ipc()

    def _apply_kde_window_rules(self, app_id):
        """Usa scripts de KWin para forzar la ventana al fondo, sin bordes y omitir taskbar."""
        import subprocess
        import threading

        def _worker():
            # Esperar un poco a que la ventana se cree
            time.sleep(1.0)
            
            # Script de KWin que busca la ventana por app-id y aplica propiedades de wallpaper
            # En Wayland, 'resourceName' suele ser el app-id
            script = f"""
                var clients = workspace.clientList();
                for (var i = 0; i < clients.length; i++) {{
                    var c = clients[i];
                    if (c.resourceClass.toString().indexOf("{app_id}") !== -1 || 
                        c.resourceName.toString().indexOf("{app_id}") !== -1 ||
                        c.caption.indexOf("{app_id}") !== -1) {{
                        
                        c.keepBelow = true;
                        c.noBorder = true;
                        c.skipTaskbar = true;
                        c.skipPager = true;
                        c.skipSwitcher = true;
                        c.fullScreen = true; // Opcional, forzar a pantalla completa
                        
                        // Enviar al fondo de nuevo por si acaso
                        workspace.activeClient = null;
                    }}
                }}
            """
            
            try:
                # 1. Cargar script
                res = subprocess.run([
                    "qdbus", "org.kde.KWin", "/Scripting", 
                    "org.kde.KWin.Scripting.loadScript", 
                    "dummy", "wengine-pin"
                ], capture_output=True, text=True)
                
                # Si qdbus no funciona, probar qdbus-qt5 o qdbus6
                if res.returncode != 0:
                    for b in ["qdbus-qt5", "qdbus6"]:
                        if shutil.which(b):
                            subprocess.run([
                                b, "org.kde.KWin", "/Scripting", 
                                "org.kde.KWin.Scripting.loadScript", 
                                "dummy", "wengine-pin"
                            ])
                            break
                
                # 2. El script de arriba es un placeholder, lo sobreescribimos con el real
                # (KWin no permite pasar el contenido del script por dbus fácilmente, 
                # así que usamos este truco o un archivo temporal)
                # En este caso, usaremos qdbus para ejecutarlo si ya está cargado o usar un archivo
                import tempfile
                with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as f:
                    f.write(script)
                    temp_script = f.name
                
                # Ejecutar via qdbus (método alternativo de carga directa de archivo si disponible)
                # Pero lo más seguro es usar Window Rules persistentes si esto falla.
                logging.info(f"[KDE_FIX] Aplicando reglas de ventana para {app_id}...")
                
            except Exception as e:
                logging.error(f"Error aplicando reglas de ventana KDE: {e}")

        threading.Thread(target=_worker, daemon=True).start()

    def _apply_wayland_window_rules(self, app_id):
        """Usa swaymsg (u otros comandos de compositor) para configurar la ventana como wallpaper."""
        import subprocess
        import threading

        def _worker():
            time.sleep(1.5)
            
            compositor = self._detect_compositor()
            
            if compositor == "sway":
                self._apply_sway_rules(app_id)
            elif compositor == "hyprland":
                self._apply_hyprland_rules(app_id)
            else:
                logging.warning(f"[WaylandBackend] Compositor {compositor} no soportado para reglas de ventana")

        threading.Thread(target=_worker, daemon=True).start()

    def _detect_compositor(self):
        """Detecta qué compositor Wayland está en uso."""
        compositor = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        if "sway" in compositor:
            return "sway"
        if "hyprland" in compositor:
            return "hyprland"
        if "gnome" in compositor:
            return "gnome"
        if "kde" in compositor or "plasma" in compositor:
            return "kde"
        # También verificar SWAYSOCK
        if os.path.exists(os.environ.get("SWAYSOCK", "/run/user/1000/sway.sock")):
            return "sway"
        if os.path.exists(os.environ.get("HYPRLAND_INSTANCE_SIGNATURE", "")):
            return "hyprland"
        return "unknown"

    def _apply_sway_rules(self, app_id):
        """Aplica reglas de ventana específicas para Sway."""
        import subprocess
        
        try:
            time.sleep(2.0)
            
            result = subprocess.run(
                ["swaymsg", "-t", "get_tree"],
                capture_output=True, text=True, timeout=3
            )
            
            if result.returncode != 0:
                logging.warning("[WaylandBackend] swaymsg get_tree failed")
                return
            
            import json
            tree = json.loads(result.stdout)
            
            window_id = None
            outputs = tree.get("nodes", [])
            for output in outputs:
                for node_type in ["nodes", "floating_nodes"]:
                    for node in output.get(node_type, []):
                        if self._find_window_by_app_id(node, app_id):
                            window_id = self._find_window_by_app_id(node, app_id)
                            break
                    if window_id:
                        break
                if window_id:
                    break
            
            if not window_id:
                logging.warning(f"[WaylandBackend] No se encontró ventana con app_id={app_id}")
                return
            
            logging.info(f"[WaylandBackend] Encontrada ventana {window_id} para {app_id}")
            
            commands = [
                f"[con_id={window_id}] floating enable",
                f"[con_id={window_id}] border none",
                f"[con_id={window_id}] fullscreen enable",
            ]
            
            for cmd in commands:
                res = subprocess.run(
                    ["swaymsg", cmd],
                    capture_output=True, text=True, timeout=2
                )
                if res.returncode != 0:
                    logging.warning(f"[WaylandBackend] swaymsg failed: {cmd} - {res.stderr}")
            
            logging.info(f"[WaylandBackend] Aplicadas reglas de Sway para {app_id}")
            
        except subprocess.TimeoutExpired:
            logging.warning("[WaylandBackend] Timeout aplicando reglas Sway")
        except FileNotFoundError:
            logging.warning("[WaylandBackend] swaymsg no encontrado")
        except Exception as e:
            logging.error(f"[WaylandBackend] Error aplicando reglas Sway: {e}")
    
    def _find_window_by_app_id(self, node, app_id):
        """Busca recursivamente una ventana por app_id en el árbol de Sway."""
        if isinstance(node, dict):
            if node.get("app_id") == app_id or node.get("window_properties", {}).get("class") == app_id:
                return node.get("id")
            for key in ["nodes", "floating_nodes", "focus"]:
                if key in node:
                    for child in node[key]:
                        result = self._find_window_by_app_id(child, app_id)
                        if result:
                            return result
        return None

    def _apply_hyprland_rules(self, app_id):
        """Aplica reglas de ventana específicas para Hyprland."""
        import subprocess
        
        try:
            # Hyprctl para buscar y configurar ventanas
            result = subprocess.run(
                ["hyprctl", "clients", "-j"],
                capture_output=True, text=True, timeout=2
            )
            
            if result.returncode == 0:
                import json
                try:
                    clients = json.loads(result.stdout)
                    for client in clients:
                        if app_id in (client.get("class", "") + client.get("title", "")):
                            addr = client.get("address", "")
                            # Aplicar reglas
                            subprocess.run(
                                ["hyprctl", "dispatcher", "setprop", addr, "watermark", "true"],
                                capture_output=True
                            )
                            subprocess.run(
                                ["hyprctl", "dispatcher", "setprop", addr, "noBorder", "true"],
                                capture_output=True
                            )
                            subprocess.run(
                                ["hyprctl", "dispatcher", "setprop", addr, "fullscreen", "true"],
                                capture_output=True
                            )
                            logging.info(f"[WaylandBackend] Aplicadas reglas de Hyprland para {app_id}")
                            break
                except json.JSONDecodeError:
                    pass
                    
        except subprocess.TimeoutExpired:
            logging.warning("[WaylandBackend] Timeout aplicando reglas Hyprland")
        except FileNotFoundError:
            logging.warning("[WaylandBackend] hyprctl no encontrado")
        except Exception as e:
            logging.error(f"[WaylandBackend] Error aplicando reglas Hyprland: {e}")

    def _wait_for_ipc(self):
        for _ in range(10):
            if self.active_sockets and all(
                os.path.exists(s) for s in self.active_sockets
            ):
                return True
            time.sleep(0.1)
        return False

    def stop(self):
        for name in list(self.proc_manager.processes.keys()):
            if name.startswith("wayland-wallpaper") or name == "wayland-fallback":
                self.proc_manager.stop(name)

        import subprocess

        subprocess.run(["pkill", "-f", "mpvpaper"], stderr=subprocess.DEVNULL)
        subprocess.run(
            ["pkill", "-f", "mpv.*mpv-bg-socket-wayland"], stderr=subprocess.DEVNULL
        )

        for s in self.active_sockets:
            if os.path.exists(s):
                try:
                    os.remove(s)
                except OSError:
                    pass
        self.active_sockets = []

    def update_setting(self, key, value):
        logging.info(
            f"[WAYLAND_BACKEND_DEBUG] update_setting received: key={key}, value={value}"
        )
        property_map = {
            "volume": "volume",
            "mute": "mute",
            "brightness": "brightness",
            "contrast": "contrast",
            "saturation": "saturation",
            "gamma": "gamma",
        }

        if key in property_map:
            mpv_prop = property_map[key]
            if key == "mute":
                value = "yes" if value else "no"
            elif key == "gamma":
                # Gamma mapping
                try:
                    gamma_ui = float(value)
                    if gamma_ui > 1.0:
                        value = int((gamma_ui - 1.0) / 4.0 * 100)
                    else:
                        value = int((gamma_ui - 1.0) / 0.9 * 100)
                except:
                    value = 0
            logging.info(
                f"[WAYLAND_BACKEND_DEBUG] sending command: set_property, {mpv_prop}, {value}"
            )
            return self.send_command("set_property", mpv_prop, value)

        elif key == "loop":
            if value == "Loop":
                self.send_command("set_property", "loop-file", "inf")
                self.send_command("set_property", "pause", False)
            else:
                self.send_command("set_property", "loop-file", "no")
                self.send_command("set_property", "pause", True)
            return True

        return False

    def send_command(self, command, *args):
        if not self.active_sockets:
            return False

        success = True
        for socket_path in self.active_sockets:
            if not os.path.exists(socket_path):
                success = False
                continue

            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(0.05)
                    client.connect(socket_path)
                    msg = {"command": [command] + list(args)}
                    client.sendall((json.dumps(msg) + "\n").encode())
            except (socket.error, socket.timeout):
                success = False
        return success

    def _build_mpv_args(self, config, socket_path, wid_needed=False):
        args = []
        if wid_needed:
            args.append("--wid=%WID")

        args.extend(
            [
                f"--loop-file={'inf' if config.get_setting('loop', 'Loop') == 'Loop' else 'no'}",
                f"--volume={config.get_setting('volume', 50)}",
                f"--mute={'yes' if config.get_setting('mute', False) else 'no'}",
                f"--hwdec={config.get_setting('hwdec', 'auto-safe')}",
                "--vo=gpu",
                "--gpu-context=auto",
                "--profile=low-latency",
                "--untimed",
                "--no-audio" if config.get_setting("no_audio", True) else "",
                "--panscan=1.0",
                "--keep-open=yes",
                f"--input-ipc-server={socket_path}",
                "--no-osc",
                "--no-osd-bar",
                "--no-input-default-bindings",
                "--idle",
            ]
        )

        # 1. Video Quality / Resolution (Video Filter)
        resolution_map = {
            "1080p (Full HD)": "scale=-1:1080",
            "720p (HD)": "scale=-1:720",
            "480p (SD)": "scale=-1:480",
        }
        res_setting = config.get_setting("video_resolution", "Nativa")
        if res_setting in resolution_map:
            args.append(f"--vf={resolution_map[res_setting]}")

        # 2. FPS Limit
        fps_limit = config.get_setting("fps_limit", 60)
        args.append(f"--override-display-fps={fps_limit}")

        # 3. GPU API
        gpu_api = config.get_setting("gpu_api", "auto")
        if gpu_api != "auto":
            args.append(f"--gpu-api={gpu_api}")

        # Playback cache flags
        cache_flags = config.get_setting("_mpv_cache_flags", [])
        args.extend(cache_flags)

        # Add live properties from config
        for prop in ["brightness", "contrast", "saturation"]:
            val = config.get_setting(prop, 0)
            args.append(f"--{prop}={val}")

        # Gamma mapping: UI (0.1 to 5.0, neutral 1.0) -> MPV (-100 to 100, neutral 0)
        gamma_ui = config.get_setting("gamma", 1.0)
        if gamma_ui > 1.0:
            gamma_mpv = int((gamma_ui - 1.0) / 4.0 * 100)
        else:
            gamma_mpv = int((gamma_ui - 1.0) / 0.9 * 100)
        args.append(f"--gamma={gamma_mpv}")

        return [a for a in args if a]
